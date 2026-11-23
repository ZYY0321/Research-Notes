import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from truncator.common.storage import save, read, digest
from truncator.execution.workflow import batch
from truncator.review.datasets.dataset import export_dataset
from truncator.execution.campaign import campaign, save_campaign_results
from truncator.execution.device.runtime import latest_capture
from truncator.review.diagnostics import assess_capture
from truncator.execution.device.capture_policy import CURRENT_CAPTURE_POLICY
from truncator.review.datasets.export_transaction import export_state_path


class WorkflowTests(unittest.TestCase):

    def test_campaign_review_queue_accumulates_all_applications_and_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results = [
                {"cases": [{"runs": [{"run": "one"}]}, {"status": "skipped"}]},
                {"cases": [{"runs": [{"run": "two"}]}]},
            ]
            save_campaign_results(root, results)
            self.assertEqual(
                [
                    row["run"]
                    for row in read(root / "review-queue.json")["applications"]
                ],
                ["one", "two"],
            )


    def test_batch_keeps_all_haps_for_post_batch_review_without_ranking(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "sample"
            profile = {"source": "original", "hap": "output.hap", "bundle": "fixture"}
            plan = {"id": "sample"}
            save(root / "plan.json", plan)
            save(run / "plan.json", plan)
            save(run / "profile.json", profile)
            save(run / "prepared.json", {})
            (run / "project").mkdir()
            (run / "project/output.hap").write_bytes(b"app")
            save(run / "build.json", {"hap_sha256": digest(b"app")})
            save(run / "capture-1/capture.json", {"device": "device", "recipe": {}, "capture_policy": CURRENT_CAPTURE_POLICY})
            save(
                run / "capture-1/diagnostics.json",
                {"flags": ["geometry_not_triggered"]},
            )
            with patch(
                "truncator.review.diagnostics.select_candidate",
                side_effect=AssertionError("Unexpected feedback"),
            ):
                result = batch(profile, [root / "plan.json"], root, "device", {})
            self.assertEqual(result[0]["status"], "captured")
            self.assertEqual(
                result[0]["assessment"]["next_action"], "post_batch_review"
            )
            self.assertTrue(Path(result[0]["application"]["hap"]).exists())
            self.assertFalse((root / "candidate-selection.json").exists())
            self.assertEqual(len(read(root / "review-queue.json")["applications"]), 1)

    def test_capture_reuse_matches_device_recipe_and_completed_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recipe = {"checks": [{"equals": "target"}]}
            save(
                root / "capture-1/capture.json",
                {"device": "device-a", "recipe": recipe, "capture_policy": CURRENT_CAPTURE_POLICY},
            )
            save(
                root / "capture-2/capture.json",
                {"device": "device-b", "recipe": recipe, "capture_policy": CURRENT_CAPTURE_POLICY},
            )
            save(root / "capture-3/capture.json", {"device": "device-a", "recipe": {}})
            save(root / "capture-4/failure.json", {"error": "incomplete"})
            self.assertEqual(
                latest_capture(root, "device-a", recipe), root / "capture-1"
            )
            self.assertIsNone(latest_capture(root, "missing-device", recipe))

    def test_assessment_preserves_failure_and_quality_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIsNone(assess_capture(root))
            save(root / "diagnostics.json", {"flags": ["geometry_not_triggered"]})
            self.assertEqual(assess_capture(root)["next_action"], "try_other_candidate")
            save(root / "image-quality.json", {"passed": False})
            self.assertEqual(
                assess_capture(root)["next_action"], "inspect_non_target_changes"
            )


    def test_nested_export_copies_verified_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = root / "runs/app-1/mutations/sample/capture-1"
            baseline = root / "baseline"
            for folder in [capture, baseline]:
                folder.mkdir(parents=True)
                (folder / "snapshot.jpeg").write_bytes(b"fixture-image")
                for name in ["tree-before.json", "tree-after.json", "capture.json"]:
                    save(folder / name, {})
            save(capture / "capture.json", {"screenshot_sha256": digest(b"fixture-image")})
            from truncator.review.review_evidence import capture_hashes
            save(
                capture / "review-1.json",
                {
                    "decision": "accepted",
                    "reviewer": "fixture",
                    "capture_files": capture_hashes(capture),
                    "screenshot_sha256": digest(b"fixture-image"),
                },
            )
            save(capture.parent / "profile.json", {"bundle": "fixture.app"})
            save(
                capture.parent / "plan.json",
                {
                    "operator": "height-clip",
                    "site": {"file": "Index.ets", "component": "Text"},
                    "geometry": {
                        "baseline_capture": str(baseline),
                        "baseline_image_sha256": digest(b"fixture-image"),
                        "baseline_tree_sha256": digest(
                            (baseline / "tree-before.json").read_bytes()
                        ),
                    },
                },
            )
            self.assertEqual(export_dataset(root / "runs", root / "export"), 1)
            self.assertTrue((root / "export/balance.json").exists())
            sample = read(root / "export/manifest.json")["samples"][0]
            self.assertNotIn("case_review", sample)
            self.assertTrue(all("production_basis" not in m for m in sample["mutations"]))
            self.assertEqual(sample["split_group"], "fixture.app/Index.ets")
            self.assertTrue(
                (root / "export" / sample["id"] / "baseline/tree-before.json").exists()
            )

    def test_resume_does_not_rebuild_completed_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "abc"
            run.mkdir()
            profile = {"source": "original"}
            plan = {"id": "abc"}
            save(root / "plan.json", plan)
            save(run / "plan.json", plan)
            save(run / "profile.json", profile)
            save(run / "prepared.json", {})
            save(run / "build.json", {})
            with patch("truncator.execution.workflow.build") as mocked:
                report = batch(profile, [root / "plan.json"], root)
                mocked.assert_not_called()
            self.assertEqual(report[0]["status"], "built")
            altered = batch({"source": "different"}, [root / "plan.json"], root)
            self.assertEqual(altered[0]["status"], "failed")

    def test_pending_samples_are_not_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = root / "runs/app/capture-1"
            save(capture / "capture.json", {})
            self.assertEqual(export_dataset(root / "runs", root / "export"), 0)
            self.assertTrue(read(root / "export/export-status.json")["complete"])

    def test_missing_evidence_fails_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = root / "runs/app/capture-1"
            save(capture / "capture.json", {})
            save(capture / "review-1.json", {"decision": "accepted"})
            with self.assertRaises(ValueError):
                export_dataset(root / "runs", root / "export")
            self.assertFalse((root / "export").exists())
            self.assertFalse(read(export_state_path(root / "export"))["complete"])
