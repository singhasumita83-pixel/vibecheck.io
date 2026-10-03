import unittest
from analyzer.schema import Finding, CodeLocation
from analyzer.repo_fix import RepoFixer, generate_unified_diff

class TestRepoFix(unittest.TestCase):
    def setUp(self):
        self.fixer = RepoFixer()

    def test_generate_unified_diff(self):
        diff = generate_unified_diff("src/App.jsx", "<img src='logo.png'>", "<img alt='logo' src='logo.png'>", 12)
        self.assertIn("--- a/src/App.jsx", diff)
        self.assertIn("+++ b/src/App.jsx", diff)
        self.assertIn("-<img src='logo.png'>", diff)
        self.assertIn("+<img alt='logo' src='logo.png'>", diff)

    def test_synthesize_fix_img_alt(self):
        finding = Finding(
            id="static_img_alt_2",
            title="Image missing alt",
            category="Accessibility",
            severity="High",
            confidence=0.9,
            heuristic="WCAG 1.1.1",
            code_location=CodeLocation(file="src/Header.jsx", line_start=2, line_end=2),
            problem="Missing alt",
            impact="No screen reader info",
            solution="Add alt attribute",
            evidence="rule img_alt"
        )
        content = "<div>\n  <img src='photo.jpg'>\n</div>"
        fix = self.fixer.synthesize_fix(finding, content)
        self.assertIsNotNone(fix)
        self.assertTrue(fix.validated)
        self.assertIn("alt=", fix.diff)

    def test_combine_patches(self):
        f1 = Finding(
            id="r1",
            title="Image missing alt text",
            category="Accessibility",
            severity="High",
            confidence=0.9,
            heuristic="WCAG",
            code_location=CodeLocation(file="a.html", line_start=1, line_end=1),
            problem="", impact="", solution="", evidence=""
        )
        fix1 = self.fixer.synthesize_fix(f1, "<img src='a.png'>")
        f1.fix = fix1

        combined = self.fixer.combine_patches([f1])
        self.assertIn("--- a/a.html", combined)

if __name__ == "__main__":
    unittest.main()
