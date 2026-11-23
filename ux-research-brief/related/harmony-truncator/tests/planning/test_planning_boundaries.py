"""Regressions for source/runtime identity and batch failure isolation."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from truncator.source.binding import parent_binding, ancestor_binding
from truncator.common.storage import save
from truncator.execution.workflow import batch


class BoundaryTests(unittest.TestCase):
    def test_parent_prefers_declared_id_over_nearest_matching_type(self):
        parent = {"id": "parent", "component": "Row", "attributes": [
            {"name": "id", "text": "'original'"}]}
        catalog = {"structural_sites": [parent]}
        outer = {"attributes": {"type": "Row", "id": "original", "bounds": [0, 0, 100, 40]}}
        inner = {"attributes": {"type": "Row", "id": "injected", "bounds": [0, 0, 80, 40]}}
        target = {"ancestors": [outer, inner]}
        site = {"parent_id": "parent"}
        self.assertIs(parent_binding(catalog, site, target)[1], outer)
        self.assertIs(ancestor_binding(catalog, site, target, "Row")[1], outer)
        parent["attributes"] = []
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            parent_binding(catalog, site, target)

    def test_invalid_plan_does_not_prevent_later_package_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad, good = root / "a.json", root / "b.json"
            bad.write_text("{ broken", encoding="utf-8")
            save(good, {"id": "good"})
            with patch("truncator.execution.workflow.prepare"), patch("truncator.execution.workflow.build") as build:
                results = batch({}, [bad, good], root / "output")
            self.assertEqual([r["status"] for r in results], ["failed", "built"])
            self.assertIsNone(results[0]["run"])
            build.assert_called_once()

    def test_plan_directory_cannot_escape_batch_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = root / "bad.json"
            save(bad, {"id": "../outside"})
            with patch("truncator.execution.workflow.prepare") as prepare:
                results = batch({}, [bad], root / "output")
            self.assertEqual(results[0]["status"], "failed")
            prepare.assert_not_called()
