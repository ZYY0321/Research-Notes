import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from PIL import Image, ImageDraw
from truncator.planning.parameter_policy import choose_parameters


class ParameterPolicyTests(unittest.TestCase):
    def test_registered_selection_extends_policy_without_name_switches(self):
        from dataclasses import replace
        from unittest.mock import patch
        from truncator.mutation.operator_strategies import STRATEGIES
        from truncator.imaging.visual import baseline_foreground

        def select(context, choice):
            self.assertTrue(context.measured)
            choice.cuts = [-10, 300, 11]
            choice.rule = "extension-probe"

        with tempfile.TemporaryDirectory() as directory:
            baseline = self.baseline(Path(directory), ink=[(20, 30, 79, 69)])
            original = choose_parameters(baseline, "fixed-parent-clip", "right")
            strategy = replace(STRATEGIES["fixed-parent-clip"], select=select)
            with patch.dict(STRATEGIES, {"extension-probe": strategy}), patch(
                "truncator.planning.parameter_policy.baseline_foreground", wraps=baseline_foreground
            ) as measure:
                choice = choose_parameters(baseline, "extension-probe", "right")
            self.assertEqual(measure.call_count, 1)
            self.assertEqual(choice["cut_px"], 11)
            self.assertEqual(choice["metadata"]["cut_interval_px"], [1, 199])
            self.assertEqual(choice["metadata"]["rule"], "extension-probe")
            self.assertEqual(choose_parameters(baseline, "fixed-parent-clip", "right"), original)

    def test_self_height_preserves_bottom_padding_but_parent_boundary_does_not(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self.baseline(Path(directory), width=200, height=100, ink=[(20, 30, 79, 69)], density=2)
            baseline.site["padding"] = {"status": "resolved", "value": {"bottom": "10%"}}
            own = choose_parameters(baseline, "height-clip", "bottom")
            parent = choose_parameters(baseline, "fixed-parent-clip", "bottom")
            self.assertAlmostEqual(own["cut_px"], 18)
            self.assertAlmostEqual(parent["cut_px"], 38)
            self.assertEqual(own["metadata"]["text_padding"]["pixels"]["bottom"], 20)

    def test_unresolved_padding_cannot_be_treated_as_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self.baseline(Path(directory), ink=[(20, 30, 79, 69)])
            baseline.site["padding"] = {"status": "unresolved", "reason": "dynamic value"}
            with self.assertRaisesRegex(ValueError, "resolved padding"):
                choose_parameters(baseline, "height-clip", "bottom")

    def test_nontext_whitespace_uses_visible_content_and_rejects_full_bleed(self):
        with tempfile.TemporaryDirectory() as directory:
            for component in ("SymbolGlyph", "Image", "Button"):
                with self.subTest(component=component):
                    baseline = self.baseline(Path(directory), component=component, ink=[(20, 20, 119, 59)])
                    choice = choose_parameters(baseline, "whitespace-clip", "right")
                    self.assertEqual(choice["cut_px"], 40)
                    self.assertEqual(choice["metadata"]["visible_text_bands_px"], [])
                    baseline = self.baseline(Path(directory), component=component, ink=[(20, 20, 199, 59)])
                    with self.assertRaises(ValueError):
                        choose_parameters(baseline, "whitespace-clip", "right")

    def test_whitespace_control_cuts_only_trailing_margin(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self.baseline(Path(directory), ink=[(20, 20, 119, 59)])
            choice = choose_parameters(baseline, "whitespace-clip", "right")
            self.assertEqual(choice["cut_px"], 40)
            self.assertEqual(choice["metadata"]["rule"], "trailing-whitespace-only")
            self.assertLess(choice["cut_px"], 200 - 120)
            with self.assertRaises(ValueError):
                choose_parameters(baseline, "whitespace-clip", "left")

    def test_whitespace_control_has_no_component_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self.baseline(Path(directory))
            with self.assertRaisesRegex(ValueError, "measurable"):
                choose_parameters(baseline, "whitespace-clip", "right")

    def test_rounded_text_background_excludes_page_colored_corners(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = self.baseline(root, width=120, height=50)
            baseline.site["attributes"] = [
                {"name": "backgroundColor", "text": "Color.Gray"},
                {"name": "borderRadius", "text": "25"},
            ]
            image = Image.new("RGB", (120, 50), "white")
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle((0, 0, 119, 49), radius=25, fill=(153, 153, 153))
            draw.rectangle((40, 15, 79, 34), fill="white")
            image.save(root / "snapshot.jpeg", quality=100, subsampling=0)
            choice = choose_parameters(baseline, "line-clip", "right")
            self.assertAlmostEqual(120 - choice["cut_px"], 40 * 0.65)
            measurement = choice["metadata"]["foreground_measurement"]
            self.assertEqual(measurement["bounds_px"], [40, 15, 80, 35])
            self.assertGreater(measurement["boundary_pixels_removed"], 0)
            self.assertEqual(choice["metadata"]["visible_text_bands_px"], [[15, 35]])

    def test_complex_image_overlay_samples_adjacent_background(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = self.baseline(root, component="Image")
            baseline.bounds = [50, 30, 150, 80]
            image = Image.new("RGB", (200, 100), (220, 30, 50))
            drawing = ImageDraw.Draw(image)
            drawing.rectangle((50, 30, 99, 79), fill="blue")
            drawing.rectangle((100, 30, 149, 79), fill="yellow")
            image.save(root / "snapshot.jpeg", quality=100, subsampling=0)
            choice = choose_parameters(baseline, "overlay-occlusion", "top")
            self.assertEqual(choice["metadata"]["overlay_color_source"], "baseline_adjacent_strip")
            rgb = tuple(int(choice["color"][i : i + 2], 16) for i in (1, 3, 5))
            self.assertTrue(all(abs(a - b) < 4 for a, b in zip(rgb, (220, 30, 50))))

            drawing.rectangle((50, 25, 99, 29), fill="blue")
            drawing.rectangle((100, 25, 149, 29), fill="yellow")
            image.save(root / "snapshot.jpeg", quality=100, subsampling=0)
            with self.assertRaisesRegex(ValueError, "locally uniform"):
                choose_parameters(baseline, "overlay-occlusion", "top")

    def test_complex_overlay_without_local_color_requires_explicit_color(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = self.baseline(root, component="Image")
            image = Image.new("RGB", (200, 100), "blue")
            ImageDraw.Draw(image).rectangle((100, 0, 199, 99), fill="yellow")
            image.save(root / "snapshot.jpeg", quality=100, subsampling=0)
            with self.assertRaisesRegex(ValueError, "beside the overlay"):
                choose_parameters(baseline, "overlay-occlusion", "top")
            choice = choose_parameters(baseline, "overlay-occlusion", "top", color="#FF0000")
            self.assertEqual(choice["color"], "#FF0000")
            self.assertEqual(choice["metadata"]["overlay_color_source"], "explicit")

    def test_flat_icon_overlay_uses_icon_background(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = self.baseline(root, component="Image")
            image = Image.new("RGB", (200, 100), (220, 30, 50))
            ImageDraw.Draw(image).rectangle((80, 30, 120, 70), fill="white")
            image.save(root / "snapshot.jpeg", quality=100, subsampling=0)
            choice = choose_parameters(baseline, "overlay-occlusion", "top")
            self.assertEqual(choice["metadata"]["rule"], "flat-image-foreground")
            rgb = tuple(int(choice["color"][i : i + 2], 16) for i in (1, 3, 5))
            self.assertTrue(all(abs(a - b) < 4 for a, b in zip(rgb, (220, 30, 50))))
            self.assertEqual(choice["metadata"]["visible_text_bands_px"], [])

    def baseline(
        self, root, width=200, height=100, ink=(), component="Text", density=1
    ):
        image = Image.new("RGB", (width, height), "white")
        drawing = ImageDraw.Draw(image)
        for box in ink:
            drawing.rectangle(box, fill="black")
        image.save(root / "snapshot.jpeg", quality=100, subsampling=0)
        return SimpleNamespace(
            capture_dir=root,
            bounds=[0, 0, width, height],
            density=density,
            site={"component": component, "attributes": []},
            records=[],
        )

    def test_padding_and_ink_determine_range_and_one_value(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self.baseline(Path(directory), ink=[(80, 40, 119, 59)])
            choice = choose_parameters(baseline, "fixed-parent-clip", "bottom")
            self.assertAlmostEqual(choice["cut_px"], 44)
            self.assertEqual(choice["metadata"]["cut_interval_px"], [43, 46])
            self.assertEqual(choice["metadata"]["evidence_source"], "baseline-only")

    def test_width_uses_ink_instead_of_large_centered_container(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self.baseline(
                Path(directory), width=1000, ink=[(400, 40, 599, 59)]
            )
            baseline.site["attributes"] = [{"name": "padding", "text": "10"}]
            choice = choose_parameters(baseline, "line-clip", "right")
            self.assertAlmostEqual(1000 - choice["cut_px"], 150)

    def test_line_limit_depends_on_baseline_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self.baseline(
                Path(directory),
                height=140,
                ink=[(10, y, 70, y + 10) for y in (10, 40, 70, 100)],
            )
            choice = choose_parameters(baseline, "ellipsis-lines", "bottom")
            self.assertEqual(choice["line_limit"], 3)
            self.assertEqual(choice["metadata"]["max_lines_interval"], [1, 3])
            self.assertEqual(len(choice["metadata"]["visible_text_bands_px"]), 4)

    def test_single_row_does_not_receive_an_ineffective_line_only_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self.baseline(Path(directory), ink=[(80, 40, 119, 59)])
            with self.assertRaisesRegex(ValueError, "two measurable"):
                choose_parameters(baseline, "ellipsis-lines", "bottom")

    def test_one_pixel_edge_is_not_a_second_text_line(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self.baseline(
                Path(directory), ink=[(30, 30, 150, 60), (0, 99, 199, 99)], density=2.875
            )
            with self.assertRaisesRegex(ValueError, "two measurable"):
                choose_parameters(baseline, "ellipsis-lines", "bottom")

    def test_image_fallback_scales_with_component(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            small = choose_parameters(
                self.baseline(root, component="Image"), "translate-clip", "left"
            )
            large = choose_parameters(
                self.baseline(
                    root, width=400, height=200, component="Image", density=2
                ),
                "translate-clip",
                "left",
            )
            self.assertEqual(large["cut_px"], small["cut_px"] * 2)

    def test_vertical_clipping_only_targets_the_edge_row(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = self.baseline(
                Path(directory),
                height=140,
                ink=[(10, y, 70, y + 9) for y in (10, 40, 70, 100)],
            )
            choice = choose_parameters(baseline, "fixed-parent-clip", "bottom")
            self.assertAlmostEqual(choice["cut_px"], 32)


if __name__ == "__main__":
    unittest.main()
