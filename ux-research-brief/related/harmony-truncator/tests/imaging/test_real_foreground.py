"""Regression against visual boxes frozen before foreground predictions."""
import unittest
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
from truncator.common.storage import read
from truncator.imaging.visual import foreground


class RealForegroundTests(unittest.TestCase):
    def test_boundary_exclusion_keeps_one_sided_ink_but_removes_outline(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "text.png"
            image = Image.new("RGB", (100, 50), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle((90, 20, 99, 30), fill="black")
            image.save(path)
            self.assertEqual(foreground(path, [0, 0, 100, 50], exclude_boundary=True)["bounds_px"], [90, 20, 100, 31])
            draw.rectangle((90, 20, 99, 30), fill="white")
            draw.rectangle((40, 20, 60, 30), fill="black")
            # A continuous rendered outline, rather than diagonally separated
            # one-pixel fragments (the flood fill uses four-neighbour regions).
            draw.ellipse((0, 0, 99, 49), outline="black", width=3)
            image.save(path)
            self.assertEqual(foreground(path, [0, 0, 100, 50], exclude_boundary=True)["bounds_px"], [40, 20, 61, 31])

    def test_plain_text_and_illustration_rejection(self):
        folder = Path(__file__).resolve().parents[2] / "docs/real-foreground"
        for row in read(folder / "results.json")["samples"]:
            with self.subTest(text=row["text"]):
                path = folder / row["image"]
                with Image.open(path) as image:
                    width, height = image.size
                measured = foreground(path, [0, 0, width, height])
                if row["text"] in {"目标进度", "健康生活", "%"}:
                    self.assertEqual(measured["status"], "unsupported_background")
                else:
                    self.assertEqual(measured["status"], "measured")
                    self.assertLessEqual(max(abs(a-b) for a, b in zip(
                        measured["bounds_px"], row["reference_local"])), 4)

    def test_stricter_background_requirement_is_preserved(self):
        folder = Path(__file__).resolve().parents[2] / "docs/real-foreground"
        row = next(r for r in read(folder / "results.json")["samples"] if r["text"] == "亚瑟王")
        with Image.open(folder / row["image"]) as image:
            width, height = image.size
        self.assertEqual(foreground(folder / row["image"], [0, 0, width, height],
                                   minimum_background=0.9)["status"], "unsupported_background")
