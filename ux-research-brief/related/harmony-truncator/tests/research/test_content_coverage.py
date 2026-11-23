import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from truncator.imaging.content_coverage import (
    foreground_coverage,
    uncovered_area,
    visible_regions,
)
from research.controls.evidence import (
    validate_visual_recovery,
    refresh_visual_interactions,
)


class CoverageTests(unittest.TestCase):
    def test_unbound_saved_measurements_cannot_bypass_recomputation(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = {
                "states": [{"state": "scroll", "capture": str(Path(tmp) / "initial")}],
                "interactions": [
                    {
                        "state": "scroll",
                        "capture": str(Path(tmp) / "missing/capture-1"),
                        "measurement": {"same_content": True},
                    }
                ],
            }
            with self.assertRaisesRegex(ValueError, "immutable source plan"):
                refresh_visual_interactions(result)

    def test_complete_geometry_does_not_establish_recovery_when_text_changed(self):
        result = {
            "interactions": [
                {
                    "state": "scroll",
                    "stage": "forward",
                    "measurement": {
                        "same_extent": True,
                        "same_content": False,
                        "foreground_coverage": {"status": "covered"},
                    },
                }
            ]
        }
        with self.assertRaises(ValueError):
            validate_visual_recovery(result, {"scroll"})

    def test_both_axis_projections_can_be_full_while_corner_content_is_missing(self):
        boxes = [[0, 0, 60, 60], [40, 40, 100, 100]]
        self.assertEqual(uncovered_area([0, 0, 100, 100], boxes), 3200)
        self.assertEqual(
            uncovered_area([0, 0, 100, 100], [[0, 0, 60, 100], [40, 0, 100, 100]]), 0
        )

    def test_horizontal_recovery_does_not_hide_persistent_vertical_clipping(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "baseline.png"
            image = Image.new("RGB", (100, 100), "white")
            ImageDraw.Draw(image).rectangle((10, 20, 90, 90), outline="black", width=2)
            image.save(p)
            result = foreground_coverage(
                p, [0, 0, 100, 100], [[0, 0, 60, 70], [40, 0, 100, 70]]
            )
            self.assertEqual(result["status"], "incomplete")
            self.assertGreater(result["uncovered_pixels"], 0)
            action = {
                "state": "scroll",
                "stage": "forward",
                "measurement": {"same_extent": True, "foreground_coverage": result},
            }
            with self.assertRaisesRegex(ValueError, "two-dimensional"):
                validate_visual_recovery({"interactions": [action]}, {"scroll"})

    def test_uncovered_whitespace_is_not_missing_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "baseline.png"
            image = Image.new("RGB", (100, 100), "white")
            ImageDraw.Draw(image).rectangle((10, 20, 90, 60), outline="black", width=2)
            image.save(p)
            result = foreground_coverage(
                p, [0, 0, 100, 100], [[0, 0, 60, 70], [40, 0, 100, 70]]
            )
            self.assertEqual(result["status"], "covered")
            self.assertGreater(uncovered_area([0, 0, 100, 100], [[0, 0, 100, 70]]), 0)

    def test_diagonal_frames_leave_actual_glyph_pixels_unseen(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "baseline.png"
            image = Image.new("RGB", (100, 100), "white")
            ImageDraw.Draw(image).rectangle((75, 10, 85, 20), fill="black")
            image.save(p)
            result = foreground_coverage(
                p, [0, 0, 100, 100], [[0, 0, 60, 60], [40, 40, 100, 100]]
            )
            self.assertEqual(result["uncovered_pixels"], 121)

    def test_screen_and_viewport_boundaries_limit_available_pixels(self):
        row = {
            "original": [-10, -20, 90, 80],
            "visible": [-10, -20, 90, 80],
            "viewport": [0, 0, 100, 100],
            "screen_size": [50, 50],
        }
        self.assertEqual(visible_regions([row]), [[10, 20, 60, 70]])

    def test_blank_reference_does_not_prove_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "baseline.png"
            Image.new("RGB", (50, 50), "white").save(p)
            self.assertEqual(
                foreground_coverage(p, [0, 0, 50, 50], [[0, 0, 50, 50]])["status"],
                "unknown",
            )


if __name__ == "__main__":
    unittest.main()
