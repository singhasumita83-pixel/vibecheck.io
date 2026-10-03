"""
analyzer/compare.py
───────────────────
Compare two VibeCheck analysis results (before / after) and produce a
structured delta report.

Matching strategy
-----------------
For **screenshot mode** findings match when:
  category equals  AND  ( IoU(box_before, box_after) > 0.3
                          OR  title Jaccard similarity > 0.5 )

For **repo mode** findings match when:
  file equals  AND  (rule_id / title Jaccard similarity > 0.5)

Unmatched old findings  → fixed
Unmatched new findings  → new
Matched findings        → remaining

"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


# ─── Box IoU ─────────────────────────────────────────────────────────────────

def _iou(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Intersection-over-Union for two normalised boxes {x, y, w, h}."""
    ax1, ay1 = a.get("x", 0), a.get("y", 0)
    ax2, ay2 = ax1 + a.get("w", 0), ay1 + a.get("h", 0)
    bx1, by1 = b.get("x", 0), b.get("y", 0)
    bx2, by2 = bx1 + b.get("w", 0), by1 + b.get("h", 0)

    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union > 0 else 0.0


# ─── Title token Jaccard ─────────────────────────────────────────────────────

def _jaccard(title_a: str, title_b: str) -> float:
    """Token-level Jaccard similarity (lowercased words)."""
    tokens_a = set(title_a.lower().split())
    tokens_b = set(title_b.lower().split())
    if not tokens_a and not tokens_b:
        return 1.0
    union = tokens_a | tokens_b
    if not union:
        return 0.0
    return len(tokens_a & tokens_b) / len(union)


# ─── Finding accessors (works for dicts and Pydantic models) ─────────────────

def _g(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _finding_to_dict(f: Any) -> Dict:
    if hasattr(f, "model_dump"):
        return f.model_dump()
    if isinstance(f, dict):
        return f
    return {}


# ─── Matching ────────────────────────────────────────────────────────────────

IOU_THRESHOLD = 0.3
JACCARD_THRESHOLD = 0.5


def _matches_screenshot(a: Dict, b: Dict) -> bool:
    """Return True if two screenshot-mode findings are the same issue."""
    if _g(a, "category") != _g(b, "category"):
        return False
    loc_a = _g(a, "location") or {}
    loc_b = _g(b, "location") or {}
    if loc_a and loc_b:
        if _iou(loc_a, loc_b) > IOU_THRESHOLD:
            return True
    return _jaccard(_g(a, "title", ""), _g(b, "title", "")) > JACCARD_THRESHOLD


def _matches_repo(a: Dict, b: Dict) -> bool:
    """Return True if two repo-mode findings are the same issue."""
    loc_a = _g(a, "code_location") or {}
    loc_b = _g(b, "code_location") or {}
    if hasattr(loc_a, "__dict__"):
        loc_a = loc_a.__dict__
    if hasattr(loc_b, "__dict__"):
        loc_b = loc_b.__dict__

    file_a = loc_a.get("file", "") if isinstance(loc_a, dict) else ""
    file_b = loc_b.get("file", "") if isinstance(loc_b, dict) else ""
    if file_a != file_b:
        return False
    return _jaccard(_g(a, "title", ""), _g(b, "title", "")) > JACCARD_THRESHOLD


def _match_findings(
    before_findings: List[Dict],
    after_findings: List[Dict],
    mode: str,
) -> Tuple[List[Dict], List[Dict], List[Tuple[Dict, Dict]]]:
    """
    Greedy O(n*m) matching.

    Returns:
        fixed     – before findings with no match in after
        new       – after findings with no match in before
        remaining – list of (before_finding, after_finding) pairs
    """
    matcher = _matches_repo if mode == "repo" else _matches_screenshot

    matched_after_indices: set = set()
    remaining: List[Tuple[Dict, Dict]] = []
    fixed: List[Dict] = []

    for bf in before_findings:
        found = False
        for j, af in enumerate(after_findings):
            if j in matched_after_indices:
                continue
            if matcher(bf, af):
                remaining.append((bf, af))
                matched_after_indices.add(j)
                found = True
                break
        if not found:
            fixed.append(bf)

    new_findings = [
        af for j, af in enumerate(after_findings)
        if j not in matched_after_indices
    ]

    return fixed, new_findings, remaining


# ─── Score delta ─────────────────────────────────────────────────────────────

def _score_deltas(
    before_scores: Dict[str, int],
    after_scores: Dict[str, int],
) -> Dict[str, Dict[str, int]]:
    """Return per-category {before, after, delta}."""
    all_cats = set(before_scores) | set(after_scores)
    return {
        cat: {
            "before": before_scores.get(cat, 100),
            "after": after_scores.get(cat, 100),
            "delta": after_scores.get(cat, 100) - before_scores.get(cat, 100),
        }
        for cat in sorted(all_cats)
    }


# ─── Public API ──────────────────────────────────────────────────────────────

def compare(before: Any, after: Any) -> Dict:
    """
    Compare two analysis results.

    Parameters
    ----------
    before, after : dict or AnalysisResponse
        Full result objects as returned by /api/analyze or /api/analyze-repo.

    Returns
    -------
    dict with keys:
        fixed        – list of findings resolved between runs
        remaining    – list of findings still present (with before/after pair)
        new          – list of findings that appeared in the after run
        score_deltas – per-category {before, after, delta}
        summary      – human-readable summary string
        contrast_deltas – list of {id, before_ratio, after_ratio} for matched
                          findings that have contrast measurements in both runs
    """
    if hasattr(before, "model_dump"):
        before = before.model_dump()
    elif not isinstance(before, dict):
        before = {}

    if hasattr(after, "model_dump"):
        after = after.model_dump()
    elif not isinstance(after, dict):
        after = {}

    mode = after.get("mode") or before.get("mode") or "screenshot"

    before_findings = [_finding_to_dict(f) for f in (before.get("findings") or [])]
    after_findings = [_finding_to_dict(f) for f in (after.get("findings") or [])]

    fixed, new_list, remaining_pairs = _match_findings(
        before_findings, after_findings, mode
    )

    before_scores: Dict[str, int] = (before.get("summary") or {}).get("scores") or {}
    after_scores: Dict[str, int] = (after.get("summary") or {}).get("scores") or {}
    deltas = _score_deltas(before_scores, after_scores)

    # Contrast deltas for matched pairs
    contrast_deltas = []
    for bf, af in remaining_pairs:
        bm = bf.get("measured")
        am = af.get("measured")
        if bm and am:
            br = bm.get("ratio")
            ar = am.get("ratio")
            if br is not None and ar is not None:
                contrast_deltas.append({
                    "id": af.get("id") or bf.get("id"),
                    "title": af.get("title") or bf.get("title", ""),
                    "before_ratio": br,
                    "after_ratio": ar,
                })

    n_fixed = len(fixed)
    n_new = len(new_list)
    n_remaining = len(remaining_pairs)
    n_total_before = len(before_findings)

    summary = (
        f"{n_fixed} of {n_total_before} fixed, "
        f"{n_new} new, "
        f"{n_remaining} remaining"
    )

    return {
        "fixed": fixed,
        "remaining": [{"before": bf, "after": af} for bf, af in remaining_pairs],
        "new": new_list,
        "score_deltas": deltas,
        "contrast_deltas": contrast_deltas,
        "summary": summary,
        "counts": {
            "fixed": n_fixed,
            "new": n_new,
            "remaining": n_remaining,
            "total_before": n_total_before,
        },
    }
