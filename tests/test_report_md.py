import unittest
from analyzer.report_md import build_markdown

class TestReportMarkdown(unittest.TestCase):
    def setUp(self):
        self.sample_result = {
            "run_id": "audit-test-123",
            "mode": "screenshot",
            "model": {
                "name": "Qwen2.5-VL-7B",
                "license": "Apache 2.0",
                "served_by": "local"
            },
            "summary": {
                "counts": {"critical": 1, "high": 2, "medium": 1, "low": 0},
                "scores": {"Usability": 70, "Accessibility": 55},
                "disclaimer": "AI heuristic indicators, not validated UX metrics."
            },
            "findings": [
                {
                    "id": "f2",
                    "title": "Low button padding",
                    "category": "Usability",
                    "severity": "Medium",
                    "confidence": 0.8,
                    "heuristic": "Target size",
                    "location": {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4},
                    "problem": "Click target is too small",
                    "impact": "Users miss the button",
                    "solution": "Add padding",
                    "evidence": "Padding is 4px"
                },
                {
                    "id": "f1",
                    "title": "Unreadable gray text",
                    "category": "Accessibility",
                    "severity": "Critical",
                    "confidence": 0.95,
                    "heuristic": "WCAG 1.4.3",
                    "location": {"x": 0.5, "y": 0.6, "w": 0.2, "h": 0.1},
                    "problem": "Contrast is 2.1:1",
                    "impact": "Text cannot be read",
                    "solution": "Darken font",
                    "evidence": "Contrast 2.1:1"
                }
            ],
            "fix_plan": [
                {"priority": 1, "title": "Fix contrast", "finding_ids": ["f1"]},
                {"priority": 2, "title": "Increase padding", "finding_ids": ["f2"]}
            ],
            "fix_prompt": "Please update styles.css to darken text and increase padding."
        }

    def test_headings_and_structure(self):
        md = build_markdown(self.sample_result)
        self.assertIn("# VibeCheck UX Audit Report", md)
        self.assertIn("## Summary", md)
        self.assertIn("## Findings", md)
        self.assertIn("## Fix Plan", md)
        self.assertIn("## Fix Prompt", md)
        self.assertIn("audit-test-123", md)
        self.assertIn("Qwen2.5-VL-7B", md)
        self.assertIn("Apache 2.0", md)

    def test_severity_ordering(self):
        md = build_markdown(self.sample_result)
        # Critical finding (f1) should appear before Medium finding (f2)
        idx_critical = md.find("Unreadable gray text")
        idx_medium = md.find("Low button padding")
        self.assertTrue(idx_critical < idx_medium, "Critical findings must precede Medium findings")

    def test_robust_with_missing_optional_fields(self):
        sparse_result = {
            "run_id": "sparse-456",
            "findings": [
                {
                    "id": "f_sparse",
                    "title": "Bare finding",
                    "category": "Usability",
                    "severity": "Low",
                    "confidence": 0.5
                }
            ]
        }
        # Must not raise an exception
        md = build_markdown(sparse_result)
        self.assertIn("Bare finding", md)
        self.assertIn("sparse-456", md)

    def test_empty_findings(self):
        empty_result = {
            "run_id": "empty-789",
            "findings": []
        }
        md = build_markdown(empty_result)
        self.assertIn("Nothing serious found", md)

    def test_api_report_md_endpoint(self):
        from app import app
        with app.test_client() as client:
            resp = client.post("/api/report.md", json=self.sample_result)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("text/markdown", resp.headers.get("Content-Type", ""))
            self.assertIn("attachment; filename=\"vibecheck-audit-test-123.md\"", resp.headers.get("Content-Disposition", ""))
            md_text = resp.data.decode("utf-8")
            self.assertIn("# VibeCheck UX Audit Report", md_text)
            self.assertIn("Unreadable gray text", md_text)

if __name__ == "__main__":
    unittest.main()
