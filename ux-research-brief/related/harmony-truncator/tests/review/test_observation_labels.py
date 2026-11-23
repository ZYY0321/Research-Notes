import tempfile
import unittest
from pathlib import Path

from PIL import Image

from truncator.review.review_policy import validate_observation_labels
from truncator.common.storage import digest, read, save
from truncator.execution.workflow import review
from truncator.review.datasets.dataset import export_dataset


class ObservationLabelTests(unittest.TestCase):
    def test_labels_are_explicit_and_old_reviews_remain_valid(self):
        validate_observation_labels(None, None)
        validate_observation_labels("clipped", "recovered")
        validate_observation_labels("complete", "not-applicable")
        for values in (("complete", None), (None, "recovered"), ("complete", "recovered")):
            with self.assertRaises(ValueError):
                validate_observation_labels(*values)

    def test_review_and_export_preserve_negative_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "run"
            capture = run / "capture-001"
            capture.mkdir(parents=True)
            Image.new("RGB", (100, 50), "white").save(capture / "snapshot.jpeg")
            save(capture / "capture.json", {
                "screenshot_sha256": digest((capture / "snapshot.jpeg").read_bytes()),
                "recipe": {},
                "hap_sha256": "same-package",
            })
            save(run / "profile.json", {"bundle": "test"})
            for name in ("tree-before.json", "tree-after.json"):
                save(capture / name, {})
            path = review(capture, "accepted", "test-reviewer", "Complete text in target region",
                          [[0, 0, 100, 50]], content_status="complete", recovery_status="not-applicable")
            self.assertEqual(read(path)["content_status"], "complete")
            export_dataset(run, root / "export")
            sample = read(root / "export/manifest.json")["samples"][0]
            self.assertEqual(sample["content_status"], "complete")
            self.assertEqual(sample["recovery_status"], "not-applicable")

    def test_additional_evidence_is_verified_and_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "run"
            save(run / "profile.json", {"bundle": "test"})
            captures = []
            for index in range(2):
                cap = run / ("capture-" + str(index))
                cap.mkdir()
                Image.new("RGB", (30, 20), "white").save(cap / "snapshot.jpeg")
                save(cap / "capture.json", {"hap_sha256": "same-package", "recipe": {},
                     "screenshot_sha256": digest((cap / "snapshot.jpeg").read_bytes())})
                for name in ("tree-before.json", "tree-after.json"):
                    save(cap / name, {})
                captures.append(cap)
            review(captures[0], "accepted", "test", "Tail recovered", [],
                   content_status="clipped", recovery_status="recovered", evidence_captures=[captures[1]])
            export_dataset(run, root / "export")
            exported = next((root / "export").glob("*/review.json"))
            extra = read(exported)["evidence_captures"][0]
            self.assertFalse(Path(extra["capture"]).is_absolute())
            self.assertTrue((exported.parent / extra["capture"] / "tree-before.json").exists())
            save(captures[1] / "tree-before.json", {"changed": True})
            with self.assertRaisesRegex(ValueError, "evidence changed"):
                export_dataset(run, root / "changed-export")
