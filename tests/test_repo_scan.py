import unittest
from analyzer.repo_scan import RepoScanner, calculate_contrast_ratio

class TestRepoScan(unittest.TestCase):
    def setUp(self):
        self.scanner = RepoScanner()

    def test_contrast_ratio_calculation(self):
        # Black on white: 21:1
        ratio_bw = calculate_contrast_ratio("#000000", "#ffffff")
        self.assertGreaterEqual(ratio_bw, 20.0)

        # Light gray on white: low contrast
        ratio_low = calculate_contrast_ratio("#cccccc", "#ffffff")
        self.assertLess(ratio_low, 3.0)

    def test_img_without_alt(self):
        html = '<div class="banner">\n  <img src="logo.png">\n</div>'
        findings = self.scanner.scan_file("src/Header.jsx", html)
        img_findings = [f for f in findings if "alt" in f.title.lower()]
        self.assertEqual(len(img_findings), 1)
        self.assertEqual(img_findings[0].code_location.line_start, 2)
        self.assertEqual(img_findings[0].category, "Accessibility")

    def test_input_without_label(self):
        html = '<form>\n  <input type="email" placeholder="email" />\n</form>'
        findings = self.scanner.scan_file("src/Login.html", html)
        input_findings = [f for f in findings if "input" in f.title.lower()]
        self.assertEqual(len(input_findings), 1)
        self.assertEqual(input_findings[0].code_location.line_start, 2)

    def test_clickable_div(self):
        jsx = '<div onClick={() => submit()}>Click me</div>'
        findings = self.scanner.scan_file("src/Button.jsx", jsx)
        div_findings = [f for f in findings if "clickable" in f.title.lower()]
        self.assertEqual(len(div_findings), 1)

    def test_fixed_width_overflow(self):
        css = '.container {\n  width: 1200px;\n}'
        findings = self.scanner.scan_file("styles/layout.css", css)
        width_findings = [f for f in findings if "fixed" in f.title.lower()]
        self.assertEqual(len(width_findings), 1)
        self.assertEqual(width_findings[0].category, "Responsive")

    def test_outline_none(self):
        css = 'button:focus {\n  outline: none;\n}'
        findings = self.scanner.scan_file("styles/button.css", css)
        outline_findings = [f for f in findings if "outline" in f.title.lower()]
        self.assertEqual(len(outline_findings), 1)

if __name__ == "__main__":
    unittest.main()
