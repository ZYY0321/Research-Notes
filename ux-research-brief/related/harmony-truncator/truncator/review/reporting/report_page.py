"""Assemble one path's source, target, image and layout evidence page."""

from truncator.common.capture_files import capture_image
from pathlib import Path
from truncator.planning.composition import capture_members
from truncator.planning.pages import resolve_page
from truncator.common.storage import read, save
from truncator.review.reporting.report_assets import (
    copy_capture,
    locate,
    som,
    source_changes,
    component_preview,
    escaped,
    json_block,
    document,
)

DESCRIPTIONS = {
    "freeze-viewport-width": "将宽窗口基线尺寸固定为vp，在同一HAP进入窄窗口后核验裁切",
    "window-edge-clip": "父容器整体偏移使目标越过所属窗口边界，实际限制边界由运行图树复核",
    "viewport-width-mismatch": "扩大已有Scroll布局宽度，检查后代越出当前窗口的图树关系",
    "scroll-recovery": "完整布局的内容置于较小滚动视口，恢复结果需操作验证",
    "whitespace-clip": "裁切目标尾部留白，文字完整性需前后图审核",
    "line-clip": "限制文字宽度和行数，使用Clip处理溢出",
    "ellipsis-width": "限制文字宽度并显示省略号",
    "ellipsis-lines": "减少文字最大行数并显示省略号",
    "height-clip": "限制组件高度并启用自身裁切",
    "width-clip": "限制组件宽度并启用自身裁切",
    "parent-clip": "添加尺寸受限的裁切父容器",
    "fixed-parent-clip": "固定子组件尺寸，缩小外部裁切容器",
    "translate-clip": "在局部裁切容器内平移目标",
    "ancestor-translate-clip": "平移目标并启用已有父容器裁切",
    "child-overflow-clip": "联动父容器约束与子组件内容放大",
    "overlay-occlusion": "插入不拦截触摸的不透明覆盖块",
    "sibling-translate-occlusion": "平移已有兄弟组件并调整层级形成遮挡",
    "sibling-position-occlusion": "定位已有兄弟组件并调整层级形成遮挡",
}


