import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.planning import test_composition
from truncator.planning.composition import compose, validate_plan
from truncator.review.review_policy import retained_plan, review_template
from truncator.review.review_evidence import record_review, recorded_review
from truncator.mutation.mutations import apply_patches
from truncator.source.project import prepare
from truncator.common.storage import save, digest, read
from truncator.review.reporting.review_ui import write_review
from truncator.review.review_evidence import capture_identity


class CurationTests(unittest.TestCase):
    def test_recorded_review_is_bound_to_package_and_captured_screenshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, plan, _ = self.fixture(root)
            run = root / "run"
            (run / "project").mkdir(parents=True)
            (run / "project/app.hap").write_bytes(b"package")
            checksum = digest(b"package")
            save(run / "plan.json", plan)
            save(run / "profile.json", {"hap": "app.hap"})
            save(run / "build.json", {"hap_sha256": checksum})
            review = review_template(plan, checksum)
            save(root / "review.json", review)
            with self.assertRaisesRegex(ValueError, "exact capture evidence"):
                record_review(run, root / "review.json")
            capture = run / "capture-1"
            capture.mkdir()
            (capture / "snapshot.jpeg").write_bytes(b"image")
            save(
                capture / "capture.json",
                {"recipe": {}, "screenshot_sha256": digest(b"image")},
            )
            save(capture / "tree-before.json", {})
            save(capture / "tree-after.json", {})
            review = review_template(
                plan, checksum, [capture_identity(run, plan["pages"][0], capture)]
            )
            save(root / "review.json", review)
            path = record_review(run, root / "review.json")
            self.assertEqual(recorded_review(run), read(path))
            self.assertEqual(
                recorded_review(run)["captures"][0]["files"]["snapshot.jpeg"],
                digest(b"image"),
            )
            (capture / "snapshot.jpeg").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "screenshot changed"):
                record_review(run, root / "review.json")

    def fixture(self, root):
        source, candidates, pages = test_composition.CompositionTests().fixture(root)
        plan = compose([candidates[0], candidates[4]], pages, {})
        return source, plan, review_template(plan, "package-hash")

    def test_remove_one_preserves_other_patch_and_notes_do_not_affect_build(self):
        with tempfile.TemporaryDirectory() as directory:
            source, plan, review = self.fixture(Path(directory))
            first, second = [m["id"] for m in plan["mutations"]]
            review["decisions"][first]["decision"] = "remove"
            curated = retained_plan(plan, review, "package-hash")
            self.assertEqual([m["id"] for m in curated["mutations"]], [second])
            self.assertEqual(curated["mutations"][0], plan["mutations"][1])
            updated = apply_patches(source, curated["patches"])
            self.assertIn("Text('first')\n", updated)
            self.assertIn("Text('second').width(80)", updated)
            review["decisions"][second].update(
                decision="keep", note="remove everything <script>"
            )
            self.assertEqual(curated, retained_plan(plan, review, "package-hash"))
            validate_plan(plan)
            validate_plan(curated)

    def test_review_version_ids_and_decisions_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            _, plan, original = self.fixture(Path(directory))
            for field in ["plan_id", "hap_sha256", "schema_version"]:
                review = {**original, field: "wrong"}
                with self.assertRaises(ValueError):
                    retained_plan(plan, review, "package-hash")
            review = copy.deepcopy(original)
            review["decisions"]["unknown"] = {"decision": "remove"}
            with self.assertRaises(ValueError):
                retained_plan(plan, review, "package-hash")
            review = copy.deepcopy(original)
            next(iter(review["decisions"].values()))["decision"] = "guess"
            with self.assertRaises(ValueError):
                retained_plan(plan, review, "package-hash")

    def test_remove_all_prepares_normal_source_in_new_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = root / "source"
            source_root.mkdir()
            source, plan, review = self.fixture(source_root)
            (source_root / "Index.ets").write_text(source, encoding="utf-8")
            for item in review["decisions"].values():
                item["decision"] = "remove"
            curated = retained_plan(plan, review, "package-hash")
            with patch(
                "truncator.source.project.scan", return_value={"files": {}, "diagnostics": []}
            ):
                prepare({"source": str(source_root)}, root / "new", curated)
            self.assertEqual((root / "new/project/Index.ets").read_text(), source)
            self.assertEqual(curated["patches"], [])

    def test_review_html_has_one_control_per_defect_and_escaped_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, plan, _ = self.fixture(root)
            plan["mutations"][0]["site"]["file"] = "<script>test</script>"
            write_review(root, plan, {"hap_sha256": "package-hash"}, root, [])
            page = (root / "review.html").read_text(encoding="utf-8")
            self.assertEqual(page.count("data-mutation="), 2)
            self.assertIn("&lt;script&gt;test&lt;/script&gt;", page)
            self.assertEqual(len(read(root / "review-template.json")["decisions"]), 2)


if __name__ == "__main__":
    unittest.main()
