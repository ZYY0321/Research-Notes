import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from truncator.review.reporting.report_assets import locate
from truncator.execution.device.runtime import capture
from truncator.common.storage import digest, read, save


class ModalCaptureTests(unittest.TestCase):
    def test_duplicate_nodes_in_active_dialog_remain_unresolved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            node = {"attributes": {
                "id": "shared", "type": "Text", "bounds": "[0,0][20,20]",
                "visible": "true",
            }}
            save(root / "tree-before.json", {
                "attributes": {"type": "Dialog", "visible": "true"},
                "children": [node, node],
            })
            result = locate(root, {"id": "shared", "type": "Text"})
            self.assertEqual(result["status"], "target_unresolved")
            self.assertIn("matched 2", result["reason"])

    def test_capture_measurement_and_report_use_the_active_dialog(self):
        def text_node(bounds):
            return {"attributes": {
                "id": "shared", "type": "Text", "text": "label",
                "bounds": bounds, "origBounds": bounds, "visible": "true",
            }}

        tree = [text_node("[0,0][40,20]"), {
            "attributes": {
                "type": "Dialog", "visible": "true", "focused": "true",
                "bounds": "[0,50][100,100]",
            },
            "children": [text_node("[20,60][70,80]")],
        }]

        def command(args, log, **kwargs):
            if "dumpLayout" in args:
                output = "DumpLayout saved"
            elif "cat" in args:
                output = json.dumps(tree)
            elif "pidof" in args:
                output = "123"
            else:
                output = ""
            Path(log).write_text(output, encoding="utf-8")
            return output, {"seconds": 0, "returncode": 0}

        def acquire(folder, *args):
            Image.new("RGB", (100, 100), "white").save(folder / "snapshot.jpeg")
            for name in ("tree-before.json", "tree-after.json"):
                save(folder / name, tree)
            return tree, tree

        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            baseline = run / "baseline"
            baseline.mkdir()
            acquire(baseline)
            profile = {"hdc": "mock", "bundle": "fixture", "hap": "app.hap"}
            save(run / "profile.json", profile)
            (run / "project").mkdir()
            (run / "project/app.hap").write_bytes(b"hap")
            save(run / "build.json", {"hap_sha256": digest(b"hap")})
            selector = {"id": "shared", "type": "Text"}
            save(run / "plan.json", {
                "operator": "height-clip",
                "geometry": {
                    "selector": selector,
                    "penetration_px": 5,
                    "target_bounds_px": [20, 60, 70, 80],
                    "baseline_capture": str(baseline),
                    "source_binding": {"instance_index": 0, "baseline_text": "label"},
                },
            })
            with patch("truncator.execution.device.runtime.command", command), patch(
                "truncator.execution.device.runtime.time.sleep", lambda _: None
            ), patch("truncator.execution.device.acquisition.acquire", acquire):
                folder = capture(profile, run, "modal-fixture", {"settle_seconds": 0}, run)
            observation = read(folder / "geometry-observation.json")
            self.assertEqual(observation["status"], "measured")
            self.assertEqual(observation["target"]["bounds"], "[20,60][70,80]")
            self.assertEqual(locate(folder, selector)["bounds"], [20, 60, 70, 80])
            self.assertEqual(read(folder / "tree-before.json"), tree)
