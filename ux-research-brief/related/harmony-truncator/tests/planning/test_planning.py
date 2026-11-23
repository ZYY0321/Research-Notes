"""End-to-end planning contract against the installed ArkTS parser."""

import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from truncator.common.storage import read, save, digest
from truncator.source.project import scan
from truncator.mutation.mutations import apply_patches
from truncator.mutation.operators import OPERATORS
from truncator.planning.planning import geometry_plans
from truncator.planning.calibration import automatic_plans, plan_for_target
from truncator.source.binding import bind_candidates, active_records
from truncator.planning.composition import footprint

PROFILE = Path(__file__).resolve().parents[2] / "profiles/apps/ohbill.json"


@unittest.skipUnless(PROFILE.exists(), "Local SDK profile required")
class PlanningTests(unittest.TestCase):
    def test_planning_reuses_one_validated_baseline(self):
        from unittest.mock import patch
        from truncator.planning.baseline import load_baseline
        with tempfile.TemporaryDirectory() as directory:
            _, _, catalog, cap, target, _ = self.fixture(Path(directory))
            for operator, kwargs in (("height-clip", {}), ("scroll-recovery", {}),
                                     ("height-clip", {"ratios": [0.15, 0.25]}),
                                     ("translate-clip", {"penetrations": [3, 5]})):
                with self.subTest(operator=operator, kwargs=kwargs), patch(
                    "truncator.planning.calibration.load_baseline", wraps=load_baseline
                ) as loader, patch("truncator.planning.planning.load_baseline", side_effect=AssertionError(
                    "Geometry reloaded the validated baseline"
                )):
                    self.assertTrue(plan_for_target(catalog, cap, target, operator, **kwargs))
                    self.assertEqual(loader.call_count, 1)


    def test_button_body_remains_a_parent_while_label_button_is_a_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Index.ets").write_text("""@Component struct Index {
              build() { Column() {
                Button({ type: ButtonType.Normal }) { Text('nested') }
                Button('label').id('button')
              } }
            }""", encoding="utf-8")
            catalog = scan({**read(PROFILE), "source": str(root)})
            self.assertEqual(catalog["diagnostics"], [])
            parent = next(s for s in catalog["structural_sites"] if s["component"] == "Button")
            nested = next(s for s in catalog["sites"] if s["component"] == "Text")
            self.assertEqual(nested["parent_id"], parent["id"])
            button = next(s for s in catalog["sites"] if s["component"] == "Button")
            self.assertIn("whitespace-clip", button["operators"])
            self.assertNotIn("line-clip", button["operators"])


    def test_runtime_width_cache_uses_initial_expression_and_preserves_handlers(self):
        from truncator.mutation.viewport_cache import cache_patches
        import copy
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, _ = self.fixture(Path(directory))
            plan = plan_for_target(catalog, cap, target, "cache-viewport-width")[0]
            self.assertEqual([r["role"] for r in plan["related_sites"]], ["viewport"])
            changed = apply_patches(source, plan["patches"])
            self.assertIn("Number(newArea.width)", changed)
            self.assertIn("=== 0", changed)
            self.assertIn(" : (150)", changed)
            self.assertEqual(plan["geometry"]["parameter_basis"], "first_runtime_layout_width")
            for field, value, error in (
                ("repeated", True, "unique"),
                ("owner", {"decorators": ["@ComponentV2"]}, "V1"),
                ("attributes", [{"name": "onAreaChange"}], "preserves"),
            ):
                viewport = copy.deepcopy(plan["related_sites"][0]["site"])
                viewport[field] = value
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, error):
                    cache_patches(viewport)
            with self.assertRaisesRegex(ValueError, "cut schedules"):
                plan_for_target(catalog, cap, target, "cache-viewport-width", penetrations=[8])



    def test_freeze_width_uses_measured_width_without_expansion(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            plan = plan_for_target(catalog, cap, target, "freeze-viewport-width")[0]
            self.assertEqual(plan["parameters"]["viewport_width"], 150)
            self.assertEqual(plan["parameters"]["width_factor"], 1)
            self.assertEqual(plan["geometry"]["penetration_px"], 0)
            self.assertEqual(plan["geometry"]["trigger_condition"], "same-package-in-narrower-window")
            with self.assertRaisesRegex(ValueError, "cut schedules"):
                plan_for_target(catalog, cap, target, "freeze-viewport-width", penetrations=[10])

    def test_viewport_expansion_reserves_existing_container_and_legacy_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            path = Path(profile["source"]) / "Index.ets"
            text = path.read_text(encoding="utf-8").replace("   Scroll() {", "   Column() {\n   Scroll() {")
            text = text.replace(".id('viewport')", ".id('viewport')\n   }.width(150).height(180).id('container')")
            path.write_text(text, encoding="utf-8")
            tree = read(cap / "tree-before.json")
            tree["children"] = [{"attributes": {"type": "Column", "id": "container",
                                "bounds": "[0,0][150,180]", "origBounds": "[0,0][150,180]",
                                "hostWindowId": "1"}, "children": tree["children"]}]
            for filename in ("tree-before.json", "tree-after.json"):
                save(cap / filename, tree)
            catalog = scan(profile)
            target = next(row for row in bind_candidates(catalog, tree)["bindings"]
                          if row["selector"].get("text") == "target")
            plan = plan_for_target(catalog, cap, target, "viewport-width-mismatch", penetrations=[8])[0]
            self.assertTrue(plan["parameters"]["expand_container"])
            self.assertEqual([row["role"] for row in plan["related_sites"]], ["viewport", "viewport_parent"])
            self.assertEqual(footprint(plan, active_records(tree)), [0, 0, 870, 180])
            plan["related_sites"][1].pop("bounds_px")
            self.assertEqual(footprint(plan, active_records(tree)), [0, 0, 870, 180])

    def test_viewport_width_modifies_bound_scroll_and_keeps_target(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            plan = plan_for_target(catalog, cap, target, "viewport-width-mismatch", penetrations=[8])[0]
            self.assertEqual(plan["geometry"]["viewport_selector"], {"id": "viewport", "type": "Scroll"})
            self.assertAlmostEqual(plan["parameters"]["viewport_width"], 870)
            self.assertEqual(plan["related_sites"][0]["role"], "viewport")
            self.assertNotIn(".clip(true)", str(plan["patches"]))
            self.assertNotIn(".width(870", plan["replacement"])
            with self.assertRaisesRegex(ValueError, "right edge"):
                plan_for_target(catalog, cap, target, "viewport-width-mismatch", edge="bottom", penetrations=[8])

    def test_web_source_is_bound_as_a_window_operator_target(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            fixture = Path(__file__).resolve().parents[2] / "research/fixtures/layout-reference/Index.ets"
            (source / "Index.ets").write_bytes(fixture.read_bytes())
            catalog = scan({**read(PROFILE), "source": str(source)})
            web = next(site for site in catalog["sites"] if site["component"] == "Web")
            self.assertEqual(web["operators"], ["window-edge-clip"])
            parent = next(site for site in catalog["structural_sites"] if site["id"] == web["parent_id"])
            self.assertEqual(parent["component"], "Row")

    def test_window_edge_uses_window_coordinates_and_preserves_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            plan = plan_for_target(catalog, cap, target, "window-edge-clip", penetrations=[8])[0]
            self.assertEqual(plan["geometry"]["edge"], "bottom")
            self.assertEqual(plan["geometry"]["window_bounds_px"], [0, 0, 150, 60])
            self.assertEqual(plan["parameters"]["y"], 34)
            self.assertEqual(plan["related_sites"][0]["role"], "window_parent")
            self.assertTrue(plan["parameters"]["move_parent"])
            self.assertIn("translate", str(plan["patches"]))
            self.assertNotIn(".clip(true)", plan["replacement"])
            self.assertNotIn("Row()", plan["replacement"])
            for filename in ("tree-before.json", "tree-after.json"):
                tree = read(cap / filename)
                tree["attributes"]["hostWindowId"] = "2"
                save(cap / filename, tree)
            with self.assertRaisesRegex(ValueError, "same-window root"):
                plan_for_target(catalog, cap, target, "window-edge-clip", penetrations=[8])

    def test_default_width_clip_fixes_text_height_and_child_growth_fixes_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            width = automatic_plans(catalog, cap, target, "width-clip")[0]
            self.assertGreater(width["parameters"]["preserve_height"], 0)
            self.assertIn(".height(", width["replacement"])
            child = automatic_plans(catalog, cap, target, "child-overflow-clip")[0]
            self.assertTrue(child["parameters"]["freeze_parent"])
            self.assertIn(".scale(", child["replacement"])
            self.assertGreater(child["parameters"]["content_scale"], 1)
            self.assertGreater(child["parameters"]["parent_height"], 0)
            explicit = geometry_plans(
                catalog, cap, target, "child-overflow-clip", None, [8], edge="bottom"
            )[0]
            self.assertNotIn("freeze_parent", explicit["parameters"])

    def test_shared_entry_preserves_explicit_and_automatic_plans(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            self.assertEqual(
                plan_for_target(catalog, cap, target, "translate-clip"),
                automatic_plans(catalog, cap, target, "translate-clip"),
            )
            self.assertEqual(
                plan_for_target(
                    catalog, cap, target, "translate-clip", penetrations=[8]
                ),
                geometry_plans(catalog, cap, target, "translate-clip", None, [8]),
            )
            self.assertEqual(
                plan_for_target(catalog, cap, target, "translate-clip", ratios=[0.3]),
                automatic_plans(catalog, cap, target, "translate-clip", ratios=[0.3]),
            )

    def test_shared_entry_rejects_conflicting_parameter_modes(self):
        with self.assertRaisesRegex(ValueError, "only one"):
            plan_for_target(
                {}, ".", {}, "translate-clip", penetrations=[8], ratios=[0.2]
            )
        with self.assertRaisesRegex(ValueError, "only one"):
            plan_for_target(
                {}, ".", {}, "translate-clip", ratios=[0.2], foreground_fraction=0.2
            )

    def test_automatic_budget_does_not_multiply_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            one = automatic_plans(catalog, cap, target, "translate-clip", budget=1)
            many = automatic_plans(catalog, cap, target, "translate-clip", budget=100)
            self.assertEqual(one, many)
            self.assertEqual(len(many), 1)

    def test_automatic_sibling_is_selected_without_a_manual_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            plan = automatic_plans(catalog, cap, target, "sibling-translate-occlusion")[
                0
            ]
            self.assertEqual(
                plan["geometry"]["occluder_binding"]["site"], cover["site"]
            )

    def fixture(self, root):
        source = """@Entry
