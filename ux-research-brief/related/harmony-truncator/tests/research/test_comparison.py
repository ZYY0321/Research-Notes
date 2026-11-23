import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from research.production_evidence.comparison import inspect_target, compare_targets, load_tree


class ComparisonTests(unittest.TestCase):
    def test_boundary_relation_preserves_scroll_and_window(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "screen.png"
            Image.new("RGB", (200, 200)).save(image)
            target = {"type": "Text", "text": "target", "hostWindowId": "1",
                      "bounds": "[10,10][80,30]", "origBounds": "[10,10][100,30]",
                      "clip": "false", "scrollable": "false"}
            results = []
            for scrollable, window in [("false", "1"), ("true", "1"), ("false", "2")]:
                tree = root / f"{scrollable}-{window}.json"
                tree.write_text(json.dumps({"attributes": {
                    "type": "Row", "hostWindowId": window, "clip": "true",
                    "scrollable": scrollable, "bounds": "[0,0][80,100]",
                    "origBounds": "[0,0][80,100]"},
                    "children": [{"attributes": target}]}), encoding="utf-8")
                results.append(inspect_target(tree, image, {"text": "target"}))
            comparison = compare_targets(results[0], results[1])
            self.assertEqual(comparison["local_assessment"]["status"], "different")
            self.assertIn("nearest_aligned_clip_ancestors",
                          comparison["local_assessment"]["different_fields"])
            other_window = compare_targets(results[0], results[2])
            witnesses = other_window["local_relations"]["injected"]["aligned_clip_ancestor_witnesses"]
            self.assertEqual(witnesses["right"], [])

    def test_local_match_keeps_visual_review_and_screen_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tree = root / "tree.json"
            tree.write_text(json.dumps({"attributes": {
                "type": "Row", "hostWindowId": "1", "clip": "true", "scrollable": "false",
                "bounds": "[0,0][80,100]", "origBounds": "[0,0][80,100]"},
                "children": [{"attributes": {
                    "type": "Text", "text": "target", "hostWindowId": "1",
                    "clip": "false", "scrollable": "false",
                    "bounds": "[10,10][80,30]", "origBounds": "[10,10][100,30]"}}]}),
                encoding="utf-8")
            results = []
            for width in (80, 200):
                image = root / f"{width}.png"
                Image.new("RGB", (width, 200)).save(image)
                results.append(inspect_target(tree, image, {"text": "target"}))
            same = compare_targets(results[0], results[0])
            self.assertEqual(same["local_assessment"]["status"], "structural_candidate")
            self.assertTrue(same["local_assessment"]["visual_review_required"])
            different = compare_targets(results[0], results[1])
            self.assertIn("loss_at_screen_edges", different["local_assessment"]["different_fields"])

    def test_xml_json_equivalence_and_missing_original(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            xml = root / "tree.xml"
            xml.write_text('<node type="Scroll" bounds="[0,0][100,100]" '
                           'scrollable="true"><node type="Text" text="完整文字" '
                           'bounds="[0,0][80,20]" clip="false"/></node>', encoding="utf-8")
            tree = root / "tree.json"
            tree.write_text(json.dumps(load_tree(xml)), encoding="utf-8")
            image = root / "screen.png"
            Image.new("RGB", (100, 100)).save(image)
            selector = {"type": "Text", "text": "完整文字"}
            left = inspect_target(xml, image, selector)
            right = inspect_target(tree, image, selector)
            self.assertEqual(left["target"], right["target"])
            self.assertIsNone(left["target"]["exported_edge_loss_px"])
            self.assertEqual(left["recovery"], "unmeasured")
            comparison = compare_targets(left, right)
            self.assertIsNone(comparison["feature_comparison"]["exported_loss_edges"]["equal"])
            self.assertEqual(comparison["mechanism_assessment"],
                             "requires_visual_and_behavioral_review")

    def test_window_ambiguity_and_screen_edge(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            attrs = {"type": "Text", "text": "我的", "clip": "false",
                     "bounds": "[0,90][20,100]", "origBounds": "[0,90][20,105]"}
            tree = root / "tree.json"
            tree.write_text(json.dumps({"children": [
                {"attributes": {**attrs, "hostWindowId": "1"}},
                {"attributes": {**attrs, "hostWindowId": "2"}},
            ]}), encoding="utf-8")
            image = root / "screen.png"
            Image.new("RGB", (100, 100)).save(image)
            with self.assertRaisesRegex(ValueError, "matched 2"):
                inspect_target(tree, image, {"text": "我的"})
            result = inspect_target(tree, image, {"text": "我的", "hostWindowId": "1"})
            self.assertEqual(result["orig_outside_screen_px"]["bottom"], 5)
            self.assertAlmostEqual(result["exported_edge_loss_ratio"]["bottom"], 1 / 3)
            self.assertEqual(result["visual_content_loss"], "unreviewed")
