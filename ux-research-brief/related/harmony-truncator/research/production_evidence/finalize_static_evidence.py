"""Assemble the existing commercial references and controlled captures, offline."""

from truncator.common.capture_files import capture_image
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from research.production_evidence.comparison import inspect_target, compare_targets
from truncator.mutation.operators import REGISTRY
from truncator.common.storage import read, save, digest


PROJECT = Path(__file__).resolve().parents[2]
ARTIFACTS = PROJECT / "artifacts"
AUDIT = ARTIFACTS / "real-case-local-audit-20261117"
OUTPUT = ARTIFACTS / "static-evidence-final-20261117"


def verify_inspection(evidence):
    for key in ("tree", "screenshot"):
        if digest(Path(evidence[key]).read_bytes()) != evidence[key + "_sha256"]:
            raise ValueError("Evidence changed: " + evidence[key])


def inspect_capture(directory, selector, *, volatile_fields=()):
    directory = Path(directory)
    capture = read(directory / "capture.json")
    evidence = inspect_target(directory / "tree-before.json", capture_image(directory), selector)
    after = inspect_target(directory / "tree-after.json", capture_image(directory), selector)
    if capture["screenshot_sha256"] != evidence["screenshot_sha256"]:
        raise ValueError("Capture screenshot hash mismatch")
    before_attributes = evidence["target"]["attributes"]
    after_attributes = after["target"]["attributes"]
    changes = {key: [before_attributes.get(key), after_attributes.get(key)]
               for key in before_attributes.keys() | after_attributes.keys()
               if before_attributes.get(key) != after_attributes.get(key)}
    if set(changes) - set(volatile_fields) or evidence["target"]["path"] != after["target"]["path"]:
        raise ValueError("Target changed across the screenshot capture")
    return {
        "capture": str(directory), "hap_sha256": capture["hap_sha256"],
        "capture_sha256": digest((directory / "capture.json").read_bytes()),
        "after_tree_sha256": after["tree_sha256"], "target_stable": True,
        "evidence": evidence,
        **({"volatile_attribute_changes": changes, "ignored_fields": list(volatile_fields)}
           if volatile_fields else {}),
    }


def control_group():
    selector = {"id": "truncator_probe_bf0e7db549458b6420b3_0", "type": "Text"}
    baseline = Path("E:/HarmonyDev/MutationRuns/commerce-wide-baseline-20261113/capture-20261113-232634-158600")
    group = [{"state": "normal", "content_status": "complete", "recovery_status": "not-applicable",
              **inspect_capture(baseline, selector)}]
    for entry in read(ARTIFACTS / "service-control-final-reviews.json"):
        review_path = Path(entry["review"])
        review = read(review_path)
        initial = inspect_capture(review_path.parent, selector)
        if review["screenshot_sha256"] != initial["evidence"]["screenshot_sha256"]:
            raise ValueError("Review screenshot hash mismatch")
        actions = []
        for supplementary in review.get("evidence_captures", []):
            directory = Path(supplementary["capture"])
            for filename, expected in supplementary["sha256"].items():
                if digest((directory / filename).read_bytes()) != expected:
                    raise ValueError("Supplementary review evidence changed")
            action = inspect_capture(directory, selector)
            if action["hap_sha256"] != initial["hap_sha256"]:
                raise ValueError("Supplementary capture uses another HAP")
            action["recipe"] = read(directory / "capture.json")["recipe"]
            action["delta_x_px"] = (action["evidence"]["target"]["orig_bounds_px"][0]
                                    - initial["evidence"]["target"]["orig_bounds_px"][0])
            actions.append(action)
        group.append({"state": entry["operator"], **initial,
                      "content_status": review["content_status"],
                      "recovery_status": review["recovery_status"],
                      "review": str(review_path), "review_sha256": digest(review_path.read_bytes()),
                      "observed_actions": actions})
    save(OUTPUT / "matched-control-group.json", {
        "selector": selector, "reviewer": "assistant_visual_review",
        "independent_human_review": False,
        "recovery_scope": "Only the recorded actions on the injected applications",
        "states": group,
    })
    return group


