import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from research.production_evidence.comparison import inspect_target, compare_targets


class BoundaryComparisonTests(unittest.TestCase):
    def inspect(self, root, name, *, outer_scroll=False, outer_clip=False,
                native=False, window="0", unknown=False, loss=True, parent_type="Row", outer_type="Column"):
        def boolean(value):
            return value if native else str(value).lower()
        def attrs(kind, box, **extra):
            return {"type": kind, "bounds": box, "origBounds": box,
                    "hostWindowId": window, "clip": boolean(False),
                    "scrollable": boolean(False), **extra}
        outer = attrs(outer_type, "[0,0][80,100]", clip=boolean(outer_clip),
                      scrollable=boolean(outer_scroll))
        if unknown:
            outer.pop("scrollable")
        target = attrs("Text", "[10,10][80,30]", text="target",
                       origBounds="[10,10][100,30]" if loss else "[10,10][80,30]")
        tree = {"attributes": outer, "children": [{
            "attributes": attrs(parent_type, "[0,0][80,100]", clip=boolean(True)),
            "children": [{"attributes": target}]}]}
        filename = root / (name + ".json")
        filename.write_text(json.dumps(tree), encoding="utf-8")
        image = root / "screen.png"
        Image.new("RGB", (200, 200)).save(image)
        return inspect_target(filename, image, {"text": "target"})

    def test_outer_scroll_difference_cannot_hide_behind_matching_nearest_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = self.inspect(root, "fixed")
            right = self.inspect(root, "outer-scroll", outer_scroll=True)
            comparison = compare_targets(left, right)
            self.assertEqual(comparison["local_assessment"]["status"], "structural_candidate")
            critical = comparison["boundary_comparison"]
            self.assertEqual(critical["status"], "different")
            self.assertIn("scroll_context", critical["different_fields"])
            self.assertEqual(len(critical["injected"]["scroll_ancestor_witnesses"]), 1)

    def test_all_aligned_boundaries_are_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = self.inspect(root, "fixed")
            right = self.inspect(root, "scroll", outer_scroll=True, outer_clip=True)
            critical = compare_targets(left, right)["boundary_comparison"]
            self.assertIn("aligned_boundary_modes", critical["different_fields"])
            self.assertEqual(critical["features"]["aligned_boundary_modes"]["injected"],
                             {"right": ["fixed", "scrollable"]})
            self.assertEqual(len(critical["injected"]["aligned_boundary_witnesses"]["right"]), 2)

    def test_paging_and_continuous_scroll_types_are_not_discarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = self.inspect(root, "paging", outer_scroll=True, outer_type="Swiper")
            right = self.inspect(root, "continuous", outer_scroll=True, outer_type="Scroll")
            critical = compare_targets(left, right)["boundary_comparison"]
            self.assertEqual(critical["status"], "different")
            self.assertIn("scroll_context", critical["different_fields"])
            self.assertEqual(critical["features"]["scroll_context"]["reference"][0]["type"], "Swiper")

    def test_unknown_scroll_container_type_is_not_a_matching_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = self.inspect(Path(tmp), "unknown-type", outer_scroll=True, outer_type="")
            critical = compare_targets(evidence, evidence)["boundary_comparison"]
            self.assertEqual(critical["status"], "incomplete")
            self.assertIn("scroll_context", critical["unknown_fields"])

    def test_boolean_json_and_zero_window_id_match_xml_style_attributes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = self.inspect(root, "strings", window="0")
            right = self.inspect(root, "native", native=True, window=0)
            comparison = compare_targets(left, right)
            self.assertEqual(comparison["local_assessment"]["status"], "structural_candidate")
            self.assertEqual(comparison["boundary_comparison"]["status"], "observed_boundary_relations_match")
            self.assertTrue(all(row["equal"] for row in comparison["feature_comparison"].values()))

    def test_missing_ancestor_flag_is_unknown_even_when_both_trees_omit_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self.inspect(root, "missing", unknown=True)
            critical = compare_targets(evidence, evidence)["boundary_comparison"]
            self.assertEqual(critical["status"], "incomplete")
            self.assertIn("scroll_context", critical["unknown_fields"])
            self.assertEqual(critical["reference"]["unknown_ancestor_fields"][0]["field"], "scrollable")

    def test_equal_boxes_do_not_establish_boundary_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self.inspect(root, "normal", loss=False)
            critical = compare_targets(evidence, evidence)["boundary_comparison"]
            self.assertEqual(critical["status"], "no_exported_boundary_loss")
            self.assertEqual(critical["visual_content_loss"], "requires_separate_review")

    def test_wrapper_type_difference_is_reported_separately_from_boundary_relation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = self.inspect(root, "custom", parent_type="Custom")
            right = self.inspect(root, "row", parent_type="Row")
            comparison = compare_targets(left, right)
            self.assertIn("parent_type", comparison["local_assessment"]["different_fields"])
            self.assertEqual(comparison["boundary_comparison"]["status"], "observed_boundary_relations_match")

    def test_empty_screen_envelope_is_recorded_separately_from_ui_ancestors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = self.inspect(root, "wrapped")
            filename = Path(evidence["tree"])
            tree = json.loads(filename.read_text(encoding="utf-8"))
            tree["attributes"]["type"] = "root"
            filename.write_text(json.dumps({"attributes": {
                "type": "", "bounds": "[0,0][200,200]", "clip": "", "scrollable": ""},
                "children": [tree]}), encoding="utf-8")
            evidence = inspect_target(filename, evidence["screenshot"], {"text": "target"})
            critical = compare_targets(evidence, evidence)["boundary_comparison"]
            self.assertEqual(critical["status"], "observed_boundary_relations_match")
            self.assertEqual(len(critical["reference"]["excluded_export_envelopes"]), 1)


if __name__ == "__main__":
    unittest.main()
