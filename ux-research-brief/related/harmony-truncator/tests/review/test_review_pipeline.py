"""Offline regressions for exact review binding, resumable curation and export."""

import copy
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.planning import test_composition
from truncator.planning.composition import compose
from truncator.review.review_policy import review_template
from truncator.review.review_evidence import record_review
from truncator.execution.curation import rebuild_reviewed
from truncator.review.review_evidence import capture_identity, validate_evidence
from truncator.review.datasets.dataset import export_dataset
from truncator.source.project import prepare
from truncator.common.storage import save, read, digest
from truncator.execution.workflow import batch
from truncator.execution.device.capture_policy import CURRENT_CAPTURE_POLICY


def scan_fixture(profile):
    path = Path(profile["source"]) / "Index.ets"
    return {"files": {"Index.ets": digest(path.read_bytes())}, "diagnostics": []}


def build_fixture(profile, run):
    (run / "project/app.hap").write_bytes((run / "project/Index.ets").read_bytes())
    save(
        run / "build.json",
        {"hap_sha256": digest((run / "project/app.hap").read_bytes())},
    )


def capture_fixture(profile, run, device, recipe, output):
    index = len(list(run.glob("capture-*")))
    folder = run / ("capture-%03d" % index)
    folder.mkdir()
    shutil.copy2(Path(profile["source"]) / "snapshot.jpeg", folder / "snapshot.jpeg")
    for name in ("tree-before.json", "tree-after.json"):
        save(folder / name, {})
    save(
        folder / "capture.json",
        {
            "recipe": recipe,
            "capture_policy": CURRENT_CAPTURE_POLICY,
            "device": device,
            "screenshot_sha256": digest((folder / "snapshot.jpeg").read_bytes()),
            "hap_sha256": read(run / "build.json")["hap_sha256"],
        },
    )
    return folder


