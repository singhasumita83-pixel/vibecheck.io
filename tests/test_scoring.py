import unittest
from analyzer.schema import Finding, Location
from analyzer.scoring import calculate_summary, rank_findings
from analyzer.fixprompt import build_fix_plan, build_fix_prompt

class TestScoringAndFixPrompt(unittest.TestCase):
    def setUp(self):
        self.findings = [
            Finding(
                id="raw_1",
                title="Low contrast text",
                category="Accessibility",
                severity="Critical",
                confidence=1.0,
                heuristic="WCAG 2.1 Contrast",
                location=Location(x=0.1, y=0.1, w=0.1, h=0.1),
                problem="Low contrast text",
                impact="Unreadable",
                solution="Darken text",
                evidence="Ratio 2:1"
            ),
            Finding(
                id="raw_2",
                title="Secondary style on CTA",
                category="Visual Hierarchy",
                severity="High",
                confidence=0.8,
                heuristic="Nielsen #4",
                location=Location(x=0.5, y=0.5, w=0.2, h=0.1),
                problem="CTA looks secondary",
                impact="Missed action",
                solution="Fill with primary color",
                evidence="Luminance similarity"
            )
        ]

    def test_ranking_order(self):
        ranked = rank_findings(self.findings)
        self.assertEqual(ranked[0].id, "f1")
        self.assertEqual(ranked[0].severity, "Critical")
        self.assertEqual(ranked[1].id, "f2")
        self.assertEqual(ranked[1].severity, "High")

    def test_category_scores(self):
        summary = calculate_summary(self.findings)
        # Accessibility has 1 Critical finding with confidence 1.0 -> penalty 25 -> score 75
        self.assertEqual(summary.scores["Accessibility"], 75)
        # Visual Hierarchy has 1 High finding with conf 0.8 -> penalty 15 * 0.8 = 12 -> score 88
        self.assertEqual(summary.scores["Visual Hierarchy"], 88)
        # Usability has 0 findings -> score 100
        self.assertEqual(summary.scores["Usability"], 100)
        # Mandatory disclaimer
        self.assertEqual(summary.disclaimer, "AI heuristic indicators, not validated UX metrics.")

    def test_fix_plan_and_prompt(self):
        plan = build_fix_plan(self.findings, max_items=2)
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0].priority, 1)

        prompt = build_fix_prompt(self.findings, persona="College student", goal="Sign up")
        self.assertIn("College student", prompt)
        self.assertIn("Sign up", prompt)
        self.assertIn("Low contrast text", prompt)
        self.assertIn("WCAG AA compliance", prompt)

if __name__ == "__main__":
    unittest.main()
