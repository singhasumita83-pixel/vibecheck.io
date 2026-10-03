"""
tests/test_cli.py
──────────────────
Unit tests for cli.py – argument parsing and exit-code logic.
Run: python -m pytest tests/test_cli.py -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on path when run from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import build_parser, should_fail, main


# ─── Argument parsing ─────────────────────────────────────────────────────────

class TestArgParsing:
    def test_defaults(self):
        p = build_parser()
        args = p.parse_args(["demo.png"])
        assert args.screenshot == "demo.png"
        assert args.persona == ""
        assert args.goal == ""
        assert args.output_json is False
        assert args.md is None
        assert args.fail_on is None

    def test_full_args(self):
        p = build_parser()
        args = p.parse_args([
            "ui.png",
            "--persona", "mobile user",
            "--goal", "signup",
            "--json",
            "--md", "report.md",
            "--fail-on", "high",
        ])
        assert args.screenshot == "ui.png"
        assert args.persona == "mobile user"
        assert args.goal == "signup"
        assert args.output_json is True
        assert args.md == "report.md"
        assert args.fail_on == "high"

    def test_fail_on_choices(self):
        p = build_parser()
        for level in ("critical", "high", "medium", "low"):
            args = p.parse_args(["x.png", "--fail-on", level])
            assert args.fail_on == level

    def test_invalid_fail_on_raises(self):
        p = build_parser()
        with pytest.raises(SystemExit):
            p.parse_args(["x.png", "--fail-on", "extreme"])


# ─── Exit-code logic ─────────────────────────────────────────────────────────

class TestShouldFail:
    @pytest.fixture
    def findings(self):
        return [
            {"severity": "Critical"},
            {"severity": "High"},
            {"severity": "Medium"},
            {"severity": "Low"},
        ]

    def test_no_fail_on(self, findings):
        assert should_fail(findings, None) is False

    def test_fail_on_critical_only(self):
        findings = [{"severity": "High"}, {"severity": "Medium"}]
        assert should_fail(findings, "critical") is False

    def test_fail_on_high_with_high(self):
        findings = [{"severity": "High"}]
        assert should_fail(findings, "high") is True

    def test_fail_on_high_with_critical(self):
        findings = [{"severity": "Critical"}]
        assert should_fail(findings, "high") is True

    def test_fail_on_medium(self):
        findings = [{"severity": "Medium"}]
        assert should_fail(findings, "medium") is True

    def test_fail_on_low(self):
        findings = [{"severity": "Low"}]
        assert should_fail(findings, "low") is True

    def test_empty_findings(self):
        assert should_fail([], "high") is False

    def test_all_severities_fail_on_critical(self, findings):
        assert should_fail(findings, "critical") is True


# ─── main() integration (mocked pipeline) ────────────────────────────────────

def _make_mock_result(severity="High"):
    finding = {
        "id": "f1", "title": "Low contrast", "category": "Accessibility",
        "severity": severity, "confidence": 0.9, "heuristic": "WCAG 1.4.3",
        "problem": "p", "impact": "i", "solution": "s", "evidence": "e",
        "source": "llm", "location": None, "code_location": None,
        "snippet": None, "fix": None, "measured": None,
    }
    return MagicMock(
        model_dump=lambda: {
            "run_id": "test-run",
            "mode": "screenshot",
            "model": {"name": "test", "license": "MIT", "served_by": "local"},
            "image": {"width": 800, "height": 600},
            "summary": {
                "counts": {"critical": 0, "high": 1, "medium": 0, "low": 0},
                "scores": {"Accessibility": 55},
                "disclaimer": "",
                "verified_fixes": 0,
            },
            "findings": [finding],
            "fix_plan": [],
            "fix_prompt": "",
        }
    )


class TestMain:
    def test_missing_file_returns_2(self, tmp_path):
        code = main([str(tmp_path / "nonexistent.png")])
        assert code == 2

    def test_not_a_file_returns_2(self, tmp_path):
        d = tmp_path / "a_dir"
        d.mkdir()
        code = main([str(d)])
        assert code == 2

    def test_successful_analysis_exit_0(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"FAKEPNG")

        mock_result = _make_mock_result(severity="Low")

        with patch("analyzer.pipeline.AnalysisPipeline") as MockPipeline:
            instance = MockPipeline.return_value
            instance.analyze.return_value = mock_result
            code = main([str(img)])
        assert code == 0

    def test_fail_on_high_exits_1_when_high_found(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"FAKEPNG")

        mock_result = _make_mock_result(severity="High")

        with patch("analyzer.pipeline.AnalysisPipeline") as MockPipeline:
            instance = MockPipeline.return_value
            instance.analyze.return_value = mock_result
            code = main([str(img), "--fail-on", "high"])
        assert code == 1

    def test_fail_on_critical_exits_0_when_only_high(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"FAKEPNG")

        mock_result = _make_mock_result(severity="High")

        with patch("analyzer.pipeline.AnalysisPipeline") as MockPipeline:
            instance = MockPipeline.return_value
            instance.analyze.return_value = mock_result
            code = main([str(img), "--fail-on", "critical"])
        assert code == 0

    def test_json_output(self, tmp_path, capsys):
        img = tmp_path / "test.png"
        img.write_bytes(b"FAKEPNG")

        mock_result = _make_mock_result()

        with patch("analyzer.pipeline.AnalysisPipeline") as MockPipeline:
            instance = MockPipeline.return_value
            instance.analyze.return_value = mock_result
            code = main([str(img), "--json"])

        out = capsys.readouterr().out
        data = json.loads(out)
        assert "findings" in data
        assert code == 0

    def test_md_report_written(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"FAKEPNG")
        md_path = tmp_path / "report.md"

        mock_result = _make_mock_result()

        with patch("analyzer.pipeline.AnalysisPipeline") as MockPipeline:
            instance = MockPipeline.return_value
            instance.analyze.return_value = mock_result
            code = main([str(img), "--md", str(md_path)])

        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")
        assert "VibeCheck" in content
