import os
import re
import shutil
import tempfile
import subprocess
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse

GITHUB_URL_PATTERN = re.compile(
    r"^https://github\.com/(?P<owner>[\w\.\-]+)/(?P<repo>[\w\.\-]+)(?:/tree/(?P<branch>[\w\.\-]+))?/?$"
)

ALLOWED_EXTENSIONS = {
    ".html", ".css", ".scss", ".sass", ".js", ".jsx",
    ".ts", ".tsx", ".vue", ".svelte"
}

EXCLUDE_DIRS = {
    "node_modules", "dist", "build", ".git", ".github",
    ".vscode", "coverage", ".next", ".nuxt", "out", "target", "vendor"
}

MAX_FILE_BYTES = 60 * 1024  # 60 KB
MAX_SELECTED_FILES = 25
MAX_REPO_BYTES = 50 * 1024 * 1024  # 50 MB

def validate_github_url(url: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    Validates that a URL is a legitimate public GitHub repository URL.
    Returns (is_valid, normalized_url, owner, repo).
    """
    url = url.strip()
    if not url.startswith("https://github.com/"):
        return False, "", None, None

    match = GITHUB_URL_PATTERN.match(url)
    if not match:
        return False, "", None, None

    owner = match.group("owner")
    repo = match.group("repo")
    if repo.endswith(".git"):
        repo = repo[:-4]

    clean_url = f"https://github.com/{owner}/{repo}"
    return True, clean_url, owner, repo

def score_file_relevance(rel_path: str) -> int:
    """Ranks files by UI relevance (entry HTML, components, styles first)."""
    p = rel_path.lower()
    score = 0
    if "index.html" in p or "app.jsx" in p or "app.tsx" in p or "main.jsx" in p:
        score += 100
    elif "components/" in p or "views/" in p or "pages/" in p:
        score += 80
    elif p.endswith(".css") or p.endswith(".scss") or "tailwind" in p:
        score += 70
    elif p.endswith(".jsx") or p.endswith(".tsx") or p.endswith(".vue") or p.endswith(".svelte"):
        score += 60
    elif p.endswith(".html"):
        score += 50
    elif p.endswith(".js") or p.endswith(".ts"):
        score += 40
    return score

class RepoIngest:
    def __init__(self, repo_url: str, branch: Optional[str] = None):
        is_valid, clean_url, owner, repo = validate_github_url(repo_url)
        if not is_valid:
            raise ValueError(
                "Invalid repository URL. Only public 'https://github.com/owner/repo' links are supported."
            )
        self.repo_url = clean_url
        self.branch = branch.strip() if branch else None
        self.owner = owner
        self.repo = repo
        self.temp_dir: Optional[str] = None

    def clone(self, timeout_sec: int = 40) -> str:
        """
        Shallow clones the repository with safety restrictions:
        - depth 1
        - no submodules
        - hooks disabled
        - size and time capped
        """
        self.temp_dir = tempfile.mkdtemp(prefix="vibecheck_repo_")
        
        cmd = [
            "git", "clone",
            "--depth", "1",
            "--single-branch",
            "--no-recurse-submodules",
            "-c", "core.hooksPath=/dev/null",
        ]
        if self.branch:
            cmd.extend(["-b", self.branch])
        cmd.extend([self.repo_url, self.temp_dir])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=True
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            # Fallback to downloading archive directly from GitHub
            self._download_archive_fallback(timeout_sec=timeout_sec)
        except subprocess.TimeoutExpired:
            self.cleanup()
            raise TimeoutError("Repository clone timed out (limit: 40 seconds).")

        # Enforce repo size cap
        total_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(self.temp_dir)
            for filename in filenames
        )
        if total_size > MAX_REPO_BYTES:
            self.cleanup()
            raise ValueError(f"Repository exceeds the {MAX_REPO_BYTES // (1024*1024)}MB size limit.")

        return self.temp_dir

    def _download_archive_fallback(self, timeout_sec: int = 40):
        """Downloads public repository zipball directly from GitHub if git command is unavailable."""
        import urllib.request
        import zipfile
        import io

        branch_candidates = [self.branch] if self.branch else ["main", "master"]
        downloaded = False

        for b in branch_candidates:
            archive_url = f"https://github.com/{self.owner}/{self.repo}/archive/refs/heads/{b}.zip"
            try:
                req = urllib.request.Request(archive_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                    zip_bytes = resp.read()
                    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                        names = zf.namelist()
                        if not names:
                            continue
                        top_dir = names[0].split("/")[0]
                        for member in zf.infolist():
                            rel = member.filename
                            if rel.startswith(top_dir + "/"):
                                sub_rel = rel[len(top_dir) + 1:]
                                if not sub_rel:
                                    continue
                                target = os.path.join(self.temp_dir, sub_rel.replace("/", os.sep))
                                if member.is_dir():
                                    os.makedirs(target, exist_ok=True)
                                else:
                                    os.makedirs(os.path.dirname(target), exist_ok=True)
                                    with open(target, "wb") as f:
                                        f.write(zf.read(member.filename))
                    downloaded = True
                    break
            except Exception:
                continue

        if not downloaded:
            self.cleanup()
            raise RuntimeError(f"Could not clone repository or download archive from GitHub ({self.repo_url}).")

    def select_ui_files(self) -> Tuple[List[Dict[str, any]], List[str]]:
        """
        Scans cloned repository, selecting up to 25 UI files ranked by relevance.
        Returns (selected_files_info, skipped_file_paths).
        """
        if not self.temp_dir or not os.path.exists(self.temp_dir):
            raise RuntimeError("Repository not cloned yet.")

        candidates = []
        skipped = []

        for root, dirs, files in os.walk(self.temp_dir):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            for filename in files:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, self.temp_dir).replace("\\", "/")
                _, ext = os.path.splitext(filename)
                ext = ext.lower()

                # Check lockfiles, minified files, map files
                if filename.endswith(".min.js") or filename.endswith(".min.css") or filename.endswith(".map"):
                    skipped.append(f"{rel_path} (minified/source map)")
                    continue
                if filename in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "cargo.lock"):
                    skipped.append(f"{rel_path} (package lockfile)")
                    continue

                if ext in ALLOWED_EXTENSIONS or filename in ("tailwind.config.js", "tailwind.config.ts"):
                    try:
                        size = os.path.getsize(full_path)
                    except OSError:
                        continue

                    if size > MAX_FILE_BYTES:
                        skipped.append(f"{rel_path} (exceeds 60KB cap)")
                        continue

                    score = score_file_relevance(rel_path)
                    candidates.append({
                        "rel_path": rel_path,
                        "abs_path": full_path,
                        "size": size,
                        "ext": ext,
                        "score": score
                    })
                else:
                    skipped.append(f"{rel_path} (non-UI extension)")

        # Sort by relevance score descending, then path
        candidates.sort(key=lambda x: (-x["score"], x["rel_path"]))

        selected = candidates[:MAX_SELECTED_FILES]
        for extra in candidates[MAX_SELECTED_FILES:]:
            skipped.append(f"{extra['rel_path']} (exceeded {MAX_SELECTED_FILES} file cap)")

        return selected, skipped

    def cleanup(self):
        """Safely removes the cloned temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
            self.temp_dir = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