def operator_coverage(rows, reviews):
    notes = {
        "freeze-viewport-width": "固定宽窗口基线尺寸，同HAP跨窗口适配实验；生产代表性按独立图树配对登记。",
        "viewport-width-mismatch": "点评与受控宽页面均有Scroll原宽超过导出宽度、Text右侧被屏幕边界限制；父类型和相交兄弟数量仍有差异。",
        "window-edge-clip": "美团与父容器整体偏移样本均有父子原底出窗口、导出底等于屏幕底且clip=false；Custom/Flex类型差异保留。",
        "line-clip": "58同城对应末尾字符缺失、两框相同及Row内局部结构。",
        "ellipsis-width": "58同城满足12项字段关系，原图中的省略符表现不同。",
        "ellipsis-lines": "本批商业案例没有明确的多行省略目标。",
        "height-clip": "美团在屏幕底边收缩，两框有差且clip=false；当前样本自身缩高、clip=true。",
        "width-clip": "点评在屏幕右边收缩且具有Scroll祖先；当前样本自身宽度裁切。",
        "parent-clip": "外部修复提供尺寸约束线索，商业图树配对尚缺。",
        "fixed-parent-clip": "同位置受控组已采集，商业窗口边界关系尚未对应。",
        "translate-clip": "12306同为顶部损失，Web边界与当前直接父Row裁切存在差异。",
        "ancestor-translate-clip": "12306与当前样本有顶部损失共同点，相关祖先类型及边界链有差异。",
        "child-overflow-clip": "点评宽页面提供越界线索，当前商城11目标未包含此算子。",
        "overlay-occlusion": "当前遮挡样本有相交兄弟，尚缺确定覆盖节点的商业对应。",
        "sibling-translate-occlusion": "本批商业样本尚未定位到可对应的既有兄弟覆盖关系。",
        "sibling-position-occlusion": "本批商业样本尚未定位到可对应的既有兄弟覆盖关系。",
        "scroll-recovery": "同位置已记录横滑恢复；商业历史样本的恢复行为未采集。",
        "whitespace-clip": "同位置已有框缩13px而文字完整的采集；商业对应尚缺。",
    }
    result = []
    for operator, spec in REGISTRY.items():
        comparisons = [row for row in rows if row["operator"] == operator]
        matching_reviews = [review for review in reviews if review["operator"] == operator]
        verified = [review for review in matching_reviews
                    if review["status"] == "local_static_pattern_correspondence"]
        status = "local_static_correspondence" if verified else "unestablished"
        result.append({
            "operator": operator, "mechanism_family": spec["mechanism_family"],
            "construction_intent": spec.get("construction_intent", "defect_candidate"),
            "commercial_static_status": status,
            "reviewed_pairs": matching_reviews,
            "commerce_mutation_ids": sorted({row["mutation_id"] for row in comparisons}),
            "comparisons": len(comparisons), "evidence_note": notes[operator],
            "commercial_recovery": "historically_not_collected",
        })
        if operator == "window-edge-clip":
            evidence_path = ARTIFACTS / "meituan-window-comparison-20261117.json"
            if evidence_path.exists():
                comparison = read(evidence_path)
                verify_inspection(comparison["reference"])
                verify_inspection(comparison["injected"])
                result[-1].update(commercial_static_status="window_boundary_relation_correspondence",
                                  comparison=str(evidence_path),
                                  remaining_differences=comparison["local_assessment"]["different_fields"])
        if operator == "freeze-viewport-width":
            evidence_path = ARTIFACTS / "dianping-frozen-viewport-comparison-20261117.json"
            verification_path = ARTIFACTS / "frozen-viewport-verification-20261117.json"
            if evidence_path.exists() and verification_path.exists():
                comparison = read(evidence_path)
                verify_inspection(comparison["reference"])
                verify_inspection(comparison["injected"])
                verification = read(verification_path)
                result[-1].update(commercial_static_status="viewport_boundary_relation_correspondence",
                                  comparison=str(evidence_path),
                                  remaining_differences=comparison["local_assessment"]["different_fields"],
                                  same_mutated_hap=verification["same_mutated_hap"],
                                  sampling=verification["sampling"])
        extra_name = {"window-edge-clip": "12306-web", "viewport-width-mismatch": "dianping-viewport"}.get(operator)
        if extra_name:
            evidence_path = ARTIFACTS / (extra_name + "-comparison-20261117.json")
            verified_path = ARTIFACTS / "layout-reference-verified-20261117.json"
            if evidence_path.exists() and verified_path.exists():
                comparison = read(evidence_path)
                verify_inspection(comparison["reference"])
                verify_inspection(comparison["injected"])
                case_name = "web" if operator == "window-edge-clip" else "native"
                case = next(row for row in read(verified_path)["cases"] if row["case"] == case_name)
                if case["mutated"]["evidence"] != comparison["injected"]:
                    raise ValueError("Comparison is not the reviewed runtime target")
                result[-1]["additional_commercial_pairs"] = [{
                    "comparison": str(evidence_path), "review": case["review"],
                    **case["commercial_pair_review"],
                    "remaining_differences": comparison["local_assessment"]["different_fields"],
                }]
                if operator == "viewport-width-mismatch":
                    result[-1]["commercial_static_status"] = "viewport_boundary_relation_correspondence"
    save(OUTPUT / "operator-coverage.json", result)
    return result


