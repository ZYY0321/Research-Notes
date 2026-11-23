import tempfile
import unittest
import shutil
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageDraw
from truncator.common.storage import read
from truncator.mutation.operators import mutate
from truncator.imaging.visual import (
    foreground,
    content_penetration,
    changed_fraction,
    severity_policy,
)
from truncator.execution.device.acquisition import acquire
from truncator.review.diagnostics import select_candidate
from truncator.review.diagnostics import diagnose
from truncator.common.storage import save


class RegressionTests(unittest.TestCase):
    def test_small_foreground_loss_is_not_diluted_by_large_component_background(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(
                root / "geometry-observation.json",
                {
                    "status": "measured",
                    "target": {"type": "Text", "bounds": "[0,0][1000,100]"},
                    "baseline_target_roi_mean_absolute_pixel_difference": 0.5,
                },
            )
            plan = {
                "operator": "overlay-occlusion",
                "parameters": {"color": "#FFFFFF"},
                "geometry": {
                    "baseline_capture": str(root),
                    "target_bounds_px": [0, 0, 1000, 100],
                },
            }
            with patch(
                "truncator.review.diagnostics.foreground",
                side_effect=[
                    {
                        "status": "measured",
                        "background_rgb": [255] * 3,
                        "foreground_pixels": 100,
                    },
                    {
                        "status": "measured",
                        "background_rgb": [255] * 3,
                        "foreground_pixels": 80,
                    },
                ],
            ):
                result = diagnose(plan, root)
            self.assertEqual(result["severity"], "partial")
            self.assertNotIn("target_roi_almost_unchanged", result["flags"])

    def test_all_saved_source_replacements_are_unchanged(self):
        fixtures = read(Path(__file__).parent.parent / "fixtures/operator-regressions.json")
        self.assertEqual(len(fixtures), 18)
        for fixture in fixtures:
            with self.subTest(
                operator=fixture["operator"], run=fixture["historical_run"]
            ):
                self.assertTrue(fixture["historical_replacement_equal"])
                self.assertEqual(
                    mutate(fixture["site"], fixture["operator"], fixture["parameters"]),
                    fixture["expected_replacement"],
                )

    def test_foreground_and_ratio_exclude_padding(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Image.new("RGB", (200, 100), "white")
            ImageDraw.Draw(image).rectangle((80, 40, 119, 59), fill="black")
            path = Path(directory) / "normal.png"
            image.save(path)
            measured = foreground(path, [0, 0, 200, 100])
            self.assertEqual(measured["bounds_px"], [80, 40, 120, 60])
            self.assertEqual(
                content_penetration(
                    [0, 0, 200, 100], measured["bounds_px"], "bottom", 0.25
                ),
                45,
            )
            self.assertEqual(
                content_penetration(
                    [0, 0, 400, 200], [160, 80, 240, 120], "bottom", 0.25
                ),
                90,
            )

    def test_complex_background_requires_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Image.new("RGB", (100, 100))
            image.putdata(
                [(x * 2, y * 2, (x + y) % 256) for y in range(100) for x in range(100)]
            )
            path = Path(directory) / "complex.png"
            image.save(path)
            self.assertEqual(
                foreground(path, [0, 0, 100, 100])["status"], "unsupported_background"
            )

    def test_complete_loss_is_configurable(self):
        self.assertTrue(severity_policy("complete")["eligible"])
        self.assertFalse(severity_policy("complete", ["partial"])["eligible"])

    def test_quality_excludes_intended_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = Image.new("RGB", (100, 100), "white")
            image.save(root / "a.png")
            ImageDraw.Draw(image).rectangle((10, 10, 19, 19), fill="black")
            image.save(root / "b.png")
            self.assertEqual(
                changed_fraction(root / "a.png", root / "b.png", [[10, 10, 20, 20]])[
                    "changed_fraction"
                ],
                0,
            )
            self.assertGreater(
                changed_fraction(root / "a.png", root / "b.png")["changed_fraction"], 0
            )

    def test_capture_retries_and_preserves_bad_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (50, 50), "white").save(root / "baseline.png")
            Image.new("RGB", (50, 50), "black").save(root / "bad.png")
            received = []

            def hdc(*args):
                if args[:2] == ("file", "recv"):
                    shutil.copy2(
                        root / ("bad.png" if not received else "baseline.png"),
                        args[3],
                    )
                    received.append(args[3])

            acquire(
                root / "attempt",
                hdc,
                lambda: {"attributes": {}},
                {
                    "baseline_image": str(root / "baseline.png"),
                    "attempts": 2,
                    "delay_seconds": 0,
                    "max_changed_fraction": 0.01,
                },
            )
            self.assertEqual(len(received), 2)
            self.assertTrue((root / "attempt/frames/0/snapshot.png").exists())
            self.assertTrue(read(root / "attempt/image-quality.json")["passed"])

    def test_capture_failure_never_writes_success_image(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (50, 50), "white").save(root / "baseline.png")
            Image.new("RGB", (50, 50), "black").save(root / "bad.png")

            def hdc(*args):
                if args[:2] == ("file", "recv"):
                    shutil.copy2(root / "bad.png", args[3])

            with self.assertRaises(RuntimeError):
                acquire(
                    root / "attempt",
                    hdc,
                    lambda: {},
                    {
                        "baseline_image": str(root / "baseline.png"),
                        "attempts": 2,
                        "delay_seconds": 0,
                        "enforcement": "strict",
                    },
                )
            self.assertFalse((root / "attempt/snapshot.png").exists())

    def test_quality_difference_is_advisory_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (20, 20), "white").save(root / "baseline.png")
            Image.new("RGB", (20, 20), "black").save(root / "changed.png")

            def hdc(*args):
                if args[:2] == ("file", "recv"):
                    shutil.copy2(root / "changed.png", args[3])

            acquire(
                root / "attempt",
                hdc,
                lambda: {},
                {
                    "baseline_image": str(root / "baseline.png"),
                },
            )
            self.assertTrue((root / "attempt/snapshot.png").exists())
            quality = read(root / "attempt/image-quality.json")
            self.assertFalse(quality["passed"])
            self.assertTrue(quality["review_required"])

    def test_corrupt_image_is_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (20, 20), "white").save(root / "baseline.png")
            received = []

            def hdc(*args):
                if args[:2] == ("file", "recv"):
                    if not received:
                        Path(args[3]).write_bytes(b"broken jpeg")
                    else:
                        shutil.copy2(root / "baseline.png", args[3])
                    received.append(args[3])

            acquire(
                root / "attempt",
                hdc,
                lambda: {},
                {
                    "baseline_image": str(root / "baseline.png"),
                    "attempts": 2,
                    "delay_seconds": 0,
                },
            )
            quality = read(root / "attempt/image-quality.json")
            self.assertTrue(quality["passed"])
            self.assertEqual(
                quality["checks"][0]["measurement"]["status"], "decode_failed"
            )

    def test_candidate_preference_and_quality_review(self):
        report = []
        for severity in ["complete", "unresolved", "partial"]:
            report.append(
                {
                    "status": "captured",
                    "run": severity,
                    "assessment": {
                        "capture": severity,
                        "next_action": "review_candidate",
                        "diagnostics": {"severity": severity},
                    },
                }
            )
        self.assertEqual(select_candidate(report)["selected"]["severity"], "partial")
        report[-1]["assessment"]["next_action"] = "inspect_non_target_changes"
        self.assertEqual(select_candidate(report)["selected"]["severity"], "complete")


if __name__ == "__main__":
    unittest.main()