def write_page(run_row, page_name, recipe, folder):
    folder.mkdir(parents=True, exist_ok=True)
    run = Path(run_row["run"])
    plan = (
        read(run / "plan.json")
        if (run / "plan.json").exists()
        else read(run_row["plan"])
    )
    active = capture_members(plan, recipe)
    page = resolve_page(plan, recipe) if "pages" in plan else None
    baseline = (
        Path(page["baseline_capture"])
        if page
        else (
            Path(active[0]["geometry"]["baseline_capture"])
            if active and active[0].get("geometry")
            else None
        )
    )
    assessment = run_row.get("assessment") or {}
    captured = Path(assessment["capture"]) if assessment.get("capture") else None
    copy_capture(baseline, folder / "baseline")
    copy_capture(captured, folder / "mutated")
    targets, before_marks, after_marks = [], [], []
    member_numbers = {
        m["id"]: index for index, m in enumerate(plan.get("mutations", [plan]), 1)
    }
    for member in active:
        geometry = member.get("geometry", {})
        number = member_numbers[member["id"]]
        normal = locate(baseline, geometry.get("selector", {}))
        changed = locate(
            captured, geometry.get("mutated_selector", geometry.get("selector", {}))
        )
        if normal["status"] == "located":
            before_marks.append((number, normal["bounds"]))
        if changed["status"] == "located":
            after_marks.append((number, changed["bounds"]))
        decision = next(
            (
                d
                for d in plan.get("selection", {}).get("decisions", [])
                if d["selected"] == member["id"]
            ),
            None,
        )
        targets.append(
            {
                "number": number,
                "mutation_id": member["id"],
                "operator": member["operator"],
                "method": DESCRIPTIONS.get(member["operator"]),
                "source_site": member["site"],
                "related_sites": member.get("related_sites", []),
                "parameters": member["parameters"],
                "geometry": geometry,
                "selection": decision,
                "seed": plan.get("selection", {}).get("seed", member.get("seed")),
                "before": normal,
                "after": changed,
                "review": "pending",
                **({"construction_intent": member["construction_intent"]}
                   if member.get("construction_intent") else {}),
                "source_changes": (
                    source_changes(plan, member, run, folder)
                    if (run / "prepared.json").exists()
                    else []
                ),
            }
        )
        for kind, source, location in (
            ("before", baseline, normal),
            ("after", captured, changed),
        ):
            relative = "targets/" + member["id"] + "/" + kind + ".png"
            if component_preview(source, location, folder / relative):
                targets[-1][kind + "_preview"] = relative
    som(folder / "baseline", before_marks)
    som(folder / "mutated", after_marks)
    record = {
        "page": page_name,
        "run": str(run),
        "capture": str(captured) if captured else None,
        "status": run_row["status"],
        "error": run_row.get("error"),
        "recipe": recipe,
        "targets": targets,
        "som_semantics": "component bounds of injected targets; visual defect labels pending review",
    }
    profile = read(run / "profile.json")
    if profile.get("instrumentation"):
        mapping = read(profile["instrumentation"])
        for target in targets:
            identifier = target["geometry"].get("selector", {}).get("id", "")
            target["original_source_sites"] = [
                entry
                for entry in mapping["entries"]
                if identifier == entry["probe_prefix"]
                or (
                    entry["repeated"]
                    and identifier.startswith(entry["probe_prefix"])
                    and (
                        entry["probe_prefix"].startswith("truncator_context_")
                        or identifier[len(entry["probe_prefix"]) :].isdigit()
                    )
                )
            ]
    reviews = sorted(captured.glob("review-*.json")) if captured else []
    if reviews:
        from truncator.review.review_evidence import validate_single_review
        reviewed = read(reviews[-1])
        validate_single_review(captured, reviewed)
        record["capture_review"] = reviewed
        if len(targets) == 1:
            targets[0]["review"] = reviewed["decision"]
    save(folder / "evidence.json", record)
    body = '<p><a href="../../review.html">审核本应用缺陷</a> · <a href="../../../../index.html">返回运行总览</a> · <a href="evidence.json">完整记录JSON</a></p>'
    body += (
        "<p>SoM编号对应注入目标的组件框。原始截图单独保留，实际缺陷范围待人工校对。</p>"
    )
    body += "<p>运行状态 " + escaped(run_row["status"]) + "</p>"
    if record.get("capture_review"):
        body += "<h2>已记录的内容与恢复审核</h2>" + json_block(record["capture_review"])
    if run_row.get("error"):
        body += json_block(run_row["error"])
    body += '<div class="pair">'
    for kind, title in (("baseline", "正常页面"), ("mutated", "注入后页面")):
        body += "<section><h2>" + title + "</h2>"
        if (folder / kind / "som.png").exists():
            body += (
                '<a href="' + kind + '/som.png"><img src="' + kind + '/som.png"></a>'
            )
        for filename, label in (
            (capture_image(folder / kind).name, "原始截图"),
            ("tree-before.json", "截图前layout"),
            ("tree-after.json", "截图后layout"),
            ("replay.json", "逐步重放记录"),
            ("initial-state.json", "应用初始状态"),
            ("startup-waits.json", "启动恢复等待记录"),
            ("page-wait.json", "页面等待记录"),
            ("image-quality.json", "截图与目标一致性检查"),
            ("layout-impact.json", "布局影响记录"),
            ("logs/index.html", "命令日志"),
        ):
            if (folder / kind / filename).exists():
                body += ' <a href="' + kind + "/" + filename + '">' + label + "</a>"
        body += "</section>"
    body += (
        "</div><details><summary>到页操作配置</summary>"
        + json_block(recipe)
        + "</details>"
    )
    for target in targets:
        body += (
            '<article id="target-'
            + str(target["number"])
            + '"><h2>#'
            + str(target["number"])
            + " "
            + escaped(target["method"])
            + "</h2>"
        )
        body += (
            "<p>"
            + escaped(target["source_site"]["file"])
            + " · "
            + escaped(target["operator"])
            + "</p>"
        )
        body += '<div class="pair">'
        for kind, label in (("before", "修改前"), ("after", "修改后")):
            if target.get(kind + "_preview"):
                body += (
                    "<section><p>"
                    + label
                    + '</p><img style="max-height:300px;width:auto" src="'
                    + target[kind + "_preview"]
                    + '"></section>'
                )
        body += "</div>"
        body += (
            "<details open><summary>参数、计算依据与选择记录</summary>"
            + json_block(
                {
                    k: target[k]
                    for k in (
                        "parameters",
                        "geometry",
                        "selection",
                        "seed",
                        "before",
                        "after",
                    )
                }
            )
            + "</details>"
        )
        for change in target["source_changes"]:
            body += (
                "<h3>"
                + escaped(change["file"])
                + '</h3><p><a href="'
                + change["before_link"]
                + '">修改前第'
                + str(change["before_line"])
                + '行</a> · <a href="'
                + change["after_link"]
                + '">修改后第'
                + str(change["after_line"])
                + "行</a></p>"
            )
            body += (
                '<div class="pair"><pre>'
                + escaped(change["before"])
                + "</pre><pre>"
                + escaped(change["after"])
                + "</pre></div>"
            )
        body += "</article>"
    (folder / "index.html").write_text(document(page_name, body), encoding="utf-8")
    return record
