import copy
import tempfile
import unittest
from pathlib import Path

from research.controls.replay import verify_interaction_replay
from truncator.common.storage import save


class ReplayEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.attrs = {"id": "view", "bounds": "[100,200][300,400]"}
        self.action = {"kind": "swipe", "selector": {"id": "view"}, "from": [.8,.5], "to": [.2,.5]}
        self.recipe = {"actions": [self.action]}
        self.step = {"index": 0, "phase": "route", "action": self.action,
                     "status": "dispatched", "location_wait": {"ready": True},
                     "matches": [self.attrs], "arguments": ["swipe","260","300","140","300","600"]}
        save(self.root / "action-before-000.json", {"attributes": self.attrs})

    def check(self, step):
        save(self.root / "replay.json", [step])
        verify_interaction_replay(self.root, self.recipe)

    def test_valid_dispatch_uses_absolute_observed_coordinates(self):
        self.check(self.step)

    def test_correct_recipe_cannot_hide_absent_or_failed_dispatch(self):
        for status in ("locating", "dispatching", "optional_absent", "checkpoint_failed"):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "dispatch"):
                self.check({**self.step, "status": status})

    def test_wrong_coordinates_and_different_observed_target_are_rejected(self):
        bad = copy.deepcopy(self.step)
        bad["arguments"][1] = "80"
        with self.assertRaisesRegex(ValueError, "coordinates"):
            self.check(bad)
        bad = copy.deepcopy(self.step)
        bad["matches"][0]["bounds"] = "[0,0][200,200]"
        with self.assertRaisesRegex(ValueError, "pre-action tree"):
            self.check(bad)

    def test_missing_replay_and_duplicate_target_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            verify_interaction_replay(self.root, self.recipe)
        save(self.root / "action-before-000.json", {"children": [
            {"attributes": self.attrs}, {"attributes": self.attrs}]})
        with self.assertRaises(ValueError):
            self.check({**self.step, "matches": [self.attrs, self.attrs]})

    def test_checkpoint_must_be_confirmed_by_its_observation(self):
        action = {**self.action, "checks": [{"selector": {"id": "expected"}}]}
        self.recipe = {"actions": [action]}
        step = {**self.step, "action": action, "status": "checkpoint_passed", "checkpoint_wait": {"ready": True}}
        save(self.root / "action-after-000.json", {"attributes": {"id": "elsewhere"}})
        with self.assertRaisesRegex(ValueError, "checkpoint"):
            self.check(step)
        save(self.root / "action-after-000.json", {"attributes": {"id": "expected"}})
        self.check(step)
