import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from truncator.common.storage import save, read, digest
from truncator.imaging.content_identity import compare_visible
from research.production_evidence.case_evidence import (
    template,
    record_case_review,
    export_case_review,
    verify_exported_case,
)
from truncator.review.datasets.dataset_balance import audit_exports, rank_replenishment
from research.controls.evidence import validate_visual_recovery
from research.controls.evidence import interaction_measurement
from truncator.review.review_evidence import capture_hashes


class EvidenceUpgradeTests(unittest.TestCase):
    def test_text_ink_tolerates_one_pixel_raster_shift_but_rejects_missing_glyph(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = Image.new("RGB", (80, 60), "white")
            draw = ImageDraw.Draw(reference)
            draw.rectangle((15, 15, 20, 40), fill="black")
            draw.rectangle((35, 15, 40, 40), fill="black")
            reference.save(root / "reference.png")
            shifted = Image.new("RGB", reference.size, "white")
            shifted.paste(reference, (1, 0))
            shifted.save(root / "current.png")
            box = [0, 0, 80, 60]
            args = (root / "reference.png", root / "current.png", box, box, box)
            self.assertEqual(compare_visible(*args, text=True)["status"], "matched")
            ImageDraw.Draw(shifted).rectangle((34, 14, 43, 42), fill="white")
            shifted.save(root / "current.png")
            self.assertEqual(compare_visible(*args, text=True)["status"], "different")
            Image.new("RGB", reference.size, "white").save(root / "current.png")
            self.assertEqual(compare_visible(*args, text=True)["status"], "different")
            self.assertEqual(compare_visible(root / "current.png", root / "current.png", box, box, box, text=True)["status"], "unknown")

    def test_unchanged_text_tree_and_full_geometry_cannot_hide_blank_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for component in ("Text", "Button"):
                with self.subTest(component=component):
                    for name in ("baseline", "initial", "current"):
                        folder = root / name
                        folder.mkdir(exist_ok=True)
                        image = Image.new("RGB", (80, 60), "white")
                        if name != "current":
                            ImageDraw.Draw(image).rectangle((15, 15, 22, 40), fill="black")
                        image.save(folder / "snapshot.jpeg", quality=100)
                        save(folder / "tree-before.json", {
                            "attributes": {"id": "viewport", "bounds": "[0,0][80,60]"},
                            "children": [{"attributes": {"id": "content", "type": component,
                                "text": "unchanged", "bounds": "[0,0][80,60]", "origBounds": "[0,0][80,60]"}}],
                        })
                    plan = {"geometry": {"mutated_selector": {"id": "content"},
                            "baseline_capture": str(root / "baseline"), "target_bounds_px": [0, 0, 80, 60],
                            "baseline_image_sha256": digest((root / "baseline/snapshot.jpeg").read_bytes())},
                            "parameters": {"viewport_id": "viewport"}, "control_group": {"axis": "horizontal"}}
                    result = interaction_measurement(root / "initial", root / "current", plan)
                    self.assertEqual(result["uncovered_component_area_px2"], 0)
                    self.assertFalse(result["same_content"])
                    self.assertFalse(result["initial_and_current_cover_baseline_ink"])
                    self.assertEqual(result["visual_identity"][1]["status"], "different")

    def test_text_neighborhood_does_not_judge_its_unobservable_outer_support_ring(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = Image.new("RGB", (80, 60), "white")
            ImageDraw.Draw(reference).rectangle((15, 15, 22, 40), fill="black")
            current = reference.copy()
            reference.putpixel((40, 57), (209, 209, 209))
            current.putpixel((40, 57), (236, 236, 236))
            reference.save(root / "reference.png")
            current.save(root / "current.png")
            box = [0, 0, 80, 60]
            result = compare_visible(root / "reference.png", root / "current.png", box, box, box, text=True)
            self.assertEqual(result["status"], "matched")
            self.assertEqual(result["comparison_border_px"], 3)

    def test_recovery_requires_an_actual_forward_action(self):
        with self.assertRaisesRegex(ValueError, "forward action"):
            validate_visual_recovery({"interactions": []}, {"scroll"})

    def test_image_node_with_unchanged_empty_text_does_not_hide_a_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, color in (
                ("baseline", "blue"),
                ("initial", "blue"),
                ("changed", "red"),
            ):
                folder = root / name
                folder.mkdir()
                image = Image.new("RGB", (80, 80), "white")
                ImageDraw.Draw(image).rectangle((20, 20, 60, 60), fill=color)
                image.save(folder / "snapshot.jpeg", quality=100)
                save(
                    folder / "tree-before.json",
                    {
                        "attributes": {"id": "viewport", "bounds": "[0,0][80,80]"},
                        "children": [
                            {
                                "attributes": {
                                    "id": "image",
                                    "type": "Image",
                                    "text": "",
                                    "bounds": "[0,0][80,80]",
                                    "origBounds": "[0,0][80,80]",
                                }
                            }
                        ],
                    },
                )
            plan = {
                "geometry": {
                    "mutated_selector": {"id": "image"},
                    "baseline_capture": str(root / "baseline"),
                    "target_bounds_px": [0, 0, 80, 80],
                    "baseline_image_sha256": digest(
                        (root / "baseline/snapshot.jpeg").read_bytes()
                    ),
                },
                "parameters": {"viewport_id": "viewport"},
                "control_group": {"axis": "horizontal"},
            }
            result = interaction_measurement(root / "initial", root / "changed", plan)
            self.assertFalse(result["same_content"])
            self.assertFalse(result["initial_and_current_cover_component"])
            self.assertEqual(result["visual_identity"][1]["status"], "different")
            (root / "baseline/snapshot.jpeg").write_bytes(
                (root / "changed/snapshot.jpeg").read_bytes()
            )
            with self.assertRaisesRegex(ValueError, "unchanged planned baseline"):
                interaction_measurement(root / "initial", root / "changed", plan)

    def test_aligned_visible_picture_matches_after_translation_but_replacement_fails(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = Image.new("RGB", (120, 100), "white")
            ImageDraw.Draw(a).rectangle((30, 25, 70, 65), fill="blue")
            a.save(root / "normal.png")
            b = Image.new("RGB", (120, 100), "white")
            b.paste(a.crop((30, 10, 90, 90)), (10, 10))
            b.save(root / "moved.png")
            args = (
                root / "normal.png",
                root / "moved.png",
                [10, 10, 90, 90],
                [-10, 10, 70, 90],
                [10, 10, 70, 90],
            )
            self.assertEqual(compare_visible(*args)["status"], "matched")
            ImageDraw.Draw(b).rectangle((12, 25, 50, 65), fill="red")
            b.save(root / "moved.png")
            self.assertEqual(compare_visible(*args)["status"], "different")

    def test_blank_pixels_cannot_establish_image_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Image.new("RGB", (40, 40), "white").save(root / "a.png")
            r = compare_visible(
                root / "a.png",
                root / "a.png",
                [0, 0, 40, 40],
                [0, 0, 40, 40],
                [0, 0, 40, 40],
            )
            self.assertEqual(r["status"], "unknown")

    def capture(self, root):
        cap = root / "run/capture-1"
        cap.mkdir(parents=True)
        Image.new("RGB", (40, 40), "white").save(cap / "snapshot.jpeg")
        save(
            cap / "capture.json",
            {
                "screenshot_sha256": digest((cap / "snapshot.jpeg").read_bytes()),
                "recipe": {},
            },
        )
        for name in ("tree-before.json", "tree-after.json"):
            save(cap / name, {})
        save(
            cap.parent / "plan.json",
            {"id": "target", "operator": "cache-viewport-width"},
        )
        return cap

    def test_operator_provenance_does_not_automatically_grant_production_support(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cap = self.capture(root)
            self.assertEqual(
                export_case_review(cap, root / "out")["level"], "unresolved"
            )
            review = template(cap)
            review.update(
                level="production-supported", reviewer="fixture", rationale="test"
            )
            save(root / "review.json", review)
            with self.assertRaisesRegex(ValueError, "coding_mistake"):
                record_case_review(cap, root / "review.json")

    def test_case_review_binds_tree_and_supporting_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cap = self.capture(root)
            review = template(cap)
            review.update(
                level="mechanism-control",
                reviewer="fixture",
                rationale="controlled experiment",
            )
            evidence = root / "evidence.txt"
            evidence.write_text("evidence")
            review["evidence"] = [
                {
                    "role": "comparison",
                    "path": str(evidence),
                    "sha256": digest(evidence.read_bytes()),
                }
            ]
            save(root / "review.json", review)
            record_case_review(cap, root / "review.json")
            export_case_review(cap, root / "out")
            import shutil

            for name in (
                "capture.json",
                "snapshot.jpeg",
                "tree-before.json",
                "tree-after.json",
            ):
                shutil.copy2(cap / name, root / "out" / name)
            shutil.copy2(cap.parent / "plan.json", root / "out/plan.json")
            self.assertEqual(
                verify_exported_case(root / "out")["level"], "mechanism-control"
            )
            copied = read(root / "out/case-review.json")["evidence"][0]["path"]
            self.assertFalse(Path(copied).is_absolute())
            self.assertEqual(
                (root / "out" / copied).read_bytes(), evidence.read_bytes()
            )
            portable = read(root / "out/case-review.json")
            portable["evidence"][0]["path"] = "../evidence.txt"
            save(root / "out/case-review.json", portable)
            with self.assertRaisesRegex(ValueError, "inside the sample"):
                verify_exported_case(root / "out")
            evidence.write_text("changed")
            with self.assertRaisesRegex(ValueError, "supporting evidence"):
                export_case_review(cap, root / "out2")
            save(cap / "tree-before.json", {"changed": True})
            with self.assertRaisesRegex(ValueError, "current capture"):
                record_case_review(cap, root / "review.json")

    def test_production_review_must_cover_each_visible_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cap = self.capture(root)
            review = template(cap)
            review.update(
                level="production-supported",
                reviewer="fixture",
                rationale="test",
                targets={},
            )
            save(root / "review.json", review)
            with self.assertRaisesRegex(ValueError, "exactly"):
                record_case_review(cap, root / "review.json")

    def test_different_nontext_cannot_be_accepted_as_recovered_but_can_be_rejected(
        self,
    ):
        result = {
            "interactions": [
                {
                    "state": "scroll",
                    "stage": "forward",
                    "measurement": {
                        "observations": [{"type": "Image"}],
                        "same_content": True,
                        "same_extent": True,
                        "foreground_coverage": {"status": "covered"},
                    },
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "unverified"):
            validate_visual_recovery(result, {"scroll"})
        validate_visual_recovery(result, set())

    def test_final_balance_deduplicates_exports_and_keeps_untested_recovery_unresolved(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save(root / "export-status.json", {"complete": True})
            save(root / "a/capture.json", {"unique": "capture", "screenshot_sha256": digest(b"image")})
            for name in ("tree-before.json", "tree-after.json"):
                save(root / "a" / name, {})
            (root / "a/snapshot.jpeg").write_bytes(b"image")
            save(root / "a/review.json", {"decision": "accepted", "screenshot_sha256": digest(b"image"),
                 "capture_files": capture_hashes(root / "a"),
                 "content_status": "clipped", "recovery_status": "not-tested"})
            save(
                root / "manifest.json",
                {
                    "samples": [
                        {
                            "id": "a",
                            "component": "Image",
                            "content_status": "clipped",
                            "recovery_status": "not-tested",
                            "case_review": {"level": "unresolved"},
                        }
                    ]
                },
            )
            report = audit_exports([root, root], {"component": {"Image": 3}})
            self.assertEqual(report["counts"]["component"], {"Image": 1})
            self.assertEqual(report["counts"]["label"], {"unresolved": 1})
            self.assertEqual(report["deficits"]["component"], {"Image": 2})
            self.assertEqual(len(report["duplicates_excluded"]), 1)
            with self.assertRaises(ValueError):
                audit_exports([root], {"component": {"Image": True}})

    def test_replenishment_does_not_infer_positive_labels_or_include_occlusion(self):
        candidates = [
            {
                "id": "one",
                "operator": "fixed-parent-clip",
                "site": {"component": "Image"},
                "geometry": {"edge": "right"},
                "production_basis": {"task_role": "truncation_candidate"},
            },
            {
                "id": "two",
                "operator": "overlay-occlusion",
                "site": {"component": "Image"},
                "production_basis": {"task_role": "out_of_scope"},
            },
        ]
        report = {
            "deficits": {"component": {"Image": 2}, "label": {"positive": 100}},
            "units": [],
        }
        result = rank_replenishment(candidates, report)
        self.assertEqual([r["plan"] for r in result["candidates"]], ["one"])
        self.assertEqual(result["candidates"][0]["score"], 2)


if __name__ == "__main__":
    unittest.main()
