"""
tests/test_compare.py
─────────────────────
Unit tests for analyzer/compare.py matching logic.
Run: python -m pytest tests/test_compare.py -v
"""

import pytest
from analyzer.compare import compare, _iou, _jaccard, _matches_screenshot, _matches_repo


# ─── Helpers ─────────────────────────────────────────────────────────────────

def make_finding(
    id="f1",
    title="Low contrast text",
    category="Accessibility",
    severity="High",
    location=None,
    code_location=None,
    measured=None,
):
    f = {
        "id": id,
        "title": title,
        "category": category,
        "severity": severity,
        "confidence": 0.9,
        "heuristic": "WCAG 1.4.3",
        "problem": "contrast too low",
        "impact": "hard to read",
        "solution": "increase contrast",
        "evidence": "ratio 2.3:1",
        "source": "llm",
    }
    if location:
        f["location"] = location
    if code_location:
        f["code_location"] = code_location
    if measured:
        f["measured"] = measured
    return f


def make_result(findings, mode="screenshot", scores=None):
    return {
        "run_id": "test",
        "mode": mode,
        "model": {"name": "test", "license": "MIT", "served_by": "local"},
        "image": {"width": 800, "height": 600},
        "summary": {
            "counts": {"critical": 0, "high": len(findings), "medium": 0, "low": 0},
            "scores": scores or {"Accessibility": 60, "Usability": 80},
            "disclaimer": "",
        },
        "findings": findings,
        "fix_plan": [],
        "fix_prompt": "",
    }


# ─── IoU tests ────────────────────────────────────────────────────────────────

class TestIou:
    def test_no_overlap(self):
        a = {"x": 0.0, "y": 0.0, "w": 0.1, "h": 0.1}
        b = {"x": 0.9, "y": 0.9, "w": 0.1, "h": 0.1}
        assert _iou(a, b) == 0.0

    def test_identical_boxes(self):
        box = {"x": 0.2, "y": 0.2, "w": 0.3, "h": 0.3}
        assert _iou(box, box) == pytest.approx(1.0)

    def test_partial_overlap(self):
        a = {"x": 0.0, "y": 0.0, "w": 0.4, "h": 0.4}
        b = {"x": 0.2, "y": 0.2, "w": 0.4, "h": 0.4}
        iou = _iou(a, b)
        assert 0.0 < iou < 1.0

    def test_above_threshold(self):
        a = {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5}
        b = {"x": 0.15, "y": 0.15, "w": 0.5, "h": 0.5}
        assert _iou(a, b) > 0.3


# ─── Jaccard tests ────────────────────────────────────────────────────────────

class TestJaccard:
    def test_identical(self):
        assert _jaccard("Low contrast text", "Low contrast text") == pytest.approx(1.0)

    def test_no_overlap(self):
        assert _jaccard("button color", "missing label") == 0.0

    def test_partial(self):
        score = _jaccard("Low contrast text button", "Low contrast text link")
        assert 0.0 < score < 1.0

    def test_empty_strings(self):
        assert _jaccard("", "") == pytest.approx(1.0)

    def test_above_threshold(self):
        # "contrast ratio low" vs "low contrast ratio" – same tokens
        assert _jaccard("contrast ratio low", "low contrast ratio") == pytest.approx(1.0)


# ─── Screenshot matching tests ────────────────────────────────────────────────