def layout_reference_figures():
    path = ARTIFACTS / "layout-reference-verified-20261117.json"
    if not path.exists():
        return []
    cases = read(path)["cases"]
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
    for case in cases:
        for state in ("baseline", "mutated"):
            evidence = case[state]
            current = inspect_capture(evidence["capture"], evidence["evidence"]["selector"],
                                      volatile_fields=evidence.get("ignored_fields", ()))
            if current != evidence:
                raise ValueError("Reviewed evidence changed: " + evidence["capture"])
        review_path = Path(case["review"])
        review = read(review_path)
        if digest(review_path.read_bytes()) != case["review_sha256"]:
            raise ValueError("Review changed")
        if review["decision"] != "accepted" or review["screenshot_sha256"] != case["mutated"]["evidence"]["screenshot_sha256"]:
            raise ValueError("Layout reference is not an accepted image")
        native = case["case"] == "native"
        name = "dianping-viewport" if native else "12306-web"
        comparison = read(ARTIFACTS / (name + "-comparison-20261117.json"))
        canvas = Image.new("RGB", (1450, 760), "#EEEEEE")
        draw = ImageDraw.Draw(canvas)
        panels = [
            ("商业历史原图局部，1倍像素", comparison["reference"],
             [740, 700, 1008, 980] if native else [1510, 0, 1820, 280], (30, 55)),
            ("受控应用注入前，1倍像素", case["baseline"]["evidence"],
             [600, 280, 1320, 640] if native else [0, 350, 550, 710], (30, 390)),
            ("受控应用注入后，1倍像素", case["mutated"]["evidence"],
             [1950, 270, 2584, 630] if native else [0, 0, 550, 360], (780, 390)),
        ]
        sources = []
        for label, evidence, box, position in panels:
            verify_inspection(evidence)
            with Image.open(evidence["screenshot"]) as original:
                canvas.paste(original.convert("RGB").crop(box), position)
            draw.text((position[0], position[1] - 33), label, font=font, fill="black")
            sources.append({"source": evidence["screenshot"], "sha256": evidence["screenshot_sha256"],
                            "crop_px": box, "scale": 1})
        canvas.save(OUTPUT / (name + ".png"))
        save(OUTPUT / (name + "-figure.json"), sources)
    return cases


