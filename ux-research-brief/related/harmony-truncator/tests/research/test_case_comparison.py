"""Production review must be reproducible from the attached commercial tree."""

import copy
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from research.production_evidence.case_evidence import template, validate, record_case_review, export_case_review, verify_exported_case
from research.production_evidence.comparison import inspect_target, compare_targets
from truncator.common.storage import read, save, digest


class CaseComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.capture = self.root / "run/capture"
        self.capture.mkdir(parents=True)
        attrs = {"type": "Text", "id": "target", "text": "fixture", "hostWindowId": "1",
                 "clip": "false", "scrollable": "false", "bounds": "[10,10][80,30]",
                 "origBounds": "[10,10][100,30]"}
        tree = {"attributes": {"type": "Row", "hostWindowId": "1", "clip": "true",
                               "scrollable": "false", "bounds": "[0,0][80,100]",
                               "origBounds": "[0,0][80,100]"}, "children": [
            {"attributes": attrs}, {"attributes": {**attrs, "id": "other",
                                                   "bounds": "[10,40][80,60]",
                                                   "origBounds": "[10,40][100,60]"}}]}
        for name in ("tree-before.json", "tree-after.json"):
            save(self.capture / name, tree)
        Image.new("RGB", (200, 200), "white").save(self.capture / "snapshot.jpeg")
        save(self.capture / "capture.json", {"recipe": {}, "screenshot_sha256":
                                             digest((self.capture / "snapshot.jpeg").read_bytes())})
        save(self.capture.parent / "plan.json", {"id": "mutation", "operator": "parent-clip",
                                                "geometry": {"mutated_selector": {"id": "target"}}})
        self.reference_tree = self.root / "reference.json"
        save(self.reference_tree, tree)
        self.reference_image = self.root / "reference.jpeg"
        shutil.copy2(self.capture / "snapshot.jpeg", self.reference_image)
        self.comparison = compare_targets(
            inspect_target(self.reference_tree, self.reference_image, {"id": "target"}),
            inspect_target(self.capture / "tree-before.json", self.capture / "snapshot.jpeg", {"id": "target"}))
        self.review = template(self.capture)
        self.review.update(level="production-supported", reviewer="test fixture", rationale="synthetic test only")
        self.review["targets"]["mutation"] = {k: "test fixture" for k in self.review["targets"]["mutation"]}
        # These test files exercise the binding contract, not actual source realism.
        for role in ("independent-source", "repair"):
            path = self.root / (role + ".txt")
            path.write_text("synthetic fixture")
            self.attach(role, path)
        self.attach("reference-tree", self.reference_tree)
        self.attach("reference-image", self.reference_image)
        self.update_comparison(self.comparison)

    def attach(self, role, path):
        sha = digest(path.read_bytes())
        self.review["evidence"].append({"role": role, "path": str(path), "sha256": sha})
        return sha

    def update_comparison(self, comparison):
        self.review["evidence"] = [e for e in self.review["evidence"] if e["role"] != "tree-comparison"]
        path = self.root / "comparison.json"
        save(path, comparison)
        self.review["targets"]["mutation"]["comparison_sha256"] = self.attach("tree-comparison", path)

    def test_matching_review_survives_export_without_original_files(self):
        validate(self.review, self.capture)
        submitted = self.root / "review.json"
        save(submitted, self.review)
        record_case_review(self.capture, submitted)
        destination = self.root / "portable"
        destination.mkdir()
        for name in ("capture.json", "snapshot.jpeg", "tree-before.json", "tree-after.json"):
            shutil.copy2(self.capture / name, destination / name)
        shutil.copy2(self.capture.parent / "plan.json", destination / "plan.json")
        export_case_review(self.capture, destination)
        original_open = Path.open

        def package_only(path, *args, **kwargs):
            self.assertTrue(path.resolve().is_relative_to(destination.resolve()), str(path))
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", package_only):
            self.assertEqual(verify_exported_case(destination)["level"], "production-supported")

    def test_role_names_without_per_target_binding_do_not_pass(self):
        del self.review["targets"]["mutation"]["comparison_sha256"]
        with self.assertRaisesRegex(ValueError, "comparison_sha256"):
            validate(self.review, self.capture)

    def test_comparison_for_another_target_is_rejected_even_with_updated_hashes(self):
        comparison = compare_targets(
            inspect_target(self.reference_tree, self.reference_image, {"id": "other"}),
            inspect_target(self.capture / "tree-before.json", self.capture / "snapshot.jpeg", {"id": "other"}))
        self.update_comparison(comparison)
        with self.assertRaisesRegex(ValueError, "planned mutation target"):
            validate(self.review, self.capture)

    def test_old_frame_cannot_support_current_capture(self):
        old = copy.deepcopy(self.comparison)
        old["injected"]["screenshot_sha256"] = "old-frame"
        self.update_comparison(old)
        with self.assertRaisesRegex(ValueError, "current raw"):
            validate(self.review, self.capture)

    def test_claimed_match_is_recomputed_even_when_report_hash_is_updated(self):
        altered = copy.deepcopy(self.comparison)
        altered["boundary_comparison"]["reference"]["features"]["scroll_context"] = []
        altered["injected"]["target"]["attributes"]["text"] = "forged description"
        self.update_comparison(altered)
        with self.assertRaisesRegex(ValueError, "current raw"):
            validate(self.review, self.capture)

    def test_missing_reference_tree_is_rejected(self):
        self.review["evidence"] = [e for e in self.review["evidence"] if e["role"] != "reference-tree"]
        with self.assertRaisesRegex(ValueError, "attached reference"):
            validate(self.review, self.capture)

    def test_real_scroll_difference_cannot_be_upgraded_by_text_review(self):
        tree = read(self.reference_tree)
        tree["attributes"]["scrollable"] = "true"
        save(self.reference_tree, tree)
        self.review["evidence"] = [e for e in self.review["evidence"] if e["role"] != "reference-tree"]
        self.attach("reference-tree", self.reference_tree)
        changed = compare_targets(inspect_target(self.reference_tree, self.reference_image, {"id": "target"}),
                                  self.comparison["injected"])
        self.update_comparison(changed)
        with self.assertRaisesRegex(ValueError, "structural differences"):
            validate(self.review, self.capture)
