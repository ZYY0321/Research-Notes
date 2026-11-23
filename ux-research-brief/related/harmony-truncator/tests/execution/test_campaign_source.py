import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from truncator.execution.campaign_source import prepare_application
from truncator.common.storage import read


class CampaignSourceTests(unittest.TestCase):
    def test_instrumented_source_is_selected_once_and_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = {"source": "original"}
            traced = {"source": "instrumented", "instrumentation": "map.json"}
            with patch("truncator.execution.campaign_source.instrument", return_value=traced) as instrument, \
                 patch("truncator.execution.campaign_source.prepare_baseline") as prepare, \
                 patch("truncator.execution.campaign_source.scan", return_value={"files": {"a": "sha"}}):
                first = prepare_application(profile, {}, root)
                second = prepare_application(profile, {}, root)
            self.assertEqual(first, second)
            self.assertEqual(first[0], traced)
            instrument.assert_called_once()
            self.assertTrue(all(call.args[0] == traced for call in prepare.call_args_list))
            self.assertEqual(read(root / "source-choice.json")["mode"], "instrumented")

    def test_instrumented_build_failure_falls_back_to_separate_original_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = {"source": "original"}
            traced = {"source": "instrumented"}
            def build(candidate, baseline):
                if candidate == traced:
                    raise RuntimeError("Instrumented compilation rejected")
            with patch("truncator.execution.campaign_source.instrument", return_value=traced), \
                 patch("truncator.execution.campaign_source.prepare_baseline", side_effect=build) as prepare, \
                 patch("truncator.execution.campaign_source.scan", return_value={"files": {}}):
                selected, _, baseline = prepare_application(profile, {}, root)
            self.assertEqual(selected, profile)
            self.assertEqual(baseline, root / "baseline-original")
            self.assertNotEqual(prepare.call_args_list[0].args[1], baseline)
            state = read(root / "source-choice.json")
            self.assertEqual(state["mode"], "original-fallback")
            self.assertIn("compilation", state["fallback"]["error"])

    def test_existing_baseline_retains_source_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("truncator.execution.campaign_source.instrument") as instrument, \
                 patch("truncator.execution.campaign_source.prepare_baseline"), \
                 patch("truncator.execution.campaign_source.scan", return_value={"files": {}}):
                selected, _, baseline = prepare_application(
                    {"source": "original"}, {"baseline_run": "existing"}, Path(directory))
            instrument.assert_not_called()
            self.assertEqual(baseline, Path("existing"))
