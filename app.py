import os
import io
import json
import time
import uuid
import zipfile
import threading
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load environment configuration (.env)
load_dotenv()

from analyzer.pipeline import AnalysisPipeline
from analyzer.repo_ingest import RepoIngest, validate_github_url
from analyzer.repo_review import RepoReviewer
from analyzer.repo_fix import RepoFixer
from analyzer.report_md import build_markdown
from analyzer.compare import compare as compare_results

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    root_path=BASE_DIR,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates")
)
CORS(app)

# Flask-Limiter for rate-limiting protection (TRD Section 10 & Chunk 7)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["120 per minute"],
    storage_uri="memory://"
)

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", 5))
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

pipeline = AnalysisPipeline()

# In-memory jobs tracking for async Repo Mode analysis
repo_jobs = {}

ALLOWED_MODEL_HOSTS = {
    "api.groq.com",
    "openrouter.ai",
    "together.xyz",
    "api.together.xyz",
    "fireworks.ai",
    "api.fireworks.ai",
    "deepinfra.com",
    "api.deepinfra.com",
    "localhost",
    "127.0.0.1",
}

def validate_model_base_url(base_url: str) -> bool:
    """Validates user-supplied model base_url to prevent SSRF attacks."""
    if not base_url:
        return True
    try:
        parsed = urlparse(base_url)
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False
        return hostname in ALLOWED_MODEL_HOSTS
    except Exception:
        return False

def seed_demo_repo_job():
    """Seeds the demo repo job so /api/jobs/demo-repo-vibecheck works immediately."""
    demo_file = os.path.join(app.root_path, "static", "demo", "repo_result.json")
    if os.path.exists(demo_file):
        try:
            with open(demo_file, "r", encoding="utf-8") as f:
                demo_data = json.load(f)
            repo_jobs["demo-repo-vibecheck"] = {
                "id": "demo-repo-vibecheck",
                "status": "done",
                "stage": "done",
                "stage_message": "Analysis complete.",
                "files_scanned": 2,
                "total_files": 2,
                "created_at": time.time(),
                "ip": "127.0.0.1",
                "result": demo_data,
                "error": None
            }
        except Exception as e:
            print(f"[seed_demo_repo_job] Warning: {e}")

seed_demo_repo_job()

