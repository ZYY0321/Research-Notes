"""A continuation must never silently restart or reuse a different process."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from truncator.execution.device.runtime import capture, latest_capture
from truncator.common.storage import read, save, digest


class ContinuousCaptureTests(unittest.TestCase):
    def test_live_capture_validates_identity_and_does_not_install_or_restart(self):
        calls = []
        process_start = 100
        restart_during_acquisition = False
        tree = {"attributes": {"id": "page", "type": "Text", "text": "state"}}

        def command(args, log, **kwargs):
            calls.append(args)
            if "pidof" in args:
                result = "123"
            elif args[-1] == "/proc/123/stat":
                result = "123 (name with ) spaces) S " + "0 " * 18 + str(process_start)
            elif "dumpLayout" in args:
                result = "DumpLayout saved"
            elif "cat" in args:
                result = json.dumps(tree)
            elif "clean" in args:
                result = "success"
            elif "hidumper" in args:
                result = "DisplayFoldStatus: EXPAND\nVirtualPixelRatio: 1\n[DISPLAY INFO]\nWidth: 100\nHeight: 100\n"
            else:
                result = ""
            return result, {"returncode": 0, "seconds": 0}

        def acquire(folder, *args):
            nonlocal process_start
            Image.new("RGB", (100, 100), "white").save(folder / "snapshot.jpeg")
            save(folder / "tree-before.json", tree)
            save(folder / "tree-after.json", tree)
            if restart_during_acquisition:
                process_start += 1
            return tree, tree

        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            profile = {"hdc": "mock", "bundle": "fixture", "hap": "app.hap"}
            save(run / "profile.json", profile)
            save(run / "build.json", {"hap_sha256": digest(b"hap")})
            (run / "project").mkdir()
            (run / "project/app.hap").write_bytes(b"hap")
            recipe = {
                "settle_seconds": 0,
                "checks": [{"field": "id", "equals": "page"}],
            }
            with patch("truncator.execution.device.runtime.command", command), patch(
                "truncator.execution.device.acquisition.acquire", acquire
            ):
                initial = capture(profile, run, "device", recipe, run)
                self.assertEqual(
                    read(initial / "capture.json")["session"]["process"]["start_ticks"],
                    100,
                )
                calls.clear()
                continued = capture(
                    profile, run, "device", recipe, run, continue_from=initial
                )
                self.assertFalse(
                    any(
                        set(args) & {"install", "start", "force-stop", "clean"}
                        for args in calls
                    )
                )
                record = read(continued / "capture.json")
                self.assertEqual(record["continued_from"]["capture"], str(initial))
                self.assertEqual(latest_capture(run, "device", recipe), initial)
                with self.assertRaisesRegex(ValueError, "reset_app_data"):
                    capture(
                        profile,
                        run,
                        "device",
                        {**recipe, "reset_app_data": True},
                        run,
                        continue_from=continued,
                    )
                with self.assertRaisesRegex(ValueError, "same device"):
                    capture(
                        profile,
                        run,
                        "other-device",
                        recipe,
                        run,
                        continue_from=continued,
                    )
                process_start = 200
                with self.assertRaisesRegex(RuntimeError, "process changed"):
                    capture(
                        profile, run, "device", recipe, run, continue_from=continued
                    )
                self.assertFalse(
                    any(
                        set(args) & {"install", "start", "force-stop", "clean"}
                        for args in calls
                    )
                )
                process_start = 100
                restart_during_acquisition = True
                with self.assertRaisesRegex(
                    RuntimeError, "process changed during screenshot"
                ):
                    capture(
                        profile, run, "device", recipe, run, continue_from=continued
                    )