class TestScreenshotMatching:
    def test_same_category_overlapping_box(self):
        a = make_finding(location={"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5})
        b = make_finding(id="f2", location={"x": 0.15, "y": 0.15, "w": 0.5, "h": 0.5})
        assert _matches_screenshot(a, b) is True

    def test_different_category_no_match(self):
        a = make_finding(category="Accessibility", location={"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5})
        b = make_finding(id="f2", category="Usability", location={"x": 0.15, "y": 0.15, "w": 0.5, "h": 0.5})
        assert _matches_screenshot(a, b) is False

    def test_high_title_similarity_no_box(self):
        a = make_finding(title="Low contrast text button")
        b = make_finding(id="f2", title="Low contrast text link")
        assert _matches_screenshot(a, b) is True

    def test_no_overlap_low_jaccard(self):
        a = make_finding(
            title="Navigation menu missing",
            location={"x": 0.0, "y": 0.0, "w": 0.05, "h": 0.05},
        )
        b = make_finding(
            id="f2",
            title="Button color contrast",
            location={"x": 0.9, "y": 0.9, "w": 0.05, "h": 0.05},
        )
        assert _matches_screenshot(a, b) is False


# ─── Repo matching tests ──────────────────────────────────────────────────────

class TestRepoMatching:
    def test_same_file_high_title_similarity(self):
        a = make_finding(
            code_location={"file": "src/App.jsx", "line_start": 10, "line_end": 15},
            title="Missing alt attribute on image",
        )
        b = make_finding(
            id="f2",
            code_location={"file": "src/App.jsx", "line_start": 12, "line_end": 15},
            title="Missing alt attribute image tag",
        )
        assert _matches_repo(a, b) is True

    def test_different_file_no_match(self):
        a = make_finding(
            code_location={"file": "src/App.jsx", "line_start": 10, "line_end": 15},
            title="Low contrast button",
        )
        b = make_finding(
            id="f2",
            code_location={"file": "src/Header.jsx", "line_start": 10, "line_end": 15},
            title="Low contrast button",
        )
        assert _matches_repo(a, b) is False


# ─── compare() end-to-end tests ───────────────────────────────────────────────

class TestCompare:
    def test_identical_runs_all_remaining(self):
        f = make_finding()
        before = make_result([f])
        after = make_result([f])
        result = compare(before, after)
        assert result["counts"]["fixed"] == 0
        assert result["counts"]["remaining"] == 1
        assert result["counts"]["new"] == 0

    def test_all_fixed(self):
        f = make_finding(title="XYZ unique issue alpha")
        before = make_result([f])
        after = make_result([])
        result = compare(before, after)
        assert result["counts"]["fixed"] == 1
        assert result["counts"]["remaining"] == 0
        assert result["counts"]["new"] == 0

    def test_new_finding(self):
        f_new = make_finding(id="f99", title="Completely new unrelated issue here")
        before = make_result([])
        after = make_result([f_new])
        result = compare(before, after)
        assert result["counts"]["new"] == 1
        assert result["counts"]["fixed"] == 0

    def test_partial_fix(self):
        f_fixed = make_finding(id="f1", title="Low contrast nav text")
        f_remaining = make_finding(
            id="f2", title="Missing focus indicator", category="Accessibility"
        )
        f_remaining_after = make_finding(
            id="f3", title="Missing focus indicator outline", category="Accessibility"
        )
        before = make_result([f_fixed, f_remaining])
        after = make_result([f_remaining_after])
        result = compare(before, after)
        assert result["counts"]["fixed"] == 1
        assert result["counts"]["remaining"] == 1
        assert result["counts"]["new"] == 0

    def test_summary_string_format(self):
        f = make_finding()
        before = make_result([f])
        after = make_result([])
        result = compare(before, after)
        assert "fixed" in result["summary"]
        assert "remaining" in result["summary"]

    def test_score_deltas(self):
        f = make_finding()
        before = make_result([f], scores={"Accessibility": 50, "Usability": 70})
        after = make_result([], scores={"Accessibility": 80, "Usability": 70})
        result = compare(before, after)
        deltas = result["score_deltas"]
        assert deltas["Accessibility"]["delta"] == 30
        assert deltas["Usability"]["delta"] == 0

    def test_contrast_deltas(self):
        f_before = make_finding(measured={"ratio": 2.3, "fg": "#aaa", "bg": "#fff"})
        f_after = make_finding(id="f1", measured={"ratio": 4.8, "fg": "#555", "bg": "#fff"})
        before = make_result([f_before])
        after = make_result([f_after])
        result = compare(before, after)
        assert len(result["contrast_deltas"]) == 1
        cd = result["contrast_deltas"][0]
        assert cd["before_ratio"] == 2.3
        assert cd["after_ratio"] == 4.8

    def test_empty_before_and_after(self):
        before = make_result([])
        after = make_result([])
        result = compare(before, after)
        assert result["counts"]["fixed"] == 0
        assert result["counts"]["new"] == 0
        assert result["counts"]["remaining"] == 0
