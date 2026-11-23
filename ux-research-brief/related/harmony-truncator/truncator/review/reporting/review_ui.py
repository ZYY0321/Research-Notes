"""Offline defect-level review form; only explicit decisions affect later builds."""

import html
import json
from pathlib import Path

from truncator.review.review_policy import review_template
from truncator.common.storage import save, digest
from truncator.review.review_evidence import capture_identity, recorded_review


def write_review(folder, plan, build_record, run, paths):
    from truncator.review.reporting.report_assets import document

    pages = {page["name"]: page for page in plan.get("pages", [])}
    captures = [
        capture_identity(run, pages[path["name"]], path["capture"])
        for path in paths
        if path.get("capture") and path["name"] in pages
    ]
    template = review_template(plan, build_record["hap_sha256"], captures)
    saved = recorded_review(run)
    if (
        saved
        and saved["plan_id"] == plan["id"]
        and saved["hap_sha256"] == build_record["hap_sha256"]
        and saved.get("captures") == captures
    ):
        template["decisions"] = saved["decisions"]
        template["review_revision"] = digest(json.dumps(saved, sort_keys=True))[:16]
    save(folder / "review-template.json", template)
    occurrences = {
        member["id"]: [
            page["name"]
            for page in plan.get("pages", [])
            if member["id"] in page["mutation_ids"]
        ]
        for member in plan.get("mutations", [plan])
    }
    save(folder / "mutation-occurrences.json", occurrences)
    rows = []
    for number, member in enumerate(plan.get("mutations", [plan]), 1):
        key = member["id"]
        links = " ".join(
            '<a href="'
            + html.escape(path["href"])
            + "#target-"
            + str(number)
            + '">'
            + html.escape(path["name"])
            + "</a>"
            for path in paths
            if key in path["mutation_ids"]
        )
        rows.append(
            '<tr data-mutation="'
            + key
            + '"><td>'
            + str(number)
            + "</td><td>"
            + html.escape(member["operator"])
            + "<br>"
            + html.escape(member["site"]["file"])
            + "</td><td>"
            + links
            + '</td><td><select aria-label="审核决定">'
            '<option value="pending">待定</option><option value="keep">保留</option>'
            '<option value="remove">移除</option></select></td>'
            '<td><select data-field="content_status" aria-label="目标内容状态">'
            '<option value="">未标注</option><option value="clipped">可见内容缺失</option>'
            '<option value="complete">内容完整</option><option value="uncertain">待核实</option></select></td>'
            '<td><select data-field="recovery_status" aria-label="目标恢复状态">'
            '<option value="">未标注</option><option value="recovered">已恢复</option>'
            '<option value="not-recovered">已测操作未恢复</option>'
            '<option value="inconclusive">已尝试，证据不足</option>'
            '<option value="not-tested">未测试</option><option value="not-applicable">无需恢复</option></select></td>'
            '<td><textarea aria-label="个人备注" rows="3"></textarea></td></tr>'
        )
    command = (
        'python -m truncator curate --run "'
        + str(run)
        + '" --review "审核文件.json" --out "新版本目录" --device 127.0.0.1:5555'
    )
    body = (
        '<p><a href="../../index.html">返回总览</a> · <a href="app.hap">下载本版应用包</a></p>'
        "<p>整批审核后下载决定文件，用下方命令生成新版。待定保留当前补丁，备注仅供个人记录。"
        "每个缺陷的联动修改作为一组移除。同一修改出现在多条路径时，移除会同时恢复这些位置。"
        "新版重新采集全部路径，审核状态重新标为待定。</p>"
        '<p><a href="mutation-occurrences.json">各缺陷组的关联路径记录</a></p>'
        "<p>浏览器自动保存尽力提供，下载的JSON是跨会话保存和构建的输入。</p>"
        "<p>内容状态与恢复状态需同时填写，或同时留空。恢复结论对应备注中记录的操作与证据；保留决定用于样本筛选。</p>"
        '<button id="download">下载审核决定</button> '
        '<label>载入已保存决定 <input id="import" type="file" accept=".json"></label>'
        '<p id="status" role="status"></p><table><thead><tr><th>编号</th><th>构造与源码</th>'
        "<th>关联路径</th><th>决定</th><th>内容状态</th><th>恢复状态</th><th>备注与证据</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table><pre>"
        + html.escape(command)
        + "</pre>"
    )
    payload = json.dumps(template, ensure_ascii=False).replace("<", "\\u003c")
    script = Path(__file__).with_name("review.js").read_text(encoding="utf-8")
    body += (
        '<script type="application/json" id="template">'
        + payload
        + "</script><script>"
        + script
        + "</script>"
    )
    (folder / "review.html").write_text(
        document("应用缺陷审核", body), encoding="utf-8"
    )
    return template
