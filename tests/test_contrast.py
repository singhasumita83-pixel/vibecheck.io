import unittest
from PIL import Image
from analyzer.contrast import (
    relative_luminance,
    contrast_ratio,
    estimate_colors,
    suggest_accessible_fg,
    apply_contrast_measurements
)

class TestContrast(unittest.TestCase):
    def test_known_color_pairs(self):
        # Black on white: 21:1
        ratio_bw = contrast_ratio("#000000", "#ffffff")
        self.assertAlmostEqual(ratio_bw, 21.0, places=1)

        # White on black: 21:1
        ratio_wb = contrast_ratio("#ffffff", "#000000")
        self.assertAlmostEqual(ratio_wb, 21.0, places=1)

        # #777777 on #ffffff: about 4.48:1
        ratio_777 = contrast_ratio("#777777", "#ffffff")
        self.assertAlmostEqual(ratio_777, 4.48, places=2)

    def test_suggestion_reaches_target(self):
        # #777 on white is 4.48 (< 4.5)
        suggested_fg, suggested_ratio = suggest_accessible_fg("#777777", "#ffffff", target=4.5)
        self.assertGreaterEqual(suggested_ratio, 4.5)
        self.assertNotEqual(suggested_fg, "#777777")

        # Faint gray on dark background
        sugg_fg2, sugg_ratio2 = suggest_accessible_fg("#444444", "#111111", target=4.5)
        self.assertGreaterEqual(sugg_ratio2, 4.5)

        # Already passing color pair remains unchanged
        sugg_pass, ratio_pass = suggest_accessible_fg("#000000", "#ffffff", target=4.5)
        self.assertEqual(sugg_pass, "#000000")
        self.assertAlmostEqual(ratio_pass, 21.0, places=1)

    def test_tiny_and_empty_boxes_dont_crash(self):
        # 100x100 white image
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))

        # Empty box (zero width/height)
        zero_box = {"x": 0.5, "y": 0.5, "w": 0.0, "h": 0.0}
        res_zero = estimate_colors(img, zero_box)
        self.assertIn("fg", res_zero)
        self.assertIn("bg", res_zero)
        self.assertIn("ratio", res_zero)

        # Negative / tiny coords
        tiny_box = {"x": 0.0, "y": 0.0, "w": 0.0001, "h": 0.0001}
        res_tiny = estimate_colors(img, tiny_box)
        self.assertIn("fg", res_tiny)

        # Out-of-bounds box
        oob_box = {"x": 1.5, "y": 1.5, "w": 0.2, "h": 0.2}
        res_oob = estimate_colors(img, oob_box)
        self.assertIn("fg", res_oob)

        # None box
        res_none = estimate_colors(img, None)
        self.assertIn("fg", res_none)

    def test_color_estimation_on_rendered_box(self):
        # Create an image with white background and a red text box
        img = Image.new("RGB", (200, 200), color=(255, 255, 255))
        # Draw some dark blue pixels inside box (x=0.2..0.4, y=0.2..0.4)
        for x in range(40, 80):
            for y in range(40, 80):
                img.putpixel((x, y), (10, 20, 100))

        box = {"x": 0.15, "y": 0.15, "w": 0.3, "h": 0.3}
        colors = estimate_colors(img, box)
        self.assertIn("fg", colors)
        self.assertIn("bg", colors)
        # Background should be white or close to white
        self.assertEqual(colors["bg"].lower(), "#f8f8f8") # quantized white
        self.assertGreater(colors["ratio"], 4.5)

    def test_apply_contrast_measurements(self):
        img = Image.new("RGB", (200, 200), color=(255, 255, 255))
        findings = [
            {
                "id": "f1",
                "title": "Low contrast button",
                "category": "Accessibility",
                "severity": "High",
                "confidence": 0.9,
                "location": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2},
                "problem": "Contrast is faint",
                "evidence": "Original evidence"
            },
            {
                "id": "f2",
                "title": "Unrelated issue",
                "category": "Usability",
                "severity": "Low",
                "confidence": 0.7,
                "location": {"x": 0.5, "y": 0.5, "w": 0.2, "h": 0.2},
                "problem": "Button position",
                "evidence": "Original"
            }
        ]
        apply_contrast_measurements(findings, img)
        self.assertIn("measured", findings[0])
        self.assertIn("Measured contrast", findings[0]["evidence"])
        self.assertNotIn("measured", findings[1])

if __name__ == "__main__":
    unittest.main()
