import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from truncator.execution.device.device_context import display_context
from truncator.execution.device.runtime import latest_capture
from truncator.common.storage import save
from truncator.execution.device.capture_policy import CURRENT_CAPTURE_POLICY

DUMP = "DisplayFoldStatus: EXPAND\nVirtualPixelRatio: 3.125\n[DISPLAY INFO]\nWidth: 2224\nHeight: 2496\n"


class DeviceContextTests(unittest.TestCase):
    def test_context_uses_display_dimensions_and_fold_status(self):
        self.assertEqual(
            display_context(DUMP),
            {"screen_size": [2224, 2496], "px_per_vp": 3.125, "fold_status": "EXPAND"},
        )
        self.assertIsNone(
            display_context(DUMP + "[DISPLAY INFO]\nWidth: 1080\nHeight: 2504\n")
        )

    def test_reuse_on_same_device_rejects_other_posture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(root / "profile.json", {"hdc": "mock"})
            save(
                root / "capture-1/capture.json",
                {
                    "device": "device",
                    "capture_policy": CURRENT_CAPTURE_POLICY,
                    "recipe": {},
                    "display_context": display_context(DUMP),
                },
            )
            with patch("truncator.execution.device.runtime.command", return_value=(DUMP, {})):
                self.assertEqual(latest_capture(root, "device", {}), root / "capture-1")
            closed = (
                DUMP.replace("EXPAND", "FOLDED")
                .replace("2224", "1080")
                .replace("2496", "2504")
            )
            with patch("truncator.execution.device.runtime.command", return_value=(closed, {})):
                self.assertIsNone(latest_capture(root, "device", {}))
            with patch("truncator.execution.device.runtime.command", return_value=("", {})):
                self.assertIsNone(latest_capture(root, "device", {}))
