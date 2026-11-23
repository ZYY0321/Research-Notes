"""Multi-batch exports and successive human-reviewed rebuilds share explicit ancestry."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.review import test_review_pipeline as fixtures
from truncator.common.storage import read, save
from truncator.execution.curation import rebuild_reviewed
from truncator.review.review_evidence import record_review, capture_identity
from truncator.review.review_policy import review_template
from truncator.review.datasets.dataset import export_dataset
from truncator.review.datasets.dataset_balance import audit_exports
from truncator.review.datasets.dataset_revisions import select_revisions


class DatasetRevisionTests(unittest.TestCase):
    def test_two_rebuilds_export_review_history_and_count_latest_even_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, plan, original, review_file = fixtures.ReviewPipelineTests().fixture(root)
            record_review(original, review_file)
            export_dataset(original, root / "batch-original")
            current, submitted = original, read(review_file)
            exports = [root / "batch-original"]
            for index in range(2):
                selected = next(iter(submitted["decisions"]))
                submitted["decisions"][selected].update(decision="remove", note="Visual review: remove this target")
                submitted["reviewer"] = "fixture-reviewer"
                save(review_file, submitted)
                output = root / ("rebuild-" + str(index))
                with (patch("truncator.source.project.scan", side_effect=fixtures.scan_fixture),
                      patch("truncator.execution.workflow.build", side_effect=fixtures.build_fixture),
                      patch("truncator.execution.workflow.capture", side_effect=fixtures.capture_fixture),
                      patch("truncator.review.reporting.evidence.generate_report")):
                    result = rebuild_reviewed(current, review_file, output, "device-a")
                current = next((output / "mutations").glob("*/plan.json")).parent
                new_plan = read(current / "plan.json")
                self.assertEqual(len(new_plan["curation"]["ancestors"]), index + 1)
                captures = [capture_identity(current, page, page["cases"][0]["runs"][0]["assessment"]["capture"])
                            for page in result["pages"]]
                submitted = review_template(new_plan, read(current / "build.json")["hap_sha256"], captures)
                for item in submitted["decisions"].values():
                    item.update(decision="keep", content_status="clipped", recovery_status="not-recovered")
                save(review_file, submitted)
                record_review(current, review_file)
                destination = root / ("batch-rebuilt-" + str(index))
                export_dataset(output, destination)
                exports.append(destination)
                histories = list(destination.glob("applications/*/curation-history/*.json"))
                self.assertEqual(len(histories), index + 1)
                self.assertEqual(read(histories[0])["review"]["reviewer"], "fixture-reviewer")
            latest = audit_exports(exports)
            self.assertEqual(latest["counts"]["mechanism"], {})
            self.assertEqual(len(latest["revisions"]["latest_versions"]), 1)
            self.assertEqual(len(latest["revisions"]["superseded_versions"]), 2)
            history = audit_exports(exports, revisions="all")
            self.assertTrue(history["units"])
            self.assertEqual(history, audit_exports(list(reversed(exports)), revisions="all"))
            repeated = audit_exports(exports + [exports[0]], revisions="all")
            self.assertEqual(history["counts"], repeated["counts"])
            exported_plan = next(exports[-1].glob("applications/*/paths/*/mutated/plan.json"))
            original_bytes = exported_plan.read_bytes()
            save(exported_plan, plan)
            with self.assertRaisesRegex(ValueError, "bound package review"):
                audit_exports(exports)
            exported_plan.write_bytes(original_bytes)
            entry = next((current / "curation-history").glob("*.json"))
            original_entry = entry.read_bytes()
            entry.unlink()
            with self.assertRaisesRegex(ValueError, "history is incomplete"):
                export_dataset(current, root / "missing-history-export")
            entry.write_bytes(original_entry)
            changed = read(entry)
            # Both IDs exist in the chain, but an ancestor may not point to itself.
            changed["child_plan_id"] = changed["parent_plan_id"]
            save(entry, changed)
            with self.assertRaisesRegex(ValueError, "adjacent rebuild"):
                export_dataset(current, root / "wrong-edge-export")
            entry.write_bytes(original_entry)
            changed = read(entry)
            changed["review"]["reviewer"] = "modified after review"
            save(entry, changed)
            with self.assertRaisesRegex(ValueError, "history changed"):
                export_dataset(current, root / "tampered-export")

    def test_parallel_rebuilds_are_reported_without_choosing_by_time(self):
        versions = {key: {"key": key, "ancestors": ancestors}
                    for key, ancestors in (("old", []), ("a", ["old"]), ("b", ["old"]), ("unrelated", []))}
        units = [{"revision": key, "consensus": "consistent", "export": key, "sample": key, "mutation": key}
                 for key in versions]
        selected, report = select_revisions(units, versions, "latest")
        self.assertEqual({u["revision"] for u in selected}, {"a", "b", "unrelated"})
        self.assertEqual(report["branches"], {"old": ["a", "b"]})

    def test_conflicting_child_does_not_replace_its_reviewed_parent(self):
        units = [{"revision": key, "consensus": status} for key, status in (("old", "consistent"), ("new", "conflicting"))]
        selected, report = select_revisions(units, {"old": {"ancestors": []}, "new": {"ancestors": ["old"]}}, "latest")
        self.assertEqual(selected, units)
        self.assertEqual(report["superseded_versions"], [])
