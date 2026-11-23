"""A visual decision applies to one complete capture and its recovery evidence."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image
from truncator.review.datasets.dataset import export_dataset
from truncator.review.datasets.dataset_balance import audit_exports
from truncator.review.review_evidence import validate_single_review
from truncator.common.storage import read, save, digest
from truncator.execution.workflow import review


class SingleReviewIntegrityTests(unittest.TestCase):
    def capture(self, root, name="capture-1"):
        cap = root / name
        cap.mkdir(parents=True)
        Image.new("RGB", (40, 20), "white").save(cap / "snapshot.jpeg")
        save(cap / "capture.json", {"screenshot_sha256": digest((cap / "snapshot.jpeg").read_bytes()),
                                   "hap_sha256": "same-package", "recipe": {}})
        for name in ("tree-before.json", "tree-after.json"):
            save(cap / name, {"text": "fixture"})
        save(root / "profile.json", {"bundle": "fixture"})
        return cap

    def accepted(self, cap, **kwargs):
        return review(cap, "accepted", "fixture", "Fixture review", [],
                      content_status="clipped", recovery_status="recovered", **kwargs)

    def test_each_primary_file_is_bound_before_export(self):
        for name in ("tree-before.json", "tree-after.json", "capture.json", "snapshot.jpeg"):
            with self.subTest(file=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                cap = self.capture(root / "run")
                self.accepted(cap)
                if name == "snapshot.jpeg":
                    Image.new("RGB", (40, 20), "blue").save(cap / name)
                else:
                    record = read(cap / name)
                    record["changed"] = True
                    save(cap / name, record)
                with self.assertRaisesRegex(ValueError, "changed"):
                    export_dataset(root / "run", root / "export")
                self.assertFalse((root / "export/export-status.json").exists())

    def test_legacy_image_only_review_requires_explicit_rereview(self):
        with tempfile.TemporaryDirectory() as tmp:
            cap = self.capture(Path(tmp))
            path = self.accepted(cap)
            legacy = read(path)
            legacy.pop("capture_files")
            with self.assertRaisesRegex(ValueError, "four-file capture binding"):
                validate_single_review(cap, legacy)

    def test_exported_tree_and_recovery_tree_remain_bound(self):
        for additional in (False, True):
            with self.subTest(additional=additional), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                cap = self.capture(root / "run")
                tail = self.capture(root / "run", "capture-2")
                self.accepted(cap, evidence_captures=[tail])
                export_dataset(root / "run", root / "export")
                self.assertEqual(audit_exports([root / "export"])["counts"]["label"], {"negative": 1})
                exported = next((root / "export").glob("*/review.json"))
                target = exported.parent
                if additional:
                    target /= read(exported)["evidence_captures"][0]["capture"]
                save(target / "tree-after.json", {"changed": True})
                with self.assertRaisesRegex(ValueError, "changed"):
                    audit_exports([root / "export"])

    def test_recovery_evidence_cannot_escape_export_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cap = self.capture(root / "run")
            tail = self.capture(root / "run", "capture-2")
            self.accepted(cap, evidence_captures=[tail])
            export_dataset(root / "run", root / "export")
            exported = next((root / "export").glob("*/review.json"))
            record = read(exported)
            record["evidence_captures"][0]["capture"] = str(tail)
            save(exported, record)
            with self.assertRaisesRegex(ValueError, "escapes"):
                audit_exports([root / "export"])


if __name__ == "__main__":
    unittest.main()
