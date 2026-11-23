import copy
import tempfile
import unittest
from pathlib import Path
from truncator.imaging.geometry import crossing_translation, overlap_translation, rectangle
from truncator.source.binding import background_color, bind_candidates
from truncator.mutation.operators import mutate, CONTENT_OPERATORS, TEXT_OPERATORS
from truncator.mutation.mutations import apply_patches, mutation_patches
from truncator.common.storage import digest


def site(code='Text("title").width(100)'):
    start = code.index("100")
    return {
        "id": "a",
        "file": "Index.ets",
        "start": 0,
        "end": len(code),
        "snippet": code,
        "sha256": digest(code),
        "component": "Text",
        "repeated": False,
        "operators": CONTENT_OPERATORS + TEXT_OPERATORS,
        "attributes": [
            {"name": "width", "start": start, "end": start + 3, "text": "100"}
        ],
        "arguments": ['"title"'],
        "parent_id": "parent",
    }


class GeometryTests(unittest.TestCase):
    def test_crossing_uses_existing_margin(self):
        target = [20, 30, 100, 90]
        parent = [0, 0, 120, 120]
        self.assertEqual(crossing_translation(target, parent, "top", 12), (0, -42))
        self.assertEqual(crossing_translation(target, parent, "right", 12), (32, 0))
        self.assertEqual(crossing_translation(target, parent, "bottom", 12), (0, 42))
        self.assertEqual(crossing_translation(target, parent, "left", 12), (-32, 0))

    def test_overlap_targets_edge(self):
        target = [20, 30, 100, 90]
        cover = [20, 110, 100, 150]
        self.assertEqual(overlap_translation(target, cover, "bottom", 12), (0, -32))
        self.assertEqual(overlap_translation(target, cover, "top", 12), (0, -108))

    def test_invalid_geometry(self):
        for rect in ["[0,0][0,4]", "nonsense 1 2 3 4", [1, 2, 0, 4]]:
            with self.assertRaises(ValueError):
                rectangle(rect)
        for cut in [0, -1, float("nan")]:
            with self.assertRaises(ValueError):
                crossing_translation([0, 0, 10, 10], [0, 0, 10, 10], "top", cut)

    def test_fixed_parent_pins_child(self):
        code = mutate(
            site(),
            "fixed-parent-clip",
            {"child_width": 100, "child_height": 24, "width": 60, "height": 24},
        )
        self.assertIn(".width(100)", code)
        self.assertIn(".width(60)", code)
        self.assertIn(".flexShrink(0)", code)
        self.assertIn(".clip(true)", code)

    def test_signed_translation(self):
        code = mutate(
            site(),
            "translate-clip",
            {
                "child_width": 100,
                "child_height": 24,
                "width": 100,
                "height": 24,
                "x": 0,
                "y": -12,
            },
        )
        self.assertIn(".translate({ x: 0, y: -12 })", code)

    def test_ellipsis_preserves_width_for_line_only(self):
        code = mutate(site(), "ellipsis-lines", {"lines": 2})
        self.assertIn(".width(100)", code)
        self.assertIn("Ellipsis", code)
        self.assertIn("maxLines(2)", code)

    def test_opaque_overlay_and_color_validation(self):
        p = {
            "child_width": 100,
            "child_height": 24,
            "width": 100,
            "height": 24,
            "cover_width": 100,
            "cover_height": 8,
            "cover_x": 0,
            "cover_y": 16,
            "color": "#FFFFFF",
        }
        code = mutate(site(), "overlay-occlusion", p)
        self.assertIn("Stack(", code)
        self.assertIn("HitTestMode.None", code)
        for color in ["red", "#00FFFFFF", "evil()"]:
            with self.assertRaises(ValueError):
                mutate(site(), "overlay-occlusion", {**p, "color": color})

    def test_resolves_background_without_ai(self):
        target = {
            "attributes": {"backgroundColor": "#00000000"},
            "ancestors": [{"attributes": {"backgroundColor": "#FF1FA1FF"}}],
        }
        self.assertEqual(background_color(target), "#1FA1FF")
        target["attributes"]["backgroundColor"] = "#801FA1FF"
        with self.assertRaises(ValueError):
            background_color(target)

    def test_atomic_patch_validation(self):
        edits = [
            {"start": 0, "end": 1, "before": "a", "after": "A"},
            {"start": 2, "end": 3, "before": "c", "after": "C"},
        ]
        self.assertEqual(apply_patches("abc", edits), "AbC")
        edits[1]["before"] = "d"
        with self.assertRaises(ValueError):
            apply_patches("abc", edits)

    def test_overlapping_patches_rejected(self):
        edits = [
            {"start": 0, "end": 2, "before": "ab", "after": "A"},
            {"start": 1, "end": 3, "before": "bc", "after": "C"},
        ]
        with self.assertRaises(ValueError):
            apply_patches("abc", edits)

    def test_duplicate_runtime_and_source_binding(self):
        record = {
            "attributes": {"text": "title", "type": "Text", "bounds": "[0,0][10,10]"},
            "children": [],
        }
        catalog = {"root": ".", "sites": [site()]}
        self.assertEqual(len(bind_candidates(catalog, record)["bindings"]), 1)
        self.assertEqual(bind_candidates(catalog, [record, record])["bindings"], [])
        catalog["sites"].append({**site(), "id": "b"})
        self.assertEqual(bind_candidates(catalog, record)["bindings"], [])

    def test_constraint_conflict_rejected(self):
        s = site()
        s["attributes"].append(
            {"name": "layoutWeight", "text": "1", "start": 0, "end": 1}
        )
        with self.assertRaises(ValueError):
            mutate(
                s,
                "fixed-parent-clip",
                {"child_width": 100, "child_height": 24, "width": 60, "height": 24},
            )

    def test_numeric_margin_and_dynamic_rejection(self):
        from truncator.source.source_attributes import numeric_attribute

        target = site()
        target["attributes"].append({"name": "margin", "text": "{top: 20, left: 5}"})
        self.assertEqual(
            numeric_attribute(target, "margin", ["top", "left"])["top"], 20
        )
        target["attributes"][-1]["text"] = "this.spacing"
        with self.assertRaises(ValueError):
            numeric_attribute(target, "margin", ["top", "left"])

    def test_wrapper_transfers_outer_margin(self):
        code = 'Text("title").width(100).margin({ top: 20 })'
        target = site(code)
        begin = code.index("{ top: 20 }")
        target["attributes"].append(
            {"name": "margin", "start": begin, "end": begin + 11, "text": "{ top: 20 }"}
        )
        result = mutate(
            target,
            "fixed-parent-clip",
            {"child_width": 100, "child_height": 24, "width": 60, "height": 24},
        )
        self.assertIn(".margin(0)", result)
        self.assertTrue(result.endswith(".margin({ top: 20 })"))

    def test_sibling_requires_bound_occluder(self):
        plan = {
            "site": site(),
            "operator": "sibling-translate-occlusion",
            "parameters": {},
        }
        with self.assertRaises(ValueError):
            mutation_patches(plan)


if __name__ == "__main__":
    unittest.main()
