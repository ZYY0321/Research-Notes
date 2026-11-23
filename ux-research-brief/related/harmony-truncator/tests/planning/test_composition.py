import copy
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from unittest.mock import patch

from truncator.source.binding import literal, active_records
from truncator.planning.composition import (
    capture_members,
    combined_edits,
    compose,
    select_combination,
    validate_plan,
    navigation_region,
    footprint,
    source_conflict,
)
from truncator.mutation.mutations import apply_patches, plans
from truncator.common.storage import digest, save
from truncator.execution.device.replay import action_arguments, matches_selector
from truncator.source.project import prepare
from truncator.review.datasets.dataset import export_dataset
from truncator.common.storage import read


class CompositionTests(unittest.TestCase):
    def test_state_insertion_collisions_are_rejected_before_composition(self):
        with tempfile.TemporaryDirectory() as directory:
            _, candidates, _ = self.fixture(Path(directory))
            a, b = copy.deepcopy(candidates[0]), copy.deepcopy(candidates[3])
            self.assertFalse(source_conflict(a, b))
            a["patches"] = [{"file": "Index.ets", "start": 0, "end": 0}]
            b["patches"] = [{"file": "Index.ets", "start": 0, "end": 0}]
            self.assertTrue(source_conflict(a, b))
            b["patches"][0].update(start=30, end=30)
            self.assertFalse(source_conflict(a, b))

    def test_component_diversity_is_balanced_after_safety_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            _, candidates, pages = self.fixture(Path(directory))
            # Selection uses component strata; source mutation validity is tested separately.
            for plan in candidates:
                plan["site"]["component"] = "SymbolGlyph" if plan["site"]["id"] == "third" else "Text"
            for seed in range(12):
                selected, report = select_combination(candidates, pages, max_total=2, seed=seed)
                self.assertEqual(report["components"], {"Text": 1, "SymbolGlyph": 1})
            pages[0]["recipe"] = {"actions": [{"equals": "third"}]}
            selected, report = select_combination(candidates, pages, max_total=2)
            self.assertNotIn("SymbolGlyph", report["components"])

    def test_focused_dialog_excludes_background_nodes(self):
        tree = {
            "children": [
                {"attributes": {"type": "Text", "id": "background"}},
                {
                    "attributes": {
                        "type": "Dialog",
                        "visible": "true",
                        "focused": "true",
                    },
                    "children": [{"attributes": {"type": "Text", "id": "modal"}}],
                },
            ]
        }
        self.assertEqual(
            [r["attributes"].get("id") for r in active_records(tree)], [None, "modal"]
        )

    def test_swipe_protects_gesture_corridor_and_composite_selector_matches(self):
        action = {"kind": "swipe", "selector": {"type": "Scroll", "id": "list"}}
        self.assertTrue(matches_selector({"type": "Scroll", "id": "list"}, action))
        self.assertFalse(matches_selector({"type": "Scroll", "id": "other"}, action))
        region = navigation_region(
            action, {"attributes": {"bounds": "[0,0][1000,1000]"}}
        )
        self.assertEqual(region, [490, 190, 510, 810])

    def test_sibling_footprint_includes_moved_occluder_outside_parent(self):
        target = {
            "attributes": {"id": "target", "bounds": "[0,0][50,50]"},
            "ancestors": [{"attributes": {"bounds": "[0,0][100,100]"}}],
        }
        cover = {
            "attributes": {"id": "cover", "bounds": "[60,0][100,50]"},
            "ancestors": [],
        }
        plan = {
            "operator": "sibling-translate-occlusion",
            "parameters": {"x": 100, "y": 0},
            "geometry": {
                "selector": {"id": "target"},
                "occluder_binding": {"selector": {"id": "cover"}},
                "px_per_vp": 1,
            },
            "related_sites": [{"role": "occluder", "site": {"attributes": []}}],
        }
        self.assertEqual(footprint(plan, [target, cover]), [0, 0, 200, 100])

    def test_combined_export_retains_all_page_mutations_and_paired_baselines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline"
            baseline.mkdir()
            _, candidates, pages = self.fixture(baseline)
            selected = [candidates[0], candidates[4]]
            for member in selected:
                member["geometry"].update(
                    baseline_capture=str(baseline),
                    baseline_image_sha256=digest(
                        (baseline / "snapshot.jpeg").read_bytes()
                    ),
                    baseline_tree_sha256=digest(
                        (baseline / "tree-before.json").read_bytes()
                    ),
                )
            combined = compose(selected, pages, {})
            run = root / "runs/multi"
            cap = run / "capture-1"
            cap.mkdir(parents=True)
            for name in ("snapshot.jpeg", "tree-before.json"):
                (cap / name).write_bytes((baseline / name).read_bytes())
            save(cap / "tree-after.json", {})
            save(cap / "capture.json", {"recipe": {}, "screenshot_sha256": digest((cap / "snapshot.jpeg").read_bytes())})
            from truncator.review.review_evidence import capture_hashes
            save(
                cap / "review-1.json",
                {
                    "decision": "accepted",
                    "reviewer": "test fixture",
                    "capture_files": capture_hashes(cap),
                    "screenshot_sha256": digest((cap / "snapshot.jpeg").read_bytes()),
                },
            )
            save(run / "plan.json", combined)
            save(run / "profile.json", {"bundle": "fixture"})
            self.assertEqual(export_dataset(root / "runs", root / "export"), 1)
            sample = read(root / "export/manifest.json")["samples"][0]
            self.assertEqual(len(sample["mutations"]), 2)
            self.assertEqual(sample["split_group"], "fixture/combined")
            self.assertEqual(
                len(list((root / "export" / sample["id"] / "baselines").iterdir())), 2
            )

    def test_preparation_applies_combined_plan_and_preserves_original_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = root / "source"
            source_root.mkdir()
            source, candidates, pages = self.fixture(source_root)
            (source_root / "Index.ets").write_bytes(source.encode("utf-8"))
            combined = compose([candidates[0], candidates[4]], pages, {})
            with patch(
                "truncator.source.project.scan", return_value={"files": {}, "diagnostics": []}
            ):
                prepare({"source": str(source_root)}, root / "run", combined)
            actual = (root / "run/project/Index.ets").read_text(encoding="utf-8")
            self.assertEqual(actual, apply_patches(source, combined["patches"]))
            self.assertEqual(
                (source_root / "Index.ets").read_text(encoding="utf-8"), source
            )

    def fixture(self, root):
        Image.new("RGB", (1000, 1000), "white").save(root / "snapshot.jpeg")
        source = "Text('first')\nText('second')\nText('third')"
        sites = []
        children = []
        for index, text in enumerate(("first", "second", "third")):
            snippet = f"Text('{text}')"
            start = source.index(snippet)
            sites.append(
                {
                    "id": text,
                    "file": "Index.ets",
                    "component": "Text",
                    "start": start,
                    "end": start + len(snippet),
                    "snippet": snippet,
                    "sha256": digest(snippet),
                    "attributes": [],
                    "repeated": False,
                    "operators": ["height-clip", "width-clip", "line-clip"],
                }
            )
            top = 100 + index * 150
            children.append(
                {
                    "attributes": {"bounds": f"[50,{top}][250,{top+80}]"},
                    "children": [
                        {
                            "attributes": {
                                "text": text,
                                "type": "Text",
                                "bounds": f"[60,{top+10}][240,{top+60}]",
                            }
                        }
                    ],
                }
            )
        save(
            root / "tree-before.json",
            {"attributes": {"bounds": "[0,0][1000,1000]"}, "children": children},
        )
        catalog = {
            "root": str(root),
            "sites": sites,
            "files": {"Index.ets": digest(source)},
        }
        candidates = []
        for index, site in enumerate(sites):
            for operator in site["operators"]:
                p = plans(
                    catalog,
                    0,
                    1,
                    operator,
                    {"height": 20, "width": 80},
                    site_id=site["id"],
                )[0]
                p["geometry"] = {
                    "selector": {"text": site["id"], "type": "Text"},
                    "target_bounds_px": [60, 110 + index * 150, 240, 160 + index * 150],
                }
                candidates.append(p)
        pages = [{"name": "page", "recipe": {}, "baseline_capture": str(root)}]
        return source, candidates, pages

    def test_one_package_applies_multiple_distinct_patches(self):
        with tempfile.TemporaryDirectory() as directory:
            source, candidates, pages = self.fixture(Path(directory))
            chosen = [candidates[0], candidates[4]]
            combined = compose(chosen, pages, {})
            validate_plan(combined)
            updated = apply_patches(source, combined["patches"])
            self.assertIn("Text('first').height(20).clip(true)", updated)
            self.assertIn("Text('second').width(80).clip(true)", updated)
            self.assertIn("Text('third')", updated)
            self.assertEqual(len(capture_members(combined, {})), 2)
            self.assertEqual(capture_members(combined, {"different_page": True}), [])
            changed = copy.deepcopy(combined)
            changed["mutations"][0]["parameters"]["height"] = 99
            with self.assertRaisesRegex(ValueError, "checksum"):
                validate_plan(changed)

    def test_combination_rejects_duplicate_targets_and_overlapping_patches(self):
        with tempfile.TemporaryDirectory() as directory:
            _, candidates, _ = self.fixture(Path(directory))
            with self.assertRaisesRegex(ValueError, "same source"):
                combined_edits(candidates[:2])
            other = copy.deepcopy(candidates[3])
            other["site"]["start"] = candidates[0]["site"]["start"]
            with self.assertRaisesRegex(ValueError, "overlap"):
                combined_edits([candidates[0], other])

    def test_seeded_selection_has_one_method_per_target_and_enforces_page_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            _, candidates, pages = self.fixture(Path(directory))
            first, metadata = select_combination(
                candidates, pages, max_per_page=2, seed=10
            )
            second, _ = select_combination(
                list(reversed(candidates)), pages, max_per_page=2, seed=10
            )
            self.assertEqual(len(first), 2)
            self.assertEqual(len({p["site"]["id"] for p in first}), 2)
            self.assertEqual([p["id"] for p in first], [p["id"] for p in second])
            self.assertEqual(len(metadata["influence_regions"]["page"]), 2)

    def test_navigation_and_area_limits_are_applied_before_diversity(self):
        with tempfile.TemporaryDirectory() as directory:
            _, candidates, pages = self.fixture(Path(directory))
            pages[0]["recipe"] = {"actions": [{"equals": "first"}]}
            chosen, _ = select_combination(candidates, pages)
            self.assertNotIn("first", [p["site"]["id"] for p in chosen])
            chosen, _ = select_combination(candidates, pages, max_area_ratio=0.001)
            self.assertEqual(chosen, [])

    def test_shared_component_counts_against_each_visible_page(self):
        with tempfile.TemporaryDirectory() as directory:
            _, candidates, pages = self.fixture(Path(directory))
            pages.append({**pages[0], "name": "second-page"})
            chosen, metadata = select_combination(candidates, pages, max_per_page=1)
            self.assertEqual(len(chosen), 1)
            self.assertEqual(len(metadata["influence_regions"]["second-page"]), 1)

    def test_other_route_navigation_is_protected_on_this_page(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, candidates, pages = self.fixture(root)
            destination = root / "destination"
            destination.mkdir()
            Image.new("RGB", (1000, 1000)).save(destination / "snapshot.jpeg")
            save(
                destination / "tree-before.json",
                {"attributes": {"bounds": "[0,0][1000,1000]"}},
            )
            pages.append(
                {
                    "name": "destination",
                    "recipe": {"actions": [{"equals": "first"}]},
                    "baseline_capture": str(destination),
                }
            )
            chosen, metadata = select_combination(candidates, pages)
            self.assertTrue(chosen)
            self.assertNotIn("first", [p["site"]["id"] for p in chosen])
            self.assertEqual(
                metadata["protected_navigation_regions"]["page"], [[60, 110, 240, 160]]
            )
            self.assertIn(
                "navigation_action_region", [r["reason"] for r in metadata["rejected"]]
            )

    def test_click_uses_moved_current_bounds(self):
        action = {"field": "id", "equals": "product"}
        self.assertEqual(
            action_arguments(action, "[10,20][110,100]"), ["click", "60", "60"]
        )
        self.assertEqual(
            action_arguments(action, "[40,80][140,160]"), ["click", "90", "120"]
        )

    def test_source_string_escapes_are_decoded_without_evaluating_expressions(self):
        self.assertEqual(literal("'服务不可用\\n请检查设置'"), "服务不可用\n请检查设置")
        self.assertIsNone(literal("'a' + 'b'"))
        self.assertIsNone(literal("call()"))

    def test_swipe_is_relative_to_the_current_component(self):
        self.assertEqual(
            action_arguments({"kind": "swipe"}, "[100,200][500,1200]"),
            ["swipe", "300", "1000", "300", "400", "600"],
        )
        with self.assertRaises(ValueError):
            action_arguments({"kind": "swipe", "to": [1.5, 0.2]}, "[0,0][100,100]")


if __name__ == "__main__":
    unittest.main()
