import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from truncator.execution.campaign import campaign
from truncator.planning.campaign_policy import effective_page, selected_operators, validate_campaign
from truncator.mutation.operators import UX_OPERATORS, DEFAULT_CAMPAIGN_OPERATORS


class CampaignPolicyTests(unittest.TestCase):
    def test_explicit_single_operator_in_combined_mode_is_honored(self):
        self.assertEqual(selected_operators({"operator": "scroll-recovery"}, "combined"), ["scroll-recovery"])
        self.assertEqual(selected_operators({}, "combined"), DEFAULT_CAMPAIGN_OPERATORS)

    def test_out_of_scope_case_rejected_before_workspace_or_device_work(self):
        for application in (
            {"operator": "overlay-occlusion"},
            {"operators": ["sibling-position-occlusion"]},
            {"cases": [{"operator": "sibling-translate-occlusion"}]},
            {"mode": "individual", "pages": [{"operator": "overlay-occlusion"}]},
        ):
            with self.subTest(application=application), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / "run"
                with patch("truncator.execution.campaign.prepare_application") as baseline:
                    with self.assertRaises(ValueError):
                        campaign({"applications": [application]}, target, "unused-device")
                    baseline.assert_not_called()
                self.assertFalse(target.exists())

    def test_ambiguous_or_ignored_operator_fields_fail(self):
        for page, mode in (
            ({"operator": "height-clip", "operators": ["parent-clip"]}, "combined"),
            ({"cases": [{"operator": "height-clip"}]}, "combined"),
            ({"operators": ["height-clip"]}, "individual"),
            ({"operator": "height-clip", "cases": [{"operator": "parent-clip"}]}, "individual"),
        ):
            with self.subTest(page=page, mode=mode), self.assertRaises(ValueError):
                selected_operators(page, mode)

    def test_malformed_and_duplicate_selections_are_not_silently_weighted(self):
        for values in ("height-clip", [], [None], ["no-such-operator"], ["height-clip", "height-clip"]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                selected_operators({"operators": values}, "combined")


    def test_scope_selection_uses_capabilities_without_production_grades(self):
        report = validate_campaign({"applications": [{"operators": ["cache-viewport-width", "whitespace-clip", "line-clip"]}]})
        self.assertEqual(report["pages"][0]["operators"], ["cache-viewport-width", "whitespace-clip", "line-clip"])
        self.assertNotIn("production_basis", report["pages"][0])
        self.assertNotIn("overlay-occlusion", UX_OPERATORS)

    def test_page_override_replaces_application_selection_as_one_unit(self):
        application = {"operator": "height-clip", "pages": [{}, {"operators": ["scroll-recovery"]}]}
        report = validate_campaign({"applications": [application]})
        self.assertEqual([p["operators"] for p in report["pages"]], [["height-clip"], ["scroll-recovery"]])
        page = effective_page(application, application["pages"][1])
        self.assertNotIn("operator", page)
        self.assertEqual(selected_operators(page, "combined"), ["scroll-recovery"])

    def test_invalid_mode_fails_preflight(self):
        with self.assertRaisesRegex(ValueError, "mode"):
            validate_campaign({"applications": [{"mode": "combinned"}]})

    def test_application_options_on_pages_fail_before_any_work(self):
        for key, value in {"verify_recovery": False, "instrument": False, "max_total": 2,
                           "max_per_page": 2, "max_area_ratio": 0.5, "seed": 17,
                           "profile": "ignored.json", "baseline_run": "ignored-run",
                           "mode": "combined", "pages": [{}]}.items():
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / "run"
                with patch("truncator.execution.campaign.prepare_application") as prepare:
                    with self.assertRaisesRegex(ValueError, "Application-only.*" + key):
                        campaign({"applications": [{"profile": "app.json", "pages": [{key: value}]}]},
                                 target, "unused-device")
                    prepare.assert_not_called()
                self.assertFalse(target.exists())

    def test_application_options_remain_valid_with_and_without_pages(self):
        for pages in ({}, {"pages": [{"name": "home", "recipe": "home.json", "px_per_vp": 2.75,
                                     "file": "Index.ets", "operators": ["scroll-recovery"]}]}):
            report = validate_campaign({"applications": [{"profile": "app.json", "recipe": "home.json",
                "instrument": False, "verify_recovery": False, "max_total": 2, "seed": 17, **pages}]})
            self.assertEqual(len(report["pages"]), 1)


if __name__ == "__main__":
    unittest.main()
