"""Assemble application reports and review forms from recorded batch results."""

from truncator.common.capture_files import capture_image
from pathlib import Path
import json
import shutil
from truncator.imaging.geometry import rectangle
from truncator.common.storage import read, save, digest

from truncator.review.reporting.report_assets import (
    escaped,
    document,
    json_block,
    copy_capture,
)
from truncator.review.reporting.report_page import write_page


def generate_report(destination, results=None):
    destination = Path(destination).resolve()
    if results is None:
        source = destination / "results.json"
        if not source.exists():
            source = destination / "batch-results.json"
        results = read(source)
    if results and all("run" in row and "plan" in row for row in results):
        results = [{"application": Path(row["plan"]).stem,
                    "status": row["status"], "error": row.get("error"),
                    "cases": [{"runs": [row]}]} for row in results]
    output = destination / "report"
    output.mkdir(exist_ok=True)
    manifest = {"applications": [], "errors": []}
    applications = {}
    body = "<p>每个编号关联构造方式、源码改动、参数、截图和layout。样本审核状态默认为待校对。</p>"
    for application_index, application in enumerate(results, 1):
        body += (
            "<section><h2>"
            + escaped(application.get("application", application_index))
            + "</h2>"
        )
        body += "<p>状态 " + escaped(application.get("status", "running")) + "</p>"
        if application.get("error"):
            body += json_block(application["error"])
        seen_runs = set()
        for page_index, page in enumerate(application.get("pages", [application]), 1):
            for case in page.get("cases", []):
                for row in case.get("runs", []):
                    recipe = (
                        page.get("recipe")
                        or (row.get("application") or {}).get("recipe")
                        or {}
                    )
                    name = page.get("name", "page-" + str(page_index))
                    try:
                        if not row.get("run"):
                            raise ValueError(row.get("error", "No run directory was prepared"))
                        run = Path(row["run"])
                        plan = read(run / "plan.json")
                        application_folder = output / "applications" / plan["id"]
                        slug = digest(json.dumps(recipe, sort_keys=True))[:12]
                        folder = application_folder / "paths" / slug
                        record = write_page(row, name, recipe, folder)
                        link = (folder / "index.html").relative_to(output).as_posix()
                        manifest["applications"].append(
                            {"page": name, "link": link, **record}
                        )
                        body += (
                            '<p><a href="'
                            + link
                            + '">'
                            + escaped(name)
                            + " · "
                            + str(len(record["targets"]))
                            + "个注入目标</a></p>"
                        )
                        group = applications.setdefault(
                            plan["id"],
                            {
                                "run": run,
                                "folder": application_folder,
                                "plan": plan,
                                "paths": [],
                            },
                        )
                        group["paths"].append(
                            {
                                "name": name,
                                "href": "paths/" + slug + "/index.html",
                                "capture": record["capture"],
                                "mutation_ids": [
                                    t["mutation_id"] for t in record["targets"]
                                ],
                            }
                        )
                        if row["run"] not in seen_runs:
                            seen_runs.add(row["run"])
                            logs = application_folder / "logs"
                            logs.mkdir(parents=True, exist_ok=True)
                            for filename in (
                                "plan.json",
                                "mutation.diff",
                                "build.json",
                                "events.jsonl",
                            ):
                                if (run / filename).exists():
                                    shutil.copy2(run / filename, logs / filename)
                            profile = read(run / "profile.json")
                            if profile.get("instrumentation"):
                                shutil.copy2(
                                    profile["instrumentation"], logs / "source-map.json"
                                )
                            for attempt in run.glob("build-*"):
                                if attempt.is_dir():
                                    shutil.copytree(
                                        attempt, logs / attempt.name, dirs_exist_ok=True
                                    )
                            for failure in run.glob("capture-*/failure.json"):
                                shutil.copytree(
                                    failure.parent,
                                    logs / failure.parent.name,
                                    dirs_exist_ok=True,
                                )
                                diagnostic = read(failure).get("diagnostics", {})
                                if diagnostic.get("path"):
                                    from truncator.execution.device.failure_evidence import validate_failure_evidence
                                    observed = validate_failure_evidence(logs / failure.parent.name)
                                    prefix = (logs / failure.parent.name).relative_to(output).as_posix()
                                    body += '<details><summary>失败现场：' + escaped(failure.parent.name) + '</summary>'
                                    body += '<p>采集失败；以下材料仅用于定位失败原因，不作为有效样本。</p>'
                                    if "image_size_px" in observed:
                                        body += '<img style="max-width:650px;width:100%" src="' + prefix + '/failure-evidence/snapshot.jpeg">'
                                    body += '<p><a href="' + prefix + '/failure-evidence/evidence.json">诊断记录</a></p></details>'
                            for f in sorted(logs.rglob("*")):
                                if f.is_file():
                                    body += (
                                        '<p><a href="'
                                        + f.relative_to(output).as_posix()
                                        + '">'
                                        + escaped(f.relative_to(logs))
                                        + "</a></p>"
                                    )
                            hap = (row.get("application") or {}).get("hap")
                            if hap:
                                expected = read(run / "build.json")["hap_sha256"]
                                if digest(Path(hap).read_bytes()) != expected:
                                    raise ValueError(
                                        "HAP hash differs from build record"
                                    )
                                shutil.copy2(hap, application_folder / "app.hap")
                                body += (
                                    '<p><a href="applications/'
                                    + plan["id"]
                                    + '/app.hap">本版应用包</a> · <a href="applications/'
                                    + plan["id"]
                                    + '/review.html">按缺陷审核</a></p>'
                                )
                    except (ValueError, OSError, KeyError) as error:
                        manifest["errors"].append(
                            {"page": name, "run": row.get("run"), "error": str(error)}
                        )
                        body += (
                            "<p>报告生成失败 "
                            + escaped(name)
                            + " "
                            + escaped(error)
                            + "</p>"
                        )
        body += "</section>"
    from truncator.review.reporting.review_ui import write_review
    from truncator.review.review_evidence import recorded_review

    for group in applications.values():
        build_file = group["run"] / "build.json"
        template = None
        if build_file.exists():
            template = write_review(
                group["folder"],
                group["plan"],
                read(build_file),
                group["run"],
                group["paths"],
            )
        review = recorded_review(group["run"])
        if (
            review
            and template
            and review.get("schema_version") == 2
            and review.get("captures") == template["captures"]
        ):
            save(group["folder"] / "review-decisions.json", review)
            decisions = [item["decision"] for item in review["decisions"].values()]
            counts = {
                decision: decisions.count(decision)
                for decision in ("keep", "remove", "pending")
            }
            manifest.setdefault("reviews", []).append(
                {"plan_id": group["plan"]["id"], **counts}
            )
            body += (
                "<p>已记录审核 "
                + escaped(group["plan"]["id"])
                + json_block(counts)
                + "</p>"
            )
        configured = [page["recipe"] for page in group["plan"].get("pages", [])]
        selected_captures = {
            Path(page["capture"]).resolve()
            for page in group["paths"]
            if page.get("capture")
        }
        for capture_file in sorted(group["run"].glob("capture-*/capture.json")):
            capture_record = read(capture_file)
            if (
                capture_record.get("recipe") in configured
                or capture_file.parent.resolve() in selected_captures
            ):
                continue
            check_folder = group["folder"] / "checks" / capture_file.parent.name
            copy_capture(capture_file.parent, check_folder)
            check_body = '<p><a href="../../../../index.html">返回总览</a> · <a href="replay.json">逐步执行记录</a> · <a href="tree-before.json">layout</a> · <a href="logs/index.html">命令日志</a></p>'
            check_body += json_block(capture_record)
            check_body += '<img style="max-width:100%" src="' + capture_image(check_folder).name + '">'
            (check_folder / "index.html").write_text(
                document("补充交互检查", check_body), encoding="utf-8"
            )
            link = (check_folder / "index.html").relative_to(output).as_posix()
            body += (
                '<p><a href="'
                + link
                + '">补充交互检查 '
                + escaped(capture_file.parent.name)
                + "</a></p>"
            )
            manifest.setdefault("additional_captures", []).append(
                {
                    "plan_id": group["plan"]["id"],
                    "link": link,
                    "recipe": capture_record.get("recipe"),
                }
            )
    summary = {}
    for group in applications.values():
        for member in group["plan"].get("mutations", [group["plan"]]):
            counts = summary.setdefault(
                member["operator"], {"selected": 0, "captured": 0, "bounds_differ": 0}
            )
            counts["selected"] += 1
            observations = [
                target
                for page in manifest["applications"]
                if page["run"] == str(group["run"])
                for target in page["targets"]
                if target["mutation_id"] == member["id"]
            ]
            located = [
                target
                for target in observations
                if target["after"]["status"] == "located"
            ]
            counts["captured"] += bool(located)
            counts["bounds_differ"] += any(
                target["after"].get("origBounds")
                and rectangle(target["after"]["origBounds"])
                != target["after"]["bounds"]
                for target in located
            )
    save(output / "construction-summary.json", summary)
    body += (
        "<section><h2>构造与采集统计</h2><p>按应用内缺陷ID去重。边界差异来自布局树，视觉合格情况由审核记录确认。</p>"
        + json_block(summary)
        + "</section>"
    )
    save(output / "manifest.json", manifest)
    (output / "index.html").write_text(
        document("截断注入运行报告", body), encoding="utf-8"
    )
    return output / "index.html"