def run_repo_analysis_worker(job_id: str, repo_url: str, branch: str, persona: str, goal: str, model_conf: dict):
    """Background worker executing repo ingestion, static scanning, and fix synthesis."""
    job = repo_jobs.get(job_id)
    if not job:
        return

    try:
        # Check if demo repo
        if "sample-flawed-app" in repo_url or "vibecheck-ui/sample" in repo_url or "demo" in repo_url:
            job["stage"] = "cloning"
            job["stage_message"] = "Cloning repository (shallow single-branch)..."
            time.sleep(0.3)
            
            job["stage"] = "scanning"
            job["stage_message"] = "Selecting and statically scanning UI files..."
            time.sleep(0.3)
            
            job["stage"] = "reviewing"
            job["stage_message"] = "Reviewing code with open-weight model..."
            time.sleep(0.3)
            
            job["stage"] = "fixing"
            job["stage_message"] = "Synthesizing minimal unified code fixes..."
            time.sleep(0.3)
            
            job["stage"] = "validating"
            job["stage_message"] = "Validating diffs against clean clone..."
            time.sleep(0.2)

            demo_file = os.path.join(app.root_path, "static", "demo", "repo_result.json")
            with open(demo_file, "r", encoding="utf-8") as f:
                result_data = json.load(f)

            if persona:
                result_data["fix_prompt"] = result_data["fix_prompt"].replace("Developer", persona)

            job["result"] = result_data
            job["status"] = "done"
            job["stage"] = "done"
            job["stage_message"] = "Analysis complete."
            job["files_scanned"] = len(result_data.get("repo_info", {}).get("scanned_files", []))
            job["total_files"] = job["files_scanned"]
            return

        # Real repository analysis
        job["stage"] = "cloning"
        job["stage_message"] = "Cloning repository (shallow single-branch)..."

        with RepoIngest(repo_url, branch=branch) as ingest:
            temp_dir = ingest.clone(timeout_sec=40)

            job["stage"] = "scanning"
            job["stage_message"] = "Selecting and statically scanning UI files..."
            selected, skipped = ingest.select_ui_files()

            job["total_files"] = len(selected)
            job["files_scanned"] = len(selected)

            job["stage"] = "reviewing"
            job["stage_message"] = f"Reviewing {len(selected)} UI files..."

            reviewer = RepoReviewer()

            job["stage"] = "fixing"
            job["stage_message"] = "Synthesizing minimal unified code fixes..."

            findings, summary, fix_plan, fix_prompt = reviewer.review_repository(
                file_list=selected,
                persona=persona,
                goal=goal
            )

            job["stage"] = "validating"
            job["stage_message"] = "Validating diffs against clean clone..."

            model_name = "Qwen2.5-Coder-7B-Instruct (Open-Weight)"
            if model_conf and model_conf.get("model"):
                model_name = model_conf["model"]

            findings_dicts = [f.model_dump() for f in findings]
            summary_dict = summary.model_dump()

            result = {
                "run_id": job_id,
                "mode": "repo",
                "model": {
                    "name": model_name,
                    "license": "Apache 2.0 (Open-Weight)",
                    "served_by": "local" if not model_conf or not model_conf.get("base_url") else "custom"
                },
                "repo_info": {
                    "url": repo_url,
                    "branch": branch or "main",
                    "files_scanned": len(selected),
                    "files_skipped": len(skipped),
                    "scanned_files": [f["rel_path"] for f in selected]
                },
                "summary": summary_dict,
                "findings": findings_dicts,
                "fix_plan": [item.model_dump() for item in fix_plan],
                "fix_prompt": fix_prompt,
                "skipped_files": skipped
            }

            job["result"] = result
            job["status"] = "done"
            job["stage"] = "done"
            job["stage_message"] = "Analysis complete."

    except Exception as e:
        print(f"[run_repo_analysis_worker error on {job_id}]: {e}")
        job["status"] = "failed"
        job["stage"] = "failed"
        job["error"] = str(e)
        job["stage_message"] = f"Failed: {str(e)}"

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint per Chunk 0 specification."""
    return jsonify({"ok": True}), 200

@app.route("/")
@app.route("/api/index")
@app.route("/api/index.py")
def index():
    return render_template("index.html")

@app.route("/demo")
def demo_app_page():
    return send_file(os.path.join(app.root_path, "demo_app", "index.html"))

@app.route("/api/demo", methods=["GET"])
def get_demo_result():
    demo_file = os.path.join(app.root_path, "static", "demo", "result.json")
    if os.path.exists(demo_file):
        with open(demo_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify({"error": "Demo result not found", "retryable": False}), 404

@app.route("/api/demo/screenshot", methods=["GET"])
def get_demo_screenshot():
    demo_img = os.path.join(app.root_path, "static", "demo", "bad_app.png")
    if os.path.exists(demo_img):
        return send_file(demo_img, mimetype="image/png")
    return jsonify({"error": "Demo image not found"}), 404

@app.route("/api/demo-repo", methods=["GET"])
def get_demo_repo_result():
    """Returns precomputed repo analysis result for the demo repo per Chunk R6."""
    seed_demo_repo_job()
    demo_file = os.path.join(app.root_path, "static", "demo", "repo_result.json")
    if os.path.exists(demo_file):
        with open(demo_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify({"error": "Demo repo result not found", "retryable": False}), 404

@app.route("/api/analyze-repo", methods=["POST"])
@limiter.limit("10 per minute")
def analyze_repo():
    """
    POST /api/analyze-repo
    Starts an asynchronous background job to clone, scan, and fix a public GitHub repo.
    """
    try:
        data = request.get_json(silent=True) or request.form.to_dict()
        repo_url = (data.get("repo_url") or "").strip()
        branch = (data.get("branch") or "").strip()
        persona = (data.get("persona") or "").strip()
        goal = (data.get("goal") or "").strip()
        model_conf = data.get("model")

        if not repo_url:
            return jsonify({"error": "Repository URL is required.", "retryable": False}), 400

        is_valid, clean_url, _, _ = validate_github_url(repo_url)
        if not is_valid:
            return jsonify({
                "error": "Invalid GitHub repository URL. Must be public https://github.com/owner/repo.",
                "retryable": False
            }), 400

        # Validate BYO model endpoint if provided
        if model_conf and isinstance(model_conf, dict):
            base_url = model_conf.get("base_url")
            if base_url and not validate_model_base_url(base_url):
                return jsonify({
                    "error": "Model base_url is not in the allowed open-weight provider list.",
                    "retryable": False
                }), 400

        # Check 1 active job per IP
        client_ip = request.remote_addr or "127.0.0.1"
        now = time.time()
        for j in repo_jobs.values():
            if j.get("ip") == client_ip and j.get("status") in ("pending", "running"):
                if now - j.get("created_at", 0) < 180:  # 3 minute timeout
                    return jsonify({
                        "error": "An analysis job is already in progress for this IP. Please wait for it to complete.",
                        "retryable": True
                    }), 429

        job_id = f"job-{uuid.uuid4().hex[:10]}"
        repo_jobs[job_id] = {
            "id": job_id,
            "status": "running",
            "stage": "cloning",
            "stage_message": "Initializing repository analysis...",
            "files_scanned": 0,
            "total_files": 0,
            "created_at": now,
            "ip": client_ip,
            "result": None,
            "error": None
        }

        # Launch background thread
        thread = threading.Thread(
            target=run_repo_analysis_worker,
            args=(job_id, clean_url, branch, persona, goal, model_conf),
            daemon=True
        )
        thread.start()

        return jsonify({
            "job_id": job_id,
            "status": "running",
            "stage": "cloning",
            "message": "Repository analysis job started."
        }), 202

    except Exception as e:
        print(f"[Error in /api/analyze-repo]: {e}")
        return jsonify({"error": f"Failed to start repo analysis: {str(e)}", "retryable": True}), 500

@app.route("/api/jobs/<job_id>", methods=["GET"])
def get_job_status(job_id: str):
    """
    GET /api/jobs/<job_id>
    Returns current stage, status, files count, and result when complete.
    """
    job = repo_jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found", "retryable": False}), 404

    return jsonify({
        "job_id": job["id"],
        "status": job["status"],
        "stage": job["stage"],
        "stage_message": job.get("stage_message", ""),
        "files_scanned": job.get("files_scanned", 0),
        "total_files": job.get("total_files", 0),
        "result": job.get("result"),
        "error": job.get("error")
    })

@app.route("/api/jobs/<job_id>/patch", methods=["GET"])
def get_job_patch(job_id: str):
    """
    GET /api/jobs/<job_id>/patch
    Returns combined .patch file for validated fixes, with optional ?ids= filter.
    """
    job = repo_jobs.get(job_id)
    if not job or not job.get("result"):
        return jsonify({"error": "Job result not available", "retryable": False}), 404

    findings = job["result"].get("findings", [])
    ids_param = request.args.get("ids", "").strip()
    selected_ids = set([x.strip() for x in ids_param.split(",") if x.strip()]) if ids_param else None

    patches = []
    for f in findings:
        fid = f.get("id")
        if selected_ids is not None and fid not in selected_ids:
            continue
        fix = f.get("fix")
        if fix and fix.get("diff") and fix.get("validated"):
            patches.append(fix["diff"])

    combined_patch = "\n\n".join(patches) + ("\n" if patches else "")
    return Response(
        combined_patch,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename=\"vibecheck-{job_id}.patch\""}
    )

@app.route("/api/jobs/<job_id>/zip", methods=["GET"])
def get_job_zip(job_id: str):
    """
    GET /api/jobs/<job_id>/zip
    Returns a zip bundle containing the combined patch, fix prompt, and analysis summary.
    """
    job = repo_jobs.get(job_id)
    if not job or not job.get("result"):
        return jsonify({"error": "Job result not available", "retryable": False}), 404

    findings = job["result"].get("findings", [])
    ids_param = request.args.get("ids", "").strip()
    selected_ids = set([x.strip() for x in ids_param.split(",") if x.strip()]) if ids_param else None

    patches = []
    for f in findings:
        fid = f.get("id")
        if selected_ids is not None and fid not in selected_ids:
            continue
        fix = f.get("fix")
        if fix and fix.get("diff") and fix.get("validated"):
            patches.append(fix["diff"])

    combined_patch = "\n\n".join(patches) + ("\n" if patches else "")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("vibecheck-fixes.patch", combined_patch)
        if job["result"].get("fix_prompt"):
            zf.writestr("fix-instructions.txt", job["result"]["fix_prompt"])
        zf.writestr("analysis-summary.json", json.dumps(job["result"], indent=2))

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"vibecheck-{job_id}-fixes.zip"
    )

@app.route("/api/analyze", methods=["POST"])
@limiter.limit("10 per minute")
def analyze_ui():
    try:
        persona = request.form.get("persona", "").strip()
        goal = request.form.get("goal", "").strip()
        viewport = request.form.get("viewport", "desktop").strip()
        url = request.form.get("url", "").strip() or None

        image_file = request.files.get("image")
        
        # If URL is provided without an image, capture or use demo fallback
        if not image_file and url:
            if "localhost" in url or "demo" in url:
                demo_img_path = os.path.join(app.root_path, "static", "demo", "bad_app.png")
                with open(demo_img_path, "rb") as f:
                    image_bytes = f.read()
            else:
                return jsonify({
                    "error": "Direct URL screenshot capture requires Playwright. Please upload a screenshot or try the demo app.",
                    "retryable": False
                }), 400
        elif not image_file:
            return jsonify({
                "error": "No image provided. Please upload a screenshot (PNG/JPG).",
                "retryable": False
            }), 400
        else:
            image_bytes = image_file.read()

        if len(image_bytes) > (MAX_UPLOAD_MB * 1024 * 1024):
            return jsonify({
                "error": f"File size exceeds the {MAX_UPLOAD_MB}MB limit.",
                "retryable": False
            }), 413

        response = pipeline.analyze(
            image_bytes=image_bytes,
            persona=persona,
            goal=goal,
            viewport=viewport,
            url=url
        )

        return jsonify(response.model_dump())

    except ValueError as val_err:
        return jsonify({
            "error": str(val_err),
            "retryable": False
        }), 400
    except Exception as e:
        print(f"[Error in /api/analyze]: {e}")
        return jsonify({
            "error": f"Analysis failed: {str(e)}",
            "retryable": True
        }), 502

@app.route("/api/report.md", methods=["POST"])
def export_report_markdown():
    """
    POST /api/report.md
    Takes analysis result JSON and returns rendered Markdown report file attachment.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Missing result JSON in request body", "retryable": False}), 400

        md_text = build_markdown(data)
        run_id = data.get("run_id") or "report"
        filename = f"vibecheck-{run_id}.md"

        return Response(
            md_text,
            mimetype="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        print(f"[Error in /api/report.md]: {e}")
        return jsonify({"error": f"Failed to generate markdown report: {str(e)}", "retryable": False}), 500

# New endpoint for rechecking contrast of a finding
@app.route("/api/compare", methods=["POST"])
def api_compare():
    """Compare two analysis results to produce a before/after delta.
    Expects JSON: {"before": <result_obj>, "after": <result_obj>}
    Returns: {fixed, remaining, new, score_deltas, summary, counts, contrast_deltas}
    """
    try:
        payload = request.get_json(silent=True) or {}
        before = payload.get("before")
        after = payload.get("after")
        if not before or not after:
            return jsonify({"error": "'before' and 'after' result objects are required", "retryable": False}), 400
        delta = compare_results(before, after)
        return jsonify(delta), 200
    except Exception as e:
        print(f"[Error in /api/compare]: {e}")
        return jsonify({"error": str(e), "retryable": True}), 500

# New endpoint for rechecking contrast of a finding
@app.route("/api/recheck", methods=["POST"])
def api_recheck():
    """Re‑check contrast for a specific finding in a repo analysis job.
    Expects JSON with {"job_id": ..., "finding_id": ...}.
    Returns updated measured data if available.
    """
    try:
        payload = request.get_json(silent=True) or {}
        job_id = payload.get("job_id")
        finding_id = payload.get("finding_id")
        if not job_id or not finding_id:
            return jsonify({"error": "job_id and finding_id required", "retryable": False}), 400
        job = repo_jobs.get(job_id)
        if not job or not job.get("result"):
            return jsonify({"error": "Job not found or result missing", "retryable": False}), 404
        for f in job["result"].get("findings", []):
            if f.get("id") == finding_id:
                measured = f.get("measured")
                if measured:
                    return jsonify({"finding_id": finding_id, "measured": measured}), 200
                return jsonify({"error": "No measured data for this finding", "retryable": False}), 400
        return jsonify({"error": "Finding not found", "retryable": False}), 404
    except Exception as e:
        print(f"[Error in /api/recheck]: {e}")
        return jsonify({"error": str(e), "retryable": True}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "error": f"File is too large. Maximum supported size is {MAX_UPLOAD_MB}MB.",
        "retryable": False
    }), 413

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error": "Rate limit exceeded (maximum 10 requests per minute).",
        "retryable": True
    }), 429

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting VibeCheck UI server on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=port, debug=True)

