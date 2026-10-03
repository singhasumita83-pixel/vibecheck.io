import datetime
from typing import Dict, Any, Union

SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
SEV_MARKS = {"Critical": "■", "High": "●", "Medium": "◐", "Low": "○"}

def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def build_markdown(result: Union[Dict[str, Any], Any]) -> str:
    """
    Takes an /api/analyze or /api/analyze-repo result (dict or AnalysisResponse)
    and formats it into a comprehensive GitHub-flavored Markdown report.
    """
    if hasattr(result, "model_dump"):
        data = result.model_dump()
    elif isinstance(result, dict):
        data = result
    else:
        data = {}

    run_id = data.get("run_id", "vibecheck-report")
    mode = data.get("mode", "screenshot")
    repo_info = data.get("repo_info") or {}
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append("# VibeCheck UX Audit Report")
    lines.append("")
    lines.append(f"**Date:** {now_str}  ")
    lines.append(f"**Audit ID:** `{run_id}`  ")
    lines.append(f"**Mode:** {mode.capitalize()}")
    if repo_info and repo_info.get("url"):
        lines.append(f"**Repository:** [{repo_info.get('url')}]({repo_info.get('url')}) @ `{repo_info.get('branch', 'main')}`")
    lines.append("")

    # --- Summary Section ---
    summary = data.get("summary") or {}
    counts = summary.get("counts") or {}
    scores = summary.get("scores") or {}
    disclaimer = summary.get("disclaimer") or "AI heuristic indicators, not validated UX metrics."

    crit = counts.get("critical", 0)
    high = counts.get("high", 0)
    med = counts.get("medium", 0)
    low = counts.get("low", 0)
    total_issues = crit + high + med + low

    lines.append("## Summary")
    lines.append("")
    lines.append("| Severity | Count | Mark |")
    lines.append("|---|---|---|")
    lines.append(f"| Critical | {crit} | {SEV_MARKS['Critical']} |")
    lines.append(f"| High | {high} | {SEV_MARKS['High']} |")
    lines.append(f"| Medium | {med} | {SEV_MARKS['Medium']} |")
    lines.append(f"| Low | {low} | {SEV_MARKS['Low']} |")
    lines.append(f"| **Total** | **{total_issues}** | |")
    lines.append("")

    if scores:
        lines.append("### Category Scores")
        lines.append("")
        lines.append("| Category | Score (0-100) |")
        lines.append("|---|---|")
        for cat, score in scores.items():
            lines.append(f"| {cat} | {score} |")
        lines.append("")
        lines.append(f"*({disclaimer})*")
        lines.append("")

    # --- Findings Section ---
    findings = list(data.get("findings") or [])
    # Sort findings by severity
    findings.sort(key=lambda f: (SEV_ORDER.get(f.get("severity", "Low"), 4), f.get("id", "")))

    lines.append("## Findings")
    lines.append("")

    if not findings:
        lines.append("_Nothing serious found. Try the mobile view or another page next._")
        lines.append("")
    else:
        for idx, f in enumerate(findings, start=1):
            sev = f.get("severity", "Medium")
            mark = SEV_MARKS.get(sev, "•")
            title = f.get("title", "Untitled finding")
            cat = f.get("category", "Usability")

            # Location formatting
            loc_str = "Unknown"
            code_loc = f.get("code_location")
            location = f.get("location")
            if code_loc and isinstance(code_loc, dict):
                loc_str = f"`{code_loc.get('file', 'unknown')}:{code_loc.get('line_start', '?')}`"
            elif location and isinstance(location, dict):
                x_pct = round(location.get("x", 0) * 100)
                y_pct = round(location.get("y", 0) * 100)
                loc_str = f"Region: x={x_pct}%, y={y_pct}%"

            lines.append(f"### {idx}. [{sev}] {title}")
            lines.append(f"- **Severity:** {mark} {sev}")
            lines.append(f"- **Category:** {cat}")
            lines.append(f"- **Location:** {loc_str}")
            if f.get("heuristic"):
                lines.append(f"- **Heuristic:** {f['heuristic']}")
            lines.append("")

            if f.get("problem"):
                lines.append(f"**Why (Problem):**  \n{f['problem']}")
                lines.append("")

            if f.get("impact"):
                lines.append(f"**Impact:**  \n{f['impact']}")
                lines.append("")

            if f.get("solution"):
                lines.append(f"**Fix:**  \n{f['solution']}")
                lines.append("")

            if f.get("evidence"):
                lines.append(f"**Evidence:**  \n`{f['evidence']}`")
                lines.append("")

            # Contrast measurement if present
            if f.get("measured"):
                m = f["measured"]
                ratio = m.get("ratio", "?")
                fg = m.get("fg", "")
                bg = m.get("bg", "")
                sug_fg = m.get("suggested_fg", "")
                sug_ratio = m.get("suggested_ratio", "4.5:1")
                lines.append(f"**Measured Contrast:** `{ratio}` (current fg: `{fg}`, bg: `{bg}`) → Suggested fg: `{sug_fg}` (ratio: `{sug_ratio}`)")
                lines.append("")

            if f.get("snippet"):
                lines.append("**Code Snippet:**")
                lines.append("```")
                lines.append(f.get("snippet").strip())
                lines.append("```")
                lines.append("")

            fix_obj = f.get("fix")
            if fix_obj and isinstance(fix_obj, dict) and fix_obj.get("diff"):
                lines.append("**Proposed Diff:**")
                lines.append("```diff")
                lines.append(fix_obj["diff"].strip())
                lines.append("```")
                lines.append("")

            lines.append("---")
            lines.append("")

    # --- Fix Plan Section ---
    fix_plan = data.get("fix_plan") or []
    if fix_plan:
        lines.append("## Fix Plan")
        lines.append("")
        for item in fix_plan:
            prio = item.get("priority", 1)
            title = item.get("title", "")
            fids = item.get("finding_ids", [])
            fids_str = f" (issues: {', '.join(fids)})" if fids else ""
            lines.append(f"{prio}. **{title}**{fids_str}")
        lines.append("")

    # --- Fix Prompt Section ---
    fix_prompt = data.get("fix_prompt", "")
    if fix_prompt:
        lines.append("## Fix Prompt")
        lines.append("")
        lines.append("> Hand this prompt to your coding assistant (Cursor, Lovable, Bolt, v0, Claude Code):")
        lines.append("")
        lines.append("```text")
        lines.append(fix_prompt.strip())
        lines.append("```")
        lines.append("")

    # --- Footer with Model Info ---
    model = data.get("model") or {}
    model_name = model.get("name", "Qwen-VL")
    model_license = model.get("license", "Open-Weight")
    served_by = model.get("served_by", "local")

    lines.append("---")
    lines.append(f"*Audited by VibeCheck · Model: **{model_name}** · License: {model_license} · Served: {served_by}*")

    return "\n".join(lines)
