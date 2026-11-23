"""Conflicting exported observations must not depend on input order."""

import tempfile
import unittest
from pathlib import Path

from truncator.review.datasets.dataset_balance import audit_exports
from truncator.review.datasets.dataset_consensus import reconcile
from truncator.common.storage import save, read, digest
from truncator.review.review_evidence import capture_hashes


class DatasetConsensusTests(unittest.TestCase):
    def test_shared_frame_keeps_targets_but_counts_one_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.export(Path(tmp))
            manifest = read(root / "manifest.json")
            first = manifest["samples"][0]
            first["mutations"] = [
                {"id": "image", "mechanism": "fixed-parent-clip", "component": "Image"},
                {"id": "symbol", "mechanism": "fixed-parent-clip", "component": "SymbolGlyph"},
            ]
            save(root / "manifest.json", manifest)
            coverage = audit_exports([root])["coverage"]
            self.assertEqual(coverage["target_states"], 2)
            self.assertEqual(coverage["captures"], 1)
            self.assertEqual(coverage["image_tree_sets"], 1)
            self.assertEqual(len(coverage["by_component_axis"]), 2)

    def test_recapture_does_not_invent_new_application_or_image_tree_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = [self.export(Path(tmp) / str(i)) for i in range(2)]
            for i, root in enumerate(roots):
                folder = root / "a"
                record = read(folder / "capture.json")
                record.update(attempt=i, session={"status": "verified", "process": {"bundle": "example.app"}})
                save(folder / "capture.json", record)
                review = read(folder / "review.json")
                review["capture_files"] = capture_hashes(folder)
                save(folder / "review.json", review)
            result = audit_exports(roots)
            self.assertEqual(result, audit_exports(list(reversed(roots))))
            coverage = result["coverage"]
            self.assertEqual(coverage["captures"], 2)
            self.assertEqual(coverage["image_tree_sets"], 1)
            self.assertEqual(coverage["verified_applications"], 1)
            self.assertEqual(coverage["by_application"]["example.app"]["target_states"], 2)

    def test_identical_screenshot_with_different_tree_is_not_merged(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = [self.export(Path(tmp) / str(i)) for i in range(2)]
            folder = roots[1] / "a"
            record = read(folder / "capture.json")
            record["attempt"] = "another-state"
            save(folder / "capture.json", record)
            save(folder / "tree-before.json", {"scrollable": True})
            review = read(folder / "review.json")
            review["capture_files"] = capture_hashes(folder)
            save(folder / "review.json", review)
            coverage = audit_exports(roots)["coverage"]
            self.assertEqual(coverage["screenshot_files"], 1)
            self.assertEqual(coverage["image_tree_sets"], 2)

    def test_unverified_profile_cannot_create_application_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.export(Path(tmp))
            save(root / "a/profile.json", {"bundle": "unverified-app"})
            coverage = audit_exports([root])["coverage"]
            self.assertEqual(coverage["verified_applications"], 0)
            self.assertEqual(coverage["target_states_without_verified_application"], 1)

    def test_attempted_but_inconclusive_recovery_does_not_fill_binary_label_quota(self):
        from truncator.review.review_policy import validate_observation_labels
        validate_observation_labels("clipped", "inconclusive")
        with tempfile.TemporaryDirectory() as tmp:
            a = self.export(Path(tmp) / "inconclusive", recovery="inconclusive")
            result = audit_exports([a], {"label": {"positive": 1, "negative": 1}})
            self.assertEqual(result["counts"]["label"], {"unresolved": 1})
            self.assertEqual(result["deficits"]["label"], {"positive": 1, "negative": 1})
            self.assertEqual(result["units"][0]["recovery_status"], "inconclusive")

    def test_conclusive_review_can_resolve_inconclusive_without_order_dependence(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self.export(Path(tmp) / "inconclusive", recovery="inconclusive")
            b = self.export(Path(tmp) / "confirmed", recovery="not-recovered")
            result = audit_exports([a, b])
            self.assertEqual(result, audit_exports([b, a]))
            self.assertEqual(result["conflicts"], [])
            self.assertEqual(result["counts"]["label"], {"positive": 1})

    def export(self, root, content="clipped", recovery="not-recovered"):
        save(root / "export-status.json", {"complete": True})
        save(root / "a/capture.json", {"identity": "same-frame", "screenshot_sha256": digest(b"fixture image")})
        for name in ("tree-before.json", "tree-after.json"):
            save(root / "a" / name, {})
        (root / "a/snapshot.jpeg").write_bytes(b"fixture image")
        save(root / "a/review.json", {
            "decision": "accepted", "screenshot_sha256": digest(b"fixture image"),
            "capture_files": capture_hashes(root / "a"),
            "content_status": content, "recovery_status": recovery,
        })
        save(root / "manifest.json", {"samples": [{
            "id": "a", "component": "Image",
            "content_status": content, "recovery_status": recovery,
        }]})
        return root

    def test_opposite_labels_are_quarantined_in_both_read_orders(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self.export(Path(tmp) / "a")
            b = self.export(Path(tmp) / "b", recovery="recovered")
            first = audit_exports([a, b], {"component": {"Image": 1}})
            self.assertEqual(first, audit_exports([b, a], {"component": {"Image": 1}}))
            self.assertEqual(first["counts"]["label"], {})
            self.assertEqual(first["deficits"]["component"], {"Image": 1})
            self.assertEqual(len(first["conflicts"]), 1)
            self.assertEqual(len(first["units"][0]["sources"]), 2)
            self.assertEqual(first["coverage"]["target_states"], 0)
            self.assertEqual(first["coverage"]["captures"], 0)
            self.assertEqual(first["coverage"]["excluded_conflicting_target_states"], 1)

    def test_same_binary_label_still_preserves_content_disagreement(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self.export(Path(tmp) / "a", recovery="recovered")
            b = self.export(Path(tmp) / "b", "complete", "not-applicable")
            result = audit_exports([a, b])
            self.assertIn("content_status", result["conflicts"][0]["differences"])
            self.assertEqual(result["counts"]["label"], {})

    def test_later_complete_review_can_resolve_unknown_without_double_counting(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self.export(Path(tmp) / "a", recovery="not-tested")
            b = self.export(Path(tmp) / "b")
            result = audit_exports([a, b])
            self.assertEqual(result, audit_exports([b, a]))
            self.assertEqual(result["conflicts"], [])
            self.assertEqual(result["counts"]["label"], {"positive": 1})
            self.assertEqual(len(result["duplicates_excluded"]), 1)

    def test_partial_observations_are_not_combined_into_invented_review(self):
        common = dict(capture_sha256="same", target_key="same", sample="a",
                      label="unresolved", realism="unresolved")
        rows = [{**common, "export": "a", "content_status": "clipped", "recovery_status": "not-tested"},
                {**common, "export": "b", "content_status": "uncertain", "recovery_status": "recovered"}]
        units, _, conflicts = reconcile(rows)
        self.assertEqual(conflicts, [])
        self.assertEqual(units[0]["label"], "unresolved")
        self.assertIn((units[0]["content_status"], units[0]["recovery_status"]),
                      [("clipped", "not-tested"), ("uncertain", "recovered")])

    def test_same_capture_metadata_with_different_tree_is_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self.export(Path(tmp) / "a")
            b = self.export(Path(tmp) / "b")
            save(b / "a/tree-after.json", {"changed": True})
            review = read(b / "a/review.json")
            review["capture_files"] = capture_hashes(b / "a")
            save(b / "a/review.json", review)
            result = audit_exports([a, b])
            self.assertIn("evidence_sha256", result["conflicts"][0]["differences"])

    def test_manifest_cannot_override_bound_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.export(Path(tmp))
            manifest = read(root / "manifest.json")
            manifest["samples"][0]["recovery_status"] = "recovered"
            save(root / "manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "bound visual review"):
                audit_exports([root])

    def test_changed_screenshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.export(Path(tmp))
            (root / "a/snapshot.jpeg").write_bytes(b"different")
            with self.assertRaisesRegex(ValueError, "screenshot changed"):
                audit_exports([root])

    def test_combined_page_requires_bound_capture_and_kept_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "applications/app/paths/1/mutated"
            save(root / "export-status.json", {"complete": True})
            for name in ("capture.json", "tree-before.json", "tree-after.json"):
                save(folder / name, {})
            (folder / "snapshot.jpeg").write_bytes(b"fixture")
            labels = {"content_status": "clipped", "recovery_status": "not-recovered"}
            review = {"decisions": {"m": {"decision": "keep", **labels}},
                      "captures": [{"page": "Index", "files": {
                          p.name: digest(p.read_bytes()) for p in folder.iterdir()}}]}
            save(root / "applications/app/review.json", review)
            save(root / "manifest.json", {"samples": [{
                "id": "sample", "application": "app", "page": "Index",
                "path": "applications/app/paths/1",
                "mutations": [{"id": "m", "mechanism": "fixed-parent-clip", "component": "Image"}],
                "target_observations": {"m": labels}}]})
            self.assertEqual(audit_exports([root])["counts"]["label"], {"positive": 1})
            missing = review["captures"][0]["files"].pop("tree-after.json")
            save(root / "applications/app/review.json", review)
            with self.assertRaisesRegex(ValueError, "all four"):
                audit_exports([root])
            review["captures"][0]["files"]["tree-after.json"] = missing
            save(root / "applications/app/review.json", review)
            save(folder / "tree-after.json", {"changed": True})
            with self.assertRaisesRegex(ValueError, "capture changed"):
                audit_exports([root])


if __name__ == "__main__":
    unittest.main()
