import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from truncator.execution.device.recovery import verify_scroll_members
from truncator.common.storage import read, save


class CombinedRecoveryTests(unittest.TestCase):
    def test_scroll_uses_planned_axis_and_continues_same_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, after = root / "first", root / "after"
            for folder in (first, after):
                save(folder / "tree-before.json", {})
                save(folder / "capture.json", {})
                save(folder / "replay.json", {})
            save(root / "plan.json", {"id": "plan", "operator": "scroll-recovery",
                "parameters": {"scroll_direction": "Vertical", "viewport_id": "viewport"},
                "geometry": {"mutated_selector": {"id": "target"}}})
            with patch("truncator.execution.device.runtime.capture", side_effect=[first, after]) as capture, \
                 patch("truncator.execution.device.recovery.plan_swipe", return_value={
                     "status": "planned", "from": [.5, .8], "to": [.5, .2]}) as gesture, \
                 patch("truncator.execution.device.recovery.measure_transition", return_value={"moved": True}):
                output = verify_scroll_members({}, root, first, "device", {"page_id": "home"}, max_swipes=1)
            self.assertEqual(gesture.call_args.args[-1], "vertical")
            self.assertNotIn("continue_from", capture.call_args_list[0].kwargs)
            self.assertEqual(capture.call_args_list[1].kwargs["continue_from"], first)
            record = read(output)
            self.assertEqual(record["members"][0]["status"], "measured")
            self.assertEqual(record["review"], "pending")

    def test_other_operators_do_not_trigger_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(root / "plan.json", {"id": "plan", "operator": "height-clip"})
            with patch("truncator.execution.device.runtime.capture") as capture:
                self.assertIsNone(verify_scroll_members({}, root, root, "device", {}))
            capture.assert_not_called()

    def test_stops_when_content_is_covered_or_scroll_does_not_progress(self):
        for measurement, reason in [
            ({"initial_and_current_cover_baseline_ink": True, "delta_along_axis_px": -631}, "coverage_observed"),
            ({"initial_and_current_cover_baseline_ink": False, "delta_along_axis_px": 0}, "no_forward_progress"),
        ]:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                first, after = root / "first", root / "after"
                for folder in (first, after):
                    for name in ("tree-before.json", "capture.json", "replay.json"):
                        save(folder / name, {})
                save(root / "plan.json", {"id": "plan", "operator": "scroll-recovery",
                    "parameters": {"scroll_direction": "Horizontal", "viewport_id": "viewport"},
                    "geometry": {"mutated_selector": {"id": "target"}}})
                with patch("truncator.execution.device.runtime.capture", side_effect=[first, after]) as capture, \
                     patch("truncator.execution.device.recovery.plan_swipe", return_value={
                         "status": "planned", "from": [.8, .5], "to": [.2, .5]}), \
                     patch("truncator.execution.device.recovery.measure_transition", return_value=measurement):
                    output = verify_scroll_members({}, root, first, "device", {"page_id": "home"})
                self.assertEqual(capture.call_count, 2)
                self.assertEqual(read(output)["members"][0]["stop_reason"], reason)
