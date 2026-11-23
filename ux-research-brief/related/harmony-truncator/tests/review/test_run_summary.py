import tempfile
import unittest
from pathlib import Path
from truncator.common.storage import save
from truncator.review.reporting.run_summary import summarize_runs


class RunSummaryTests(unittest.TestCase):
    def test_campaign_can_be_summarized_before_its_first_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save(root / "campaign.json", {"applications": [{"profile": "app", "recipe": "home.json"}]})
            result = summarize_runs([root])
            self.assertEqual(result["application_status"], {"not-started": 1})
            self.assertEqual(result["page_status"], {"not-started": 1})

    def test_multiple_batches_include_failed_and_unstarted_apps_and_deduplicate_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for batch in ("a", "b"):
                save(root / batch / "campaign.json", {"applications": [
                    {"profile": "app", "pages": [{"name": "home"}, {"name": "detail"}]},
                    {"profile": "not-started", "pages": [{"name": "home"}]}]})
            run = root / "package"
            save(run / "plan.json", {"id": "p", "mutations": [{"id": "m"}]})
            save(run / "build.json", {"hap_sha256": "hap"})
            pages = [{"name": name, "status": "captured", "mutation_ids": ["m"],
                      "cases": [{"runs": [{"run": str(run)}]}]} for name in ("home", "detail")]
            save(root / "a/results.json", [{"application": "app", "status": "captured", "pages": pages}])
            save(root / "b/results.json", [{"application": "app", "status": "failed", "error": "source scan failed", "pages": []}])
            result = summarize_runs([root / "a", root / "b", root / "a"])
            self.assertEqual(result["application_status"], {"captured": 1, "not-started": 2, "failed": 1})
            self.assertEqual(result["page_status"], {"captured": 2, "not-started": 4})
            self.assertEqual(result["planned_targets"], 1)
            self.assertEqual(result["unique_package_runs"], 1)
