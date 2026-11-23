"""Regressions for page identity, cache policy and interrupted publication."""

import copy
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from truncator.planning.composition import capture_members
from truncator.planning.pages import resolve_page
from truncator.execution.device.runtime import latest_capture
from truncator.execution.device.capture_policy import CURRENT_CAPTURE_POLICY
from truncator.common.storage import read, save
from truncator.common.locking import lock
from truncator.review.datasets.dataset import export_dataset
from truncator.review.datasets.export_transaction import export_state_path
from truncator.review.review_evidence import record_review
from truncator.execution.curation import rebuild_reviewed
from truncator.review.review_evidence import capture_identity, validate_evidence
from tests.review import test_review_pipeline


class PageIdentityTests(unittest.TestCase):
    def fixture(self):
        recipe = {
            "settle_seconds": 8,
            "actions": [{"equals": "open", "wait": 2}],
            "checks": [{"equals": "target"}],
        }
        return {
            "mutations": [{"id": "a"}],
            "pages": [{"name": "detail", "recipe": recipe, "mutation_ids": ["a"]}],
        }

    def test_timing_changes_preserve_legacy_targets(self):
        plan = self.fixture()
        recipe = copy.deepcopy(plan["pages"][0]["recipe"])
        recipe.update(settle_seconds=9, image_check={"attempts": 3}, poll_interval=1)
        recipe["actions"][0]["wait"] = 4
        self.assertEqual(capture_members(plan, recipe), [{"id": "a"}])

    def test_navigation_changes_require_explicit_identity(self):
        plan = self.fixture()
        recipe = {"actions": [{"equals": "another path"}]}
        self.assertEqual(capture_members(plan, recipe), [])
        recipe["page_id"] = "detail"
        self.assertEqual(capture_members(plan, recipe), [{"id": "a"}])
        recipe["page_id"] = "typo"
        with self.assertRaisesRegex(ValueError, "Unknown page_id"):
            capture_members(plan, recipe)

    def test_ambiguous_fallback_requires_page_id(self):
        plan = self.fixture()
        second = copy.deepcopy(plan["pages"][0])
        second.update(name="other")
        second["recipe"]["settle_seconds"] = 10
        plan["pages"].append(second)
        recipe = {**second["recipe"], "settle_seconds": 12}
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            resolve_page(plan, recipe)
        self.assertEqual(
            resolve_page(plan, {**recipe, "page_id": "other"})["name"], "other"
        )

    def test_review_and_export_keep_the_executed_recipe(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, plan, run, review_file = (
                test_review_pipeline.ReviewPipelineTests().fixture(root)
            )
            review = read(review_file)
            page = plan["pages"][0]
            recipe = {**page["recipe"], "settle_seconds": 11, "page_id": page["name"]}
            capture = test_review_pipeline.capture_fixture(
                profile, run, "device-a", recipe, root
            )
            review["captures"][0] = capture_identity(run, page, capture)
            save(review_file, review)
            validate_evidence(run, plan, review)
            record_review(run, review_file)
            export_dataset(run, root / "export")
            recipes = [
                read(p)
                for p in (root / "export").glob("applications/*/paths/*/recipe.json")
            ]
            self.assertIn(recipe, recipes)
            with (
                patch(
                    "truncator.source.project.scan",
                    side_effect=test_review_pipeline.scan_fixture,
                ),
                patch(
                    "truncator.execution.workflow.build",
                    side_effect=test_review_pipeline.build_fixture,
                ),
                patch(
                    "truncator.execution.workflow.capture",
                    side_effect=test_review_pipeline.capture_fixture,
                ),
            ):
                result = rebuild_reviewed(
                    run, review_file, root / "rebuilt", "device-a"
                )
            self.assertEqual(result["status"], "captured")
            self.assertEqual(result["pages"][0]["recipe"], recipe)


class CachePolicyTests(unittest.TestCase):
    def test_unknown_old_and_current_policy_and_force(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = {"device": "d", "recipe": {}}
            save(root / "capture-1/capture.json", record)
            self.assertIsNone(latest_capture(root, "d", {}))
            record["capture_policy"] = {"rule_version": "old"}
            save(root / "capture-1/capture.json", record)
            self.assertIsNone(latest_capture(root, "d", {}))
            record["capture_policy"] = CURRENT_CAPTURE_POLICY
            save(root / "capture-1/capture.json", record)
            self.assertEqual(latest_capture(root, "d", {}), root / "capture-1")
            record["capture_policy"] = {
                **CURRENT_CAPTURE_POLICY,
                "implementation_sha256": "changed",
            }
            save(root / "capture-1/capture.json", record)
            self.assertIsNone(latest_capture(root, "d", {}))
            record["capture_policy"] = CURRENT_CAPTURE_POLICY
            save(root / "capture-1/capture.json", record)
            self.assertIsNone(latest_capture(root, "d", {}, force=True))
            self.assertIsNone(latest_capture(root, "d", {"settle_seconds": 1}))


class RecoveryTests(unittest.TestCase):
    def child(self, code, root):
        ready = root / "ready"
        process = subprocess.Popen(
            [sys.executable, "-c", code, str(root), str(ready)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.addCleanup(self.stop_child, process)
        deadline = time.monotonic() + 10
        while not ready.exists():
            if process.poll() is not None or time.monotonic() > deadline:
                self.stop_child(process)
                self.fail("Child did not reach protected operation")
            time.sleep(0.05)
        return process

    @staticmethod
    def stop_child(process):
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)

    def test_kernel_lock_excludes_live_child_and_recovers_after_kill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            process = self.child(
                "import sys,time; from pathlib import Path; from truncator.common.locking import lock\n"
                "with lock(Path(sys.argv[1])/'device.lock'):\n"
                " Path(sys.argv[2]).write_text('ready')\n time.sleep(60)\n",
                root,
            )
            with self.assertRaises(FileExistsError):
                with lock(root / "device.lock"):
                    pass
            self.stop_child(process)
            with lock(root / "device.lock"):
                pass
            self.assertEqual(read(root / "device.lock")["pid"], os.getpid())
            save(root / "legacy.lock", {"pid": process.pid, "time": 0})
            with lock(root / "legacy.lock"):
                pass
            save(root / "live-legacy.lock", {"pid": os.getpid(), "time": 0})
            with self.assertRaises(FileExistsError):
                with lock(root / "live-legacy.lock"):
                    pass

    def test_killed_export_does_not_publish_partial_directory_and_can_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "runs").mkdir()
            process = self.child(
                "import sys,time; from pathlib import Path; from truncator.review.datasets.export_transaction import export_transaction\n"
                "root=Path(sys.argv[1])\n"
                "with export_transaction(root/'runs',root/'export') as stage:\n"
                " (stage/'partial').write_text('interrupted')\n"
                " Path(sys.argv[2]).write_text('ready')\n time.sleep(60)\n",
                root,
            )
            state = read(export_state_path(root / "export"))
            self.assertFalse((root / "export").exists())
            with self.assertRaises(FileExistsError):
                export_dataset(root / "runs", root / "export")
            self.stop_child(process)
            self.assertEqual(export_dataset(root / "runs", root / "export"), 0)
            self.assertTrue(read(root / "export/export-status.json")["complete"])
            self.assertTrue((Path(state["staging"]) / "partial").exists())
            self.assertFalse((root / "export/partial").exists())

    def test_copy_failure_preserves_attempt_and_retry_exports_one_hap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, run, review = test_review_pipeline.ReviewPipelineTests().fixture(root)
            record_review(run, review)
            with patch(
                "truncator.review.datasets.delivery.shutil.copy2", side_effect=OSError("disk full")
            ):
                with self.assertRaisesRegex(OSError, "disk full"):
                    export_dataset(run, root / "export")
            self.assertFalse((root / "export").exists())
            state = read(export_state_path(root / "export"))
            self.assertEqual(state["status"], "failed")
            self.assertTrue(Path(state["staging"]).exists())
            self.assertEqual(export_dataset(run, root / "export"), 2)
            self.assertEqual(len(list((root / "export").rglob("*.hap"))), 1)
            with self.assertRaises(FileExistsError):
                export_dataset(run, root / "export")

    def test_legacy_incomplete_export_is_archived(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(root / "export/export-status.json", {"complete": False})
            (root / "export/partial").write_text("keep failed evidence")
            self.assertEqual(export_dataset(root / "runs", root / "export"), 0)
            archives = list(root.glob(".export.incomplete-*"))
            self.assertEqual(len(archives), 1)
            self.assertEqual(
                (archives[0] / "partial").read_text(), "keep failed evidence"
            )


if __name__ == "__main__":
    unittest.main()
