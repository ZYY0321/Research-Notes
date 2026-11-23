import copy
import tempfile
import unittest
from pathlib import Path
from truncator.mutation.operators import mutate
from truncator.mutation.mutations import plans
from truncator.common.storage import digest, contained, save, read
from truncator.common.locking import lock


class CoreTests(unittest.TestCase):
    def site(self):
        code = 'Text("中文😀")\r\n  .width(240)'
        begin = code.index("240")
        return {
            "id": "one",
            "file": "Index.ets",
            "start": 0,
            "end": len(code),
            "snippet": code,
            "sha256": digest(code),
            "component": "Text",
            "repeated": False,
            "operators": ["line-clip", "height-clip", "parent-clip"],
            "attributes": [{"name": "width", "start": begin, "end": begin + 3}],
            "context": [],
        }

    def test_replaces_attribute_without_duplicate(self):
        code = mutate(self.site(), "line-clip", {"width": 30})
        self.assertEqual(code.count(".width("), 1)
        self.assertIn("width(30)", code)
        self.assertIn("中文😀", code)
        self.assertIn("\r\n", code)

    def test_height_does_not_limit_lines(self):
        code = mutate(self.site(), "height-clip", {"height": 10})
        self.assertIn(".height(10)", code)
        self.assertNotIn("maxLines", code)

    def test_narrow_wrapper_rejects_percentage_padding_from_shared_style(self):
        site = self.site()
        site["operators"] += ["fixed-parent-clip", "scroll-recovery", "whitespace-clip"]
        site["styles"] = {"attributes": [{"name": "padding", "origin": "style",
            "status": "resolved", "value": {"top": "1.5%", "left": "3.3%"},
            "text": '{top: "1.5%", left: "3.3%"}'}], "unresolved": []}
        parameters = {"child_width": 240, "child_height": 50, "width": 100, "height": 50}
        for operator in ("parent-clip", "fixed-parent-clip", "scroll-recovery", "whitespace-clip"):
            with self.subTest(operator=operator), self.assertRaisesRegex(ValueError, "percentage padding"):
                mutate(site, operator, parameters)
        # The earlier height-cut case keeps the wrapper width and remains usable.
        mutate(site, "height-clip", {**parameters, "width": 240, "height": 30, "preserve_slot": True})
        mutate(site, "scroll-recovery", {**parameters, "width": 240, "height": 30, "scroll_direction": "Vertical"})

    def test_fixed_padding_does_not_reject_narrow_scroll(self):
        site = self.site()
        site["operators"].append("scroll-recovery")
        site["styles"] = {"attributes": [{"name": "padding", "status": "resolved",
            "value": {"left": 8}, "text": "{left: 8}"}], "unresolved": []}
        code = mutate(site, "scroll-recovery", {
            "child_width": 240, "child_height": 50, "width": 100, "height": 50})
        self.assertIn(".scrollable(ScrollDirection.Horizontal)", code)
        self.assertIn(".scrollBar(BarState.Off)", code)

    def test_narrow_wrapper_does_not_assume_dynamic_padding_is_absolute(self):
        site = self.site()
        site["styles"] = {"attributes": [{"name": "padding", "status": "unresolved",
            "text": "this.contentPadding"}], "unresolved": []}
        with self.assertRaisesRegex(ValueError, "statically resolved padding"):
            mutate(site, "parent-clip", {"child_width": 240, "width": 100, "height": 50})

    def test_rejects_repeated_instances(self):
        site = self.site()
        site["repeated"] = True
        with self.assertRaises(ValueError):
            mutate(site, "line-clip", {})

    def test_rejects_bad_parameters(self):
        for width in [-1, 0, float("nan"), float("inf"), True]:
            with self.assertRaises(ValueError):
                mutate(self.site(), "line-clip", {"width": width})

    def test_ambiguous_attribute(self):
        site = self.site()
        site["attributes"] *= 2
        with self.assertRaises(ValueError):
            mutate(site, "line-clip", {})

    def test_seed_reproduction_and_unique_sites(self):
        a = self.site()
        b = copy.deepcopy(a)
        b["id"] = "two"
        catalog = {"root": "x", "files": {"Index.ets": "hash"}, "sites": [a, b]}
        first = plans(catalog, 42, 2, "line-clip", {"width": 30})
        self.assertEqual(first, plans(catalog, 42, 2, "line-clip", {"width": 30}))
        self.assertEqual(len({p["site"]["id"] for p in first}), 2)

    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                contained(directory, "../other")

    def test_lock_exclusion_and_atomic_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "device.lock"
            with lock(path):
                with self.assertRaises(FileExistsError):
                    with lock(path):
                        pass
            self.assertEqual(read(path)["protocol"], "kernel-v1")
            with lock(path):
                pass
            save(Path(directory) / "record.json", {"文字": 1})
            self.assertEqual(read(Path(directory) / "record.json"), {"文字": 1})


if __name__ == "__main__":
    unittest.main()