@Component
struct Index {
  build() {
   Scroll() {
    Row() {
      Text("target").width(100).height(24)
      Text("cover").width(80).height(18).backgroundColor('#FFFFFF')
    }.width(150).height(60)
   }.width(150).height(60).id('viewport')
  }
}
"""
        source = source.replace("\n", "\r\n")
        src = root / "source"
        src.mkdir()
        (src / "Index.ets").write_bytes(source.encode("utf-8"))
        profile = {**read(PROFILE), "source": str(src)}
        catalog = scan(profile)

        def node(kind, text, bounds, children=[]):
            return {
                "attributes": {
                    "type": kind,
                    "text": text,
                    "bounds": bounds,
                    "origBounds": bounds,
                    "backgroundColor": "#FFFFFFFF",
                    "zIndex": "0",
                    "hostWindowId": "1",
                },
                "children": children,
            }

        tree = node(
            "Row",
            "",
            "[0,0][150,60]",
            [
                node("Text", "target", "[10,10][110,34]"),
                node("Text", "cover", "[10,40][90,58]"),
            ],
        )
        tree = node("Scroll", "", "[0,0][150,60]", [tree])
        tree["attributes"]["id"] = "viewport"
        tree = node("root", "", "[0,0][150,60]", [tree])
        cap = root / "capture"
        cap.mkdir()
        Image.new("RGB", (200, 200), "white").save(cap / "snapshot.jpeg")
        save(
            cap / "capture.json",
            {"screenshot_sha256": digest((cap / "snapshot.jpeg").read_bytes())},
        )
        save(cap / "tree-before.json", tree)
        save(cap / "tree-after.json", tree)
        save(cap / "display.json", {"px_per_vp": 1, "source": "fixture"})
        bindings = bind_candidates(catalog, tree)["bindings"]
        target = next(b for b in bindings if b["selector"]["text"] == "target")
        cover = next(b for b in bindings if b["selector"]["text"] == "cover")
        return source, profile, catalog, cap, target, cover

    def test_scroll_control_uses_existing_planning_and_keeps_unknown_outcome(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            plan = plan_for_target(catalog, cap, target, "scroll-recovery")[0]
            self.assertIn("ScrollDirection.Horizontal", plan["replacement"])
            self.assertGreater(plan["parameters"]["child_width"], plan["parameters"]["width"])
            self.assertEqual(plan["construction_intent"], "recoverable_viewport")
            self.assertEqual(plan["outcome"], "unverified")
            self.assertEqual(plan["visual_categories"], [])
            self.assertEqual(plan["review"], "pending")
            explicit = plan_for_target(catalog, cap, target, "scroll-recovery", penetrations=[8])[0]
            self.assertEqual(explicit["geometry"]["edge"], "right")

    def test_every_registered_operator_parses_after_planning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, profile, catalog, cap, target, cover = self.fixture(root)
            for operator in OPERATORS:
                with self.subTest(operator=operator):
                    edge = "right" if operator in {"viewport-width-mismatch", "freeze-viewport-width", "cache-viewport-width"} else "bottom"
                    plans = geometry_plans(
                        catalog,
                        cap,
                        target,
                        operator,
                        None,
                        [8],
                        edge,
                        1,
                        occluder=cover,
                    )
                    plan = plans[0]
                    changed = apply_patches(source, plan["patches"])
                    self.assertIn("truncator_", changed)
                    mutated = root / operator
                    mutated.mkdir()
                    (mutated / "Index.ets").write_text(changed, encoding="utf-8")
                    after = scan({**profile, "source": str(mutated)})
                    self.assertEqual(after["diagnostics"], [])
                    self.assertEqual(
                        plan["id"],
                        geometry_plans(
                            catalog,
                            cap,
                            target,
                            operator,
                            None,
                            [8],
                            edge,
                            1,
                            occluder=cover,
                        )[0]["id"],
                    )

    def test_capture_tamper_and_full_disappearance_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            with self.assertRaises(ValueError):
                geometry_plans(
                    catalog, cap, target, "translate-clip", 1, [24], "top", 1
                )
            (cap / "snapshot.jpeg").write_bytes(b"changed")
            with self.assertRaises(ValueError):
                geometry_plans(catalog, cap, target, "translate-clip", 1, [8], "top", 1)

    def test_baseline_frame_instability_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            tree = read(cap / "tree-after.json")
            tree["children"][0]["children"][0]["children"][0]["attributes"]["bounds"] = "[10,10][110,35]"
            save(cap / "tree-after.json", tree)
            with self.assertRaises(ValueError):
                geometry_plans(catalog, cap, target, "translate-clip", 1, [8], "top", 1)

    def test_automatic_plans_need_no_pixel_ratio_or_density_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            plans = automatic_plans(catalog, cap, target, "fixed-parent-clip")
            self.assertEqual(len(plans), 1)
            self.assertEqual(
                [p["geometry"]["penetration_px"] for p in plans],
                [24 * 0.35],
            )
            self.assertTrue(all(p["geometry"]["edge"] == "bottom" for p in plans))
            self.assertTrue(
                all(p["geometry"]["automatic"]["basis"] == "component" for p in plans)
            )
            self.assertEqual(
                plans, automatic_plans(catalog, cap, target, "fixed-parent-clip")
            )

    def test_automatic_foreground_calibration_and_color(self):
        from PIL import ImageDraw

        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            image = Image.new("RGB", (200, 200), "white")
            ImageDraw.Draw(image).rectangle((40, 18, 69, 25), fill="black")
            image.save(cap / "snapshot.jpeg", quality=100)
            save(
                cap / "capture.json",
                {"screenshot_sha256": digest((cap / "snapshot.jpeg").read_bytes())},
            )
            plan = automatic_plans(catalog, cap, target, "overlay-occlusion", budget=1)[
                0
            ]
            self.assertEqual(plan["geometry"]["automatic"]["basis"], "foreground")
            self.assertEqual(plan["parameters"]["color"], "#FFFFFF")
            self.assertAlmostEqual(plan["geometry"]["penetration_px"], 8 + 8 * 0.2)

    def test_every_operator_supports_automatic_default_edge(self):
        from PIL import ImageDraw

        with tempfile.TemporaryDirectory() as directory:
            source, profile, catalog, cap, target, cover = self.fixture(Path(directory))
            image = Image.new("RGB", (200, 200), "white")
            drawing = ImageDraw.Draw(image)
            drawing.rectangle((20, 12, 39, 15), fill="black")
            drawing.rectangle((20, 24, 39, 27), fill="black")
            image.save(cap / "snapshot.jpeg", quality=100)
            save(
                cap / "capture.json",
                {"screenshot_sha256": digest((cap / "snapshot.jpeg").read_bytes())},
            )
            for operator in OPERATORS:
                with self.subTest(operator=operator):
                    plans = automatic_plans(
                        catalog, cap, target, operator, occluder=cover
                    )
                    self.assertGreater(len(plans), 0)
                    self.assertEqual(len(plans), 1)


if __name__ == "__main__":
    unittest.main()
