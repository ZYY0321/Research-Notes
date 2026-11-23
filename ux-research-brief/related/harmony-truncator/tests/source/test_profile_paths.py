"""Campaign file references remain stable across shell working directories."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from truncator.common.storage import read, save
from truncator.source.configuration import load_campaign
from truncator.planning.campaign_policy import validate_campaign


class ProfilePathTests(unittest.TestCase):
    def test_config_references_are_relative_to_specification_and_source_filters_are_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = root / "config/campaigns/task.json"
            save(spec, {"applications": [{"profile": "../apps/app.json", "baseline_run": "../../runs/base",
                 "pages": [{"recipe": "../recipes/app/home.json", "file": "pages/Index.ets"}]}]})
            with patch("pathlib.Path.cwd", return_value=root / "unrelated-shell-directory"):
                loaded = load_campaign(spec)
            app = loaded["applications"][0]
            self.assertEqual(Path(app["profile"]), root / "config/apps/app.json")
            self.assertEqual(Path(app["baseline_run"]), root / "runs/base")
            self.assertEqual(Path(app["pages"][0]["recipe"]), root / "config/recipes/app/home.json")
            self.assertEqual(app["pages"][0]["file"], "pages/Index.ets")
            self.assertEqual(read(spec)["applications"][0]["profile"], "../apps/app.json")

    def test_shipped_campaigns_resolve_all_app_and_recipe_files(self):
        profiles = Path(__file__).resolve().parents[2] / "profiles"
        self.assertEqual(len(list(profiles.rglob("*.json"))), 22)
        for spec in sorted((profiles / "campaigns").glob("*.json")):
            with self.subTest(spec=spec.name):
                config = load_campaign(spec)
                validate_campaign(config)
                for app in config["applications"]:
                    self.assertTrue(Path(app["profile"]).is_file(), app["profile"])
                    for page in app.get("pages", [app]):
                        self.assertTrue(Path(page["recipe"]).is_file(), page["recipe"])
