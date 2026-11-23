import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from truncator.execution.device.acquisition import acquire, target_state
from truncator.common.storage import read


def node(text="original", bounds="[0,0][50,20]", identity="target"):
    return {
        "attributes": {
            "id": identity,
            "type": "Text",
            "text": text,
            "bounds": bounds,
            "origBounds": bounds,
            "visible": "true",
        }
    }


class CaptureConsistencyTests(unittest.TestCase):
    target = {"selector": {"id": "target"}, "expected_text": "original"}

    def capture_sequence(self, root, sequence, check=None):
        trees = iter(sequence)
        commands = []

        def hdc(*args):
            commands.append(args[:2])
            if args[:2] == ("file", "recv"):
                Image.new("RGB", (50, 50), "white").save(args[3])

        def tree():
            commands.append(("tree",))
            return next(trees)

        with patch("truncator.execution.device.acquisition.time.sleep"), patch(
            "truncator.execution.device.waiting.time.sleep"
        ):
            result = acquire(root, hdc, tree, check, [self.target])
        return result, commands

    def test_missing_target_waits_then_captures_without_action_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result, commands = self.capture_sequence(root, [{}, node(), node()])
            self.assertEqual(result, (node(), node()))
            waiting = read(root / "frames/0/target-wait.json")
            self.assertEqual(len(waiting["polls"]), 2)
            self.assertTrue(waiting["ready"])
            self.assertEqual(commands.count(("shell", "snapshot_display")), 1)
            snapshot_index = commands.index(("shell", "snapshot_display"))
            self.assertEqual(commands[snapshot_index + 1], ("tree",))

    def test_changed_target_retries_and_preserves_failed_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.capture_sequence(root, [node(), node(identity="next"), node(), node()])
            quality = read(root / "image-quality.json")
            self.assertTrue(quality["passed"])
            self.assertFalse(quality["checks"][0]["targets"]["passed"])
            self.assertEqual(len(quality["checks"]), 2)
            self.assertTrue((root / "frames/0/snapshot.png").exists())
            self.assertEqual(read(root / "tree-after.json"), node())

    def test_motion_exhaustion_never_publishes_mismatched_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            moved = node(bounds="[0,10][50,30]")
            with self.assertRaisesRegex(RuntimeError, "target consistency"):
                self.capture_sequence(root, [node(), moved] * 3)
            self.assertFalse((root / "snapshot.png").exists())
            self.assertEqual(len(read(root / "image-quality.json")["checks"]), 3)

    def test_missing_target_timeout_remains_a_recorded_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch(
                "truncator.execution.device.acquisition.wait_for_tree",
                return_value=({}, {"ready": False, "polls": [], "elapsed": 15}),
            ), self.assertRaisesRegex(RuntimeError, "target consistency"):
                self.capture_sequence(root, [{}, {}, {}])
            quality = read(root / "image-quality.json")
            self.assertFalse(quality["passed"])
            self.assertFalse(quality["checks"][2]["target_wait"]["ready"])
            self.assertFalse((root / "snapshot.png").exists())

    def test_advisory_image_check_cannot_accept_changed_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.png"
            Image.new("RGB", (50, 50), "black").save(baseline)
            with self.assertRaisesRegex(RuntimeError, "target consistency"):
                self.capture_sequence(
                    root,
                    [node(), node(text="replacement")],
                    {
                        "baseline_image": str(baseline),
                        "attempts": 1,
                        "enforcement": "advisory",
                    },
                )
            self.assertFalse((root / "snapshot.png").exists())

    def test_identity_content_modal_scope_and_unrelated_changes(self):
        ready, state = target_state(node(text="replacement"), [self.target])
        self.assertFalse(ready)
        self.assertIn("content changed", state[0]["error"])
        self.assertFalse(target_state([node(), node()], [self.target])[0])
        dialog = {
            "attributes": {"type": "Dialog", "visible": "true"},
            "children": [node()],
        }
        self.assertEqual(
            target_state([node(text="background"), dialog], [self.target]),
            target_state(dialog, [self.target]),
        )
        self.assertEqual(
            target_state([node(), node(identity="unrelated")], [self.target]),
            target_state(node(), [self.target]),
        )


if __name__ == "__main__":
    unittest.main()