def comparison_figure(reference, baseline, injected):
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 23)
    canvas = Image.new("RGB", (1120, 660), "white")
    draw = ImageDraw.Draw(canvas)
    panels = [
        (reference, (32, 2010, 1080, 2190), 1, (24, 55), "58同城历史原图局部，1倍像素"),
        (baseline, (2420, 900, 2570, 1010), 3, (24, 300), "商城注入前，3倍像素"),
        (injected, (2420, 900, 2570, 1010), 3, (590, 300), "商城line-clip注入后，3倍像素"),
    ]
    records = []
    for evidence, box, scale, position, label in panels:
        with Image.open(evidence["screenshot"]) as original:
            crop = original.convert("RGB").crop(box)
            crop = crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)
        canvas.paste(crop, position)
        draw.text((position[0], position[1] - 35), label, font=font, fill="black")
        records.append({"source": evidence["screenshot"], "sha256": evidence["screenshot_sha256"],
                        "crop_px": box, "scale": scale})
    canvas.save(OUTPUT / "58-line-clip.png")
    save(OUTPUT / "58-line-clip-figure.json", records)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = read(AUDIT / "commerce-comparison-matrix.json")
    reviews = read(AUDIT / "reviewed-pairs.json")
    inspections = list(AUDIT.glob("*-target.json")) + list(AUDIT.glob("injected-*.json"))
    for path in inspections:
        verify_inspection(read(path))
    for review in reviews:
        verify_inspection(review["reference"])
        verify_inspection(review["injected"])
    group = control_group()
    layout_cases = layout_reference_figures()
    coverage = operator_coverage(rows, reviews)
    reference = read(AUDIT / "06-target.json")
    injected = read(AUDIT / "injected-552ef6c1249895d1d479.json")
    path = Path(injected["tree"]).parent.parent / "baseline"
    baseline = inspect_target(path / "tree-before.json", capture_image(path), injected["selector"])
    verify_inspection(baseline)
    comparison = compare_targets(reference, injected)
    line_review = next(review for review in reviews if review["mutation_id"] == "552ef6c1249895d1d479")
    save(OUTPUT / "58-line-clip-comparison.json", {**comparison, "baseline": baseline,
          "review": line_review, "commercial_recovery": "historically_not_collected"})
    comparison_figure(reference, baseline, injected)
    window_path = ARTIFACTS / "meituan-window-comparison-20261117.json"
    if window_path.exists():
        window = read(window_path)
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
        canvas = Image.new("RGB", (1100, 580), "#EEEEEE")
        draw = ImageDraw.Draw(canvas)
        panels = [
            ("美团历史原图，2倍像素", window["reference"], [510, 2410, 830, 2496], 2, (30, 65)),
            ("商城父容器偏移后，4倍像素", window["injected"], [490, 1768, 590, 1828], 4, (30, 320)),
        ]
        sources = []
        for label, evidence, box, scale, position in panels:
            verify_inspection(evidence)
            with Image.open(evidence["screenshot"]) as original:
                crop = original.convert("RGB").crop(box)
                crop = crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)
            canvas.paste(crop, position)
            draw.text((position[0], position[1] - 35), label, font=font, fill="black")
            sources.append({"source": evidence["screenshot"], "sha256": evidence["screenshot_sha256"],
                            "crop_px": box, "scale": scale})
        canvas.save(OUTPUT / "meituan-window.png")
        save(OUTPUT / "meituan-window-figure.json", sources)
    provenance = []
    for name in ("ankidroid-centered.json", "ankidroid-dropdown.json"):
        path = ARTIFACTS / "operator-realism-20261117" / name
        commit = read(path)
        provenance.append({"origin": "external_upstream_fix", "file": str(path),
                           "sha256": digest(path.read_bytes()), "commit": commit["sha"],
                           "url": commit["html_url"], "message": commit["commit"]["message"]})
    save(OUTPUT / "source-provenance.json", provenance)
    save(OUTPUT / "verification.json", {
        "scope": "existing historical screenshots and runtime layout trees",
        "commercial_recovery": "historically_not_collected",
        "source_inspections_hash_verified": len(inspections),
        "operators_listed": len(coverage), "legacy_defect_operators": 13,
        "control_states": len(group),
        "supplementary_action_captures": sum(len(state.get("observed_actions", [])) for state in group),
        "static_correspondences": sum(row["commercial_static_status"] == "local_static_correspondence"
                                      for row in coverage),
        "window_boundary_correspondences": sum(
            row["commercial_static_status"] == "window_boundary_relation_correspondence"
            for row in coverage),
        "independent_human_review": False,
        "additional_reviewed_layout_cases": len(layout_cases),
        "partial_layout_correspondences": sum(
            pair["status"] == "partial_local_relation_correspondence"
            for row in coverage for pair in row.get("additional_commercial_pairs", [])),
    })
    print(OUTPUT)


if __name__ == "__main__":
    main()