class ReviewPipelineTests(unittest.TestCase):
    def test_partial_preparation_is_archived_and_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, plan, _, _ = self.fixture(root)
            plan_file = root / "plan.json"
            save(plan_file, plan)
            output = root / "runs"
            partial = output / plan["id"]
            save(partial / "profile.json", profile)
            (partial / "partial.txt").write_text("interrupted copy")
            with (
                patch("truncator.source.project.scan", side_effect=scan_fixture),
                patch("truncator.execution.workflow.build", side_effect=build_fixture),
            ):
                result = batch(profile, [plan_file], output)
            self.assertEqual(result[0]["status"], "built")
            archives = list(output.glob("incomplete-*"))
            self.assertEqual(len(archives), 1)
            self.assertEqual(
                (archives[0] / "partial.txt").read_text(), "interrupted copy"
            )
            self.assertTrue((partial / "prepared.json").exists())

    def fixture(self, root):
        source_root = root / "source"
        source_root.mkdir()
        source, candidates, pages = test_composition.CompositionTests().fixture(
            source_root
        )
        (source_root / "Index.ets").write_bytes(source.encode())
        save(source_root / "tree-after.json", {})
        pages.append({**pages[0], "name": "second", "recipe": {"checks": []}})
        plan = compose([candidates[0], candidates[4]], pages, {})
        profile = {"source": str(source_root), "hap": "app.hap"}
        run = root / "original"
        with patch("truncator.source.project.scan", side_effect=scan_fixture):
            prepare(profile, run, plan)
        build_fixture(profile, run)
        captures = [
            capture_identity(
                run, p, capture_fixture(profile, run, "device-a", p["recipe"], root)
            )
            for p in pages
        ]
        review = review_template(plan, read(run / "build.json")["hap_sha256"], captures)
        for item in review["decisions"].values():
            item["decision"] = "keep"
        filename = root / "review.json"
        save(filename, review)
        return profile, plan, run, filename

    def test_later_capture_on_another_device_does_not_rebind_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, plan, run, filename = self.fixture(root)
            original = read(filename)["captures"]
            capture_fixture(profile, run, "device-b", plan["pages"][0]["recipe"], root)
            saved = read(record_review(run, filename))
            self.assertEqual(saved["captures"], original)
            self.assertEqual(saved["captures"][0]["device"], "device-a")

    def test_report_includes_supplementary_interaction_capture(self):
        from truncator.review.reporting.evidence import generate_report
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, plan, run, _ = self.fixture(root)
            extra = capture_fixture(profile, run, "device-a", {"actions": [{"wait": 1}]}, root)
            results = [{"application": "fixture", "pages": [
                {"name": page["name"], "recipe": page["recipe"], "cases": [{"runs": [
                    {"run": str(run), "plan": str(run / "plan.json"), "status": "captured"}]}]}
                for page in plan["pages"]]}]
            generate_report(root, results)
            report = root / "report/applications" / plan["id"] / "checks" / extra.name
            self.assertTrue((report / "snapshot.jpeg").exists())
            self.assertIn('src="snapshot.jpeg"', (report / "index.html").read_text(encoding="utf-8"))

    def test_tree_changes_missing_evidence_and_path_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, plan, run, filename = self.fixture(root)
            review = read(filename)
            changed = copy.deepcopy(review)
            changed["captures"][0]["capture_id"] = "../original"
            with self.assertRaises(ValueError):
                validate_evidence(run, plan, changed)
            changed = copy.deepcopy(review)
            changed["captures"] = changed["captures"][:1]
            with self.assertRaises(ValueError):
                validate_evidence(run, plan, changed)
            save(
                run / review["captures"][0]["capture_id"] / "tree-after.json",
                {"changed": True},
            )
            with self.assertRaisesRegex(ValueError, "evidence changed"):
                record_review(run, filename)

    def test_resume_reuses_build_and_completed_capture_then_exports_one_hap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, plan, run, filename = self.fixture(root)
            calls = []

            def interrupted_capture(*args):
                calls.append(args[3])
                if len(calls) == 2:
                    raise KeyboardInterrupt("simulated interruption")
                return capture_fixture(*args)

            with (
                patch("truncator.source.project.scan", side_effect=scan_fixture),
                patch("truncator.execution.workflow.build", side_effect=build_fixture) as builder,
                patch("truncator.execution.workflow.capture", side_effect=interrupted_capture),
                patch("truncator.review.reporting.evidence.generate_report"),
            ):
                with self.assertRaises(KeyboardInterrupt):
                    rebuild_reviewed(run, filename, root / "curated", "device-a")
                from truncator.review.reporting.run_summary import summarize_runs
                interrupted = summarize_runs([root / "curated"])
                self.assertEqual(interrupted["configured_page_attempts"], 2)
                self.assertEqual(interrupted["page_status"], {"captured": 1, "not-started": 1})
                self.assertEqual(interrupted["unique_package_runs"], 1)
                self.assertEqual(len(list((root / "curated/mutations").glob("*/curation-history/*.json"))), 1)
                result = rebuild_reviewed(run, filename, root / "curated", "device-a")
                self.assertEqual(result["status"], "captured")
                self.assertEqual(builder.call_count, 1)
                self.assertEqual(len(calls), 3)
                again = rebuild_reviewed(run, filename, root / "curated", "device-a")
                self.assertEqual(again["status"], "captured")
                self.assertEqual(len(calls), 3)
                with self.assertRaisesRegex(ValueError, "Resume inputs"):
                    rebuild_reviewed(run, filename, root / "curated", "device-b")
            final_run = next(
                path.parent for path in (root / "curated/mutations").glob("*/plan.json")
            )
            final_plan = read(final_run / "plan.json")
            identities = [
                capture_identity(
                    final_run,
                    page,
                    page["cases"][0]["runs"][0]["assessment"]["capture"],
                )
                for page in result["pages"]
            ]
            review = review_template(
                final_plan, read(final_run / "build.json")["hap_sha256"], identities
            )
            for item in review["decisions"].values():
                item["decision"] = "keep"
            save(root / "final-review.json", review)
            record_review(final_run, root / "final-review.json")
            self.assertEqual(export_dataset(root / "curated", root / "export"), 2)
            exported = read(root / "export/manifest.json")
            self.assertEqual(len(exported["applications"]), 1)
            self.assertEqual(len(list((root / "export").rglob("*.hap"))), 1)
            self.assertTrue(
                (root / "export" / exported["applications"][0]["hap"]).exists()
            )

    def test_failed_rebuild_is_not_retried_for_each_configured_page(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, run, filename = self.fixture(root)
            with (patch("truncator.source.project.scan", side_effect=scan_fixture),
                  patch("truncator.execution.workflow.build", side_effect=RuntimeError("compile failed")) as builder,
                  patch("truncator.execution.workflow.capture") as capture,
                  patch("truncator.review.reporting.evidence.generate_report")):
                result = rebuild_reviewed(run, filename, root / "curated", "device-a")
            self.assertEqual(builder.call_count, 1)
            capture.assert_not_called()
            self.assertEqual([page["status"] for page in result["pages"]], ["failed", "failed"])
            self.assertEqual(result["status"], "failed")

    def test_pending_review_prevents_final_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, run, filename = self.fixture(root)
            review = read(filename)
            next(iter(review["decisions"].values()))["decision"] = "pending"
            save(filename, review)
            record_review(run, filename)
            with self.assertRaisesRegex(ValueError, "pending defects"):
                export_dataset(run, root / "export")
