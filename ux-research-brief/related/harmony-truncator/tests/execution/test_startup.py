import tempfile
import unittest
from pathlib import Path
from truncator.execution.device.startup import start_application, retry_exited_application
from truncator.common.storage import read


class StartupTests(unittest.TestCase):
    def test_late_relaunch_keeps_total_budget_and_does_not_restart_live_process(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []
            pids = iter(["123", "123", "", "456"])

            def hdc(*args):
                calls.append(args)
                return next(pids) if "pidof" in args else "success"

            profile = {"bundle": "fixture"}
            start_application(profile, {}, hdc, root, sleep=lambda _: None)
            self.assertFalse(retry_exited_application(profile, {}, hdc, root, sleep=lambda _: None))
            self.assertTrue(retry_exited_application(profile, {}, hdc, root, sleep=lambda _: None))
            self.assertFalse(retry_exited_application(profile, {}, hdc, root, sleep=lambda _: None))
            self.assertEqual(sum("start" in c for c in calls), 2)

    def test_relaunch_only_before_actions_and_preserves_reset_log(self):
        calls = []
        pids = iter(["", "123"])

        def hdc(*args):
            calls.append(args)
            if "pidof" in args:
                return next(pids)
            return "success"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            start_application(
                {"bundle": "fixture"},
                {"reset_app_data": True},
                hdc,
                root,
                sleep=lambda _: None,
            )
            self.assertEqual(sum("clean" in c for c in calls), 1)
            self.assertEqual(sum("start" in c for c in calls), 2)
            self.assertEqual(
                [
                    r["process_running"]
                    for r in read(root / "initial-state.json")["launches"]
                ],
                [False, True],
            )

    def test_failed_launch_and_reset_are_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "process exited"):
                start_application(
                    {"bundle": "fixture"},
                    {},
                    lambda *args: "",
                    Path(directory),
                    sleep=lambda _: None,
                )
            with self.assertRaisesRegex(RuntimeError, "reset failed"):
                start_application(
                    {"bundle": "fixture"},
                    {"reset_app_data": True},
                    lambda *args: "error",
                    Path(directory),
                    sleep=lambda _: None,
                )
