import unittest
from analyzer.coords import to_normalized, clamp

class TestCoords(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(clamp(-0.5), 0.0)
        self.assertEqual(clamp(1.5), 1.0)
        self.assertEqual(clamp(0.42), 0.42)

    def test_normalized_coords(self):
        box = {"x": 0.25, "y": 0.50, "w": 0.20, "h": 0.10}
        norm = to_normalized(box, convention="normalized")
        self.assertEqual(norm.x, 0.25)
        self.assertEqual(norm.y, 0.50)
        self.assertEqual(norm.w, 0.20)
        self.assertEqual(norm.h, 0.10)

    def test_rel_1000_coords(self):
        # 0..1000 scale (Qwen-VL box convention)
        box = {"x": 250, "y": 500, "w": 200, "h": 100}
        norm = to_normalized(box, convention="rel_1000")
        self.assertEqual(norm.x, 0.25)
        self.assertEqual(norm.y, 0.50)
        self.assertEqual(norm.w, 0.20)
        self.assertEqual(norm.h, 0.10)

    def test_abs_pixels_coords(self):
        # Pixel coordinates based on 1000x500 image
        box = {"x": 250, "y": 250, "w": 200, "h": 100}
        norm = to_normalized(box, convention="abs_pixels", img_w=1000, img_h=500)
        self.assertEqual(norm.x, 0.25)
        self.assertEqual(norm.y, 0.50)
        self.assertEqual(norm.w, 0.20)
        self.assertEqual(norm.h, 0.20)

    def test_boundary_clamping(self):
        # Out of bounds coordinates should safely clamp
        box = {"x": 0.98, "y": 0.99, "w": 0.5, "h": 0.5}
        norm = to_normalized(box, convention="normalized")
        self.assertLessEqual(norm.x + norm.w, 1.0)
        self.assertLessEqual(norm.y + norm.h, 1.0)

if __name__ == "__main__":
    unittest.main()
