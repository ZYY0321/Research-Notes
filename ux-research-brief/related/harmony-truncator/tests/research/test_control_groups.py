import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

from research.controls.evidence import (
    directional_swipe,
    interaction_measurement,
    evidence_identity,
    apply_group_review,
)
from research.controls.evidence import validate_interaction
from truncator.review.consistency import inspect_exported_strips
from truncator.common.storage import read, save, digest
from research.controls.dataset import export_dataset
from truncator.execution.workflow import review


class ControlGroupTests(unittest.TestCase):
    def test_interaction_requires_unchanged_previous_frame_and_process(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = {"status": "verified", "process": {"pid": 12, "start_ticks": 100}}
            for name in ("before", "after"):
                folder = root / name
                folder.mkdir()
                (folder / "snapshot.jpeg").write_bytes(b"frame")
                save(folder / "tree-before.json", {})
                save(folder / "tree-after.json", {})
                save(
                    folder / "capture.json",
                    {
                        "screenshot_sha256": digest(b"frame"),
                        "hap_sha256": "package",
                        "session": session,
                    },
                )
            previous = evidence_identity(root / "before")
            record = read(root / "after/capture.json")
            record["continued_from"] = {
                "capture": previous["capture"],
                "capture_sha256": previous["sha256"]["capture.json"],
            }
            save(root / "after/capture.json", record)
            action = {**evidence_identity(root / "after"), "before": previous}
            validate_interaction(action)
            record["session"] = {
                "status": "verified",
                "process": {"pid": 12, "start_ticks": 200},
            }
            save(root / "after/capture.json", record)
            changed = {**evidence_identity(root / "after"), "before": previous}
            with self.assertRaisesRegex(ValueError, "preceding capture session"):
                validate_interaction(changed)
            save(root / "before/tree-after.json", {"changed": True})
            with self.assertRaisesRegex(ValueError, "evidence changed"):
                validate_interaction(changed)

    def test_directional_actions_reverse_and_orthogonal_axes(self):
        horizontal = directional_swipe({"id": "viewport"}, "horizontal")
        vertical = directional_swipe({"id": "viewport"}, "vertical")
        self.assertEqual(horizontal["from"][1], horizontal["to"][1])
        self.assertEqual(vertical["from"][0], vertical["to"][0])
        self.assertEqual(
            directional_swipe({"id": "viewport"}, "vertical", True)["from"],
            vertical["to"],
        )

    def test_content_relative_movement_excludes_whole_parent_motion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def tree(original, visible, parent):
                return {
                    "attributes": {
                        "id": "viewport",
                        "type": "Scroll",
                        "bounds": parent,
                    },
                    "children": [
                        {
                            "attributes": {
                                "id": "text",
                                "type": "Text",
                                "text": "same",
                                "bounds": visible,
                                "origBounds": original,
                            }
                        }
                    ],
                }

            save(
                root / "before/tree-before.json",
                tree("[10,10][110,110]", "[10,10][110,70]", "[10,10][110,70]"),
            )
            save(
                root / "after/tree-before.json",
                tree("[10,-30][110,70]", "[10,10][110,70]", "[10,10][110,70]"),
            )
            plan = {
                "geometry": {"mutated_selector": {"id": "text"}},
                "parameters": {"viewport_id": "viewport"},
                "control_group": {"axis": "vertical"},
            }
            measured = interaction_measurement(root / "before", root / "after", plan)
            self.assertEqual(measured["delta_along_axis_px"], -40)
            self.assertEqual(measured["uncovered_component_area_px2"], 0)
            self.assertFalse(measured["same_content"])  # No reference pixels in this geometry-only fixture.
            save(
                root / "after/tree-before.json",
                tree("[10,30][110,130]", "[10,30][110,90]", "[10,30][110,90]"),
            )
            measured = interaction_measurement(root / "before", root / "after", plan)
            self.assertEqual(measured["delta_along_axis_px"], 0)
            self.assertFalse(measured["initial_and_current_cover_component"])

    def test_exported_strip_detects_visible_ink_and_actual_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = Image.new("RGB", (80, 50), "white")
            ImageDraw.Draw(original).rectangle((30, 12, 45, 15), fill="black")
            original.save(root / "normal.png")
            original.save(root / "visible.png")
            check = inspect_exported_strips(
                root / "normal.png",
                root / "visible.png",
                [10, 10, 70, 40],
                [10, 10, 70, 40],
                [10, 20, 70, 40],
            )
            self.assertTrue(check["strips"][0]["ink_visible_outside_exported_bounds"])
            Image.new("RGB", (80, 50), "white").save(root / "clipped.png")
            check = inspect_exported_strips(
                root / "normal.png",
                root / "clipped.png",
                [10, 10, 70, 40],
                [10, 10, 70, 40],
                [10, 20, 70, 40],
            )
            self.assertFalse(check["strips"][0]["ink_visible_outside_exported_bounds"])

    def test_group_export_includes_external_normal_and_rejects_changed_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            states = []
            for name in ("normal", "clipped", "scroll", "whitespace"):
                run = root / name
                cap = run / "capture-001"
                cap.mkdir(parents=True)
                Image.new("RGB", (30, 20), "white").save(cap / "snapshot.jpeg")
                save(run / "profile.json", {"bundle": "test"})
                save(
                    cap / "capture.json",
                    {
                        "hap_sha256": name,
                        "recipe": {},
                        "screenshot_sha256": digest(
                            (cap / "snapshot.jpeg").read_bytes()
                        ),
                    },
                )
                for filename in ("tree-before.json", "tree-after.json"):
                    save(cap / filename, {})
                review(
                    cap,
                    "accepted",
                    "test",
                    "Test evidence",
                    [],
                    content_status="complete",
                    recovery_status="not-applicable",
                )
                states.append(
                    {"state": name, "status": "captured", **evidence_identity(cap)}
                )
            save(
                root / "group/control-results.json",
                {
                    "id": "group",
                    "complete": True,
                    "states": states,
                    "direction": {"axis": "horizontal"},
                    "interactions": [],
                },
            )
            entries = [
                {
                    "state": state["state"],
                    "capture": state["capture"],
                    "sha256": state["sha256"],
                    "decision": "accepted",
                    "content_status": "complete",
                    "recovery_status": "not-applicable",
                    "reason": "Independent fixture check",
                }
                for state in states
            ]
            submission = {
                "group_id": "group",
                "reviewer": "second-reviewer",
                "independent_review": True,
                "states": entries,
            }
            entries[-1]["reason"] = ""
            save(root / "review.json", submission)
            with self.assertRaisesRegex(ValueError, "evidence reason"):
                apply_group_review(root / "group", root / "review.json")
            self.assertEqual(
                len(list((root / "normal/capture-001").glob("review-*.json"))), 1
            )
            entries[-1]["reason"] = "Complete glyphs"
            save(root / "review.json", submission)
            self.assertEqual(
                len(apply_group_review(root / "group", root / "review.json")), 4
            )
            self.assertEqual(export_dataset(root / "group", root / "export"), 4)
            manifest = read(root / "export/manifest.json")
            self.assertEqual(
                {row["control_state"] for row in manifest["samples"]},
                {row["state"] for row in states},
            )
            self.assertEqual(len(manifest["control_groups"][0]["sample_ids"]), 4)
            self.assertEqual(
                len({sample["split_group"] for sample in manifest["samples"]}), 1
            )
            # A manually accepted single-state review must not bypass the
            # directional action checks required for exporting a control group.
            review(
                root / "clipped/capture-001", "accepted", "test", "No action evidence", [],
                content_status="clipped", recovery_status="not-recovered",
            )
            with self.assertRaisesRegex(ValueError, "sequence"):
                export_dataset(root / "group", root / "unsupported-label-export")
            self.assertFalse((root / "unsupported-label-export").exists())
            save(root / "normal/capture-001/tree-after.json", {"changed": True})
            with self.assertRaisesRegex(ValueError, "evidence changed"):
                export_dataset(root / "group", root / "changed-export")
