#!/usr/bin/env python3
"""Write zyy-e31-nologin-v1 task files from the spec list."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOME = "~/Desktop/e31-nologin"
BATCH = "zyy-e31-nologin-v1-1122"

APPS = {
    "TextEdit": ("TextEdit", ["com.apple.TextEdit"]),
    "Preview": ("Preview", ["com.apple.Preview"]),
    "Notes": ("Notes", ["com.apple.Notes"]),
    "Reminders": ("Reminders", ["com.apple.reminders"]),
    "Calendar": ("Calendar", ["com.apple.iCal"]),
    "Finder": ("Finder", ["com.apple.finder"]),
    "Photos": ("Photos", ["com.apple.Photos"]),
    "Shortcuts": ("Shortcuts", ["com.apple.shortcuts"]),
}

FILE_BYPASS = "纯文本和 textutil 转出的 RTF 没有文本编辑的窗口署名，得 0。用 AppleScript 让文本编辑自己存储，会带上同样的署名，这是残留绕过。"
PDF_BYPASS = "复制原 PDF、或用 sips 重渲染，得 0。手写一份带同样批注字典的 PDF 仍可能得分。"
ALIAS_BYPASS = "ln -s 符号链接得 0。用 AppleScript 让访达制作替身，会得到同样的书签文件。"
VIEW_BYPASS = "只含视图单词的文本文件得 0。手写一份 Bud1 的 .DS_Store 仍可能得分。"
APP_BYPASS = "桌面上的文本或导出文件不参与评分，得 0。用 AppleScript 直接改这个应用，会得到同样的终态，这是残留绕过。"
SHORTCUT_BYPASS = "桌面文件得 0。快捷指令的脚本字典不能新建快捷指令。若把记录直接写进它的数据库，仍可能绕过。"


def face(text, cloud=False):
    extra = "请在应用窗口里完成。只在终端里写出同名文件，不算完成。"
    if cloud:
        extra += "若出现 iCloud、登录或欢迎窗口，选择以后再说或只用这台 Mac 本机，不要登录。"
    return text.strip() + "\n" + extra


def state(name):
    return HOME + "/state/" + name


def out(name):
    return HOME + "/out/" + name


def seed(name):
    return HOME + "/seed/" + name


def mark(task_id):
    return state(task_id + "-mark.txt")


def today_path():
    return state("today.txt")


def token_path(task_id):
    return state(task_id + "-seed.txt")


def photo_path(task_id):
    return state(task_id + "-photo.txt")


def base(task_id, app, feature, instruction, fixture, grade_note, bypass, params, opens, seeds=None, clear=None, outputs=None, timeout=90, **extra):
    row = {
        "id": task_id,
        "app": app,
        "apps": app if isinstance(app, list) else [app],
        "feature": feature,
        "instruction": instruction,
        "fixture": fixture,
        "grade_note": grade_note,
        "bypass": bypass,
        "params": params,
        "opens": opens,
        "seeds": seeds or [],
        "clear": clear or [],
        "outputs": outputs or [],
        "timeout": timeout,
    }
    row.update(extra)
    return row


def rtf_task(task_id, feature, instruction, path, note, contains=None, exact=None, forbids=None, bold=False, order=False, keep=None, seeds=None, clear=None, opens=None, empty="absent", seed_text="", good_text="", in_place=False):
    params = {
        "kind": "textedit_rtf",
        "path": path,
        "marker_file": mark(task_id),
        "grade_note": note,
    }
    if exact is not None:
        params["exact"] = exact
    if contains:
        params["contains"] = contains
    if forbids:
        params["forbids"] = forbids
    if bold:
        params["bold"] = True
        params["bold_text"] = "{marker}"
    if order:
        params["order"] = True
    if keep:
        params["keep_path"] = keep["path"]
        params["keep_contains"] = keep["contains"]
        params["keep_lacks"] = "{marker}"
    outputs = [] if in_place else [{"name": task_id, "path": path}]
    if in_place:
        outputs = [{"name": task_id, "path": path}]
    return base(
        task_id, "TextEdit", feature, instruction, "rtf", note, FILE_BYPASS, params,
        opens or [{"name": "TextEdit", "file": path}],
        seeds=seeds, clear=clear if clear is not None else [path], outputs=outputs,
        empty=empty, seed_text=seed_text, good_text=good_text, bold=bold,
        keep_file=keep.get("file") if keep else None,
    )


def pdf_task(task_id, feature, instruction, mode, note, angle=None):
    src = seed(task_id + ".pdf")
    dest = out(task_id + ".pdf")
    params = {
        "kind": "preview_pdf",
        "path": dest,
        "mode": mode,
        "marker_file": mark(task_id),
        "seed_token_file": token_path(task_id),
        "keep_path": src,
        "keep_contains": "{seed}",
        "keep_lacks": "{marker}",
        "grade_note": note,
    }
    if angle is not None:
        params["angle"] = angle
    return base(
        task_id, "Preview", feature, instruction, "pdf", note, PDF_BYPASS, params,
        [{"name": "Preview", "file": src}],
        seeds=[{"kind": "pdf", "path": src, "token_file": token_path(task_id)}],
        clear=[dest],
        outputs=[{"name": task_id, "path": dest}],
        keep_file="pdf",
    )


def app_task(task_id, app, feature, instruction, note, where, good_record, opens=None, seeds=None, clear=None, timeout=120, bypass=None, cloud=True):
    params = {
        "kind": "app_state",
        "app": {
            "Notes": "notes",
            "Reminders": "reminders",
            "Calendar": "calendar",
            "Photos": "photos",
            "Shortcuts": "shortcuts",
        }[app],
        "marker_file": mark(task_id),
        "where": where,
        "grade_note": note,
    }
    if app in ("Reminders", "Calendar"):
        params["today_file"] = today_path()
    if app == "Photos" and any(clause.get("field") == "FILENAME" for clause in where):
        params["photo_file"] = photo_path(task_id)
    return base(
        task_id, app, feature, instruction, "app", note, bypass or APP_BYPASS, params,
        opens or [{"name": app}],
        seeds=seeds, clear=clear or [], outputs=[], timeout=timeout,
        good_record=good_record, cloud=cloud,
    )


def textedit_specs():
    rows = []
    path = out("te-rtf-marker.rtf")
    rows.append(rtf_task(
        "te-rtf-marker", "新建富文本",
        face("文本编辑已经打开。请新建一份富文本，不要存成纯文本。要写的那一行在 %s 的第一行（E31- 加 6 位字符，每次运行都会换）。正文只放这一行。存到 %s。" % (mark("te-rtf-marker"), path)),
        path, "正文去掉空白后必须正好是标记，并且文件带文本编辑存储时写上的窗口字段。",
        exact="{marker}", good_text="{marker}",
        opens=[{"name": "TextEdit"}],
    ))
    path = seed("te-rtf-append.rtf")
    rows.append(rtf_task(
        "te-rtf-append", "在已有富文本末尾加一行",
        face("文本编辑会打开 %s。里面已经有一句 KEEP-THIS-SENTENCE。请保留这句，另起一行写上 %s 第一行的标记。用文本编辑存回这个文件，格式仍是富文本。" % (path, mark("te-rtf-append"))),
        path, "保留 KEEP-THIS-SENTENCE，并在它后面出现标记。纯文本或 textutil 转档没有窗口字段。",
        contains=["KEEP-THIS-SENTENCE", "{marker}"], order=True,
        seeds=[{"kind": "rtf", "path": path, "text": "KEEP-THIS-SENTENCE\n"}],
        clear=[path], empty="plain", seed_text="KEEP-THIS-SENTENCE\n", good_text="KEEP-THIS-SENTENCE\n{marker}",
        in_place=True,
    ))
    path = seed("te-rtf-replace.rtf")
    rows.append(rtf_task(
        "te-rtf-replace", "替换指定单词",
        face("文本编辑会打开 %s。请把其中的 TOKEN 换成 %s 第一行的标记，KEEP-THIS-SENTENCE 要留下。用文本编辑存回这个文件，格式仍是富文本。" % (path, mark("te-rtf-replace"))),
        path, "标记替换 TOKEN，原句还在。文件里不能再出现 TOKEN。",
        contains=["KEEP-THIS-SENTENCE", "{marker}"], forbids=["TOKEN"],
        seeds=[{"kind": "rtf", "path": path, "text": "KEEP-THIS-SENTENCE TOKEN\n"}],
        clear=[path], empty="plain", seed_text="KEEP-THIS-SENTENCE TOKEN\n",
        good_text="KEEP-THIS-SENTENCE {marker}", in_place=True,
    ))
    path = out("te-rtf-bold.rtf")
    rows.append(rtf_task(
        "te-rtf-bold", "把标记设为粗体",
        face("文本编辑已经打开。请新建富文本，写入 %s 第一行的标记，并把这行设为粗体。存到 %s。" % (mark("te-rtf-bold"), path)),
        path, "标记必须落在粗体开关之间，同时要有文本编辑的窗口字段。",
        contains=["{marker}"], bold=True, good_text="{marker}",
        opens=[{"name": "TextEdit"}],
    ))
    path = out("te-rtf-two.rtf")
    rows.append(rtf_task(
        "te-rtf-two", "两行议程",
        face("文本编辑已经打开。请新建富文本，第一行写 AGENDA，第二行写 %s 第一行的标记。不要写别的字。存到 %s。" % (mark("te-rtf-two"), path)),
        path, "AGENDA 在前，标记在后。",
        contains=["AGENDA", "{marker}"], order=True, good_text="AGENDA\n{marker}",
        opens=[{"name": "TextEdit"}],
    ))
    src = seed("te-rtf-keep.txt")
    path = out("te-rtf-keep.rtf")
    rows.append(rtf_task(
        "te-rtf-keep", "另存一份，不改原稿",
        face("桌面上有原稿 %s，里面是 KEEP-THIS-SENTENCE 和 TOKEN。请用文本编辑另存一份富文本到 %s：留下 KEEP-THIS-SENTENCE，把 TOKEN 换成 %s 第一行的标记。不要改原稿。" % (src, path, mark("te-rtf-keep"))),
        path, "新文件是带窗口字段的富文本；原稿仍含 TOKEN，且没有这次的标记。",
        contains=["KEEP-THIS-SENTENCE", "{marker}"], forbids=["TOKEN"],
        keep={"path": src, "contains": "TOKEN", "file": "TOKEN\nKEEP-THIS-SENTENCE\n"},
        seeds=[{"kind": "text", "path": src, "text": "TOKEN\nKEEP-THIS-SENTENCE\n"}],
        clear=[path], good_text="KEEP-THIS-SENTENCE {marker}",
        opens=[{"name": "TextEdit", "file": src}],
    ))
    return rows


def preview_specs():
    notes = {
        "freetext": "在副本上加一条自由文本批注，内容是标记；原页上的 SEED- 那行还在。批注要带预览写进 PDF 的富文本字段。",
        "sticky": "在副本上加一张便签批注，文字是标记；原页上的 SEED- 那行还在。",
        "highlight": "把页面上 SEED- 开头的那行高亮，存成副本。不要删掉那行文字。",
        "rotate": "把这一页按给定角度旋转后另存。页面上的 SEED- 那行要还在，不要把页面重画成一张图。",
        "crop": "把页面裁成上半部分后另存。媒体框仍是原来的整页，裁剪框盖住上半页。SEED- 那行要还在。",
    }
    rows = []
    catalog = [
        ("pv-freetext", "自由文本批注", "freetext", None,
         "预览会打开 {src}。页面上有一行 SEED- 开头的文字。请加一条自由文本批注，内容是 {mark} 第一行的标记，另存到 {dest}。不要删原来的 SEED- 那行，也不要改原稿。"),
        ("pv-sticky", "便签批注", "sticky", None,
         "预览会打开 {src}。请加一张便签，里面只写 {mark} 第一行的标记，另存到 {dest}。不要删页面上的 SEED- 那行，也不要改原稿。"),
        ("pv-highlight", "高亮一行", "highlight", None,
         "预览会打开 {src}。请把页面上 SEED- 开头的那一行高亮，另存到 {dest}。不要删那行，也不要改原稿。标记文件 {mark} 这次不用写进批注。"),
        ("pv-rotate-90", "顺时针转 90 度", "rotate", 90,
         "预览会打开 {src}。请把这一页顺时针旋转 90 度，另存到 {dest}。不要删页面上的 SEED- 那行，也不要把页面导出成图片。不要改原稿。"),
        ("pv-rotate-180", "旋转 180 度", "rotate", 180,
         "预览会打开 {src}。请把这一页旋转 180 度，另存到 {dest}。不要删页面上的 SEED- 那行，也不要改原稿。"),
        ("pv-crop-top", "裁成上半页", "crop", None,
         "预览会打开 {src}。请把页面裁成上半部分（大约从页面中线裁到顶边），另存到 {dest}。整页的媒体框保持原样。不要删 SEED- 那行，也不要改原稿。"),
    ]
    for task_id, feature, mode, angle, template in catalog:
        src = seed(task_id + ".pdf")
        dest = out(task_id + ".pdf")
        text = template.format(src=src, mark=mark(task_id), dest=dest)
        row = pdf_task(task_id, feature, face(text), mode, notes[mode] if mode != "rotate" else notes["rotate"], angle)
        rows.append(row)
    return rows


def notes_specs():
    brief = seed("notes-sentence.txt")
    attach = seed("notes-brief.txt")
    rows = [
        app_task(
            "notes-title", "Notes", "新建备忘，标题为标记",
            face("备忘录已经打开。请新建一条备忘，第一行只写 %s 第一行的标记。不要登录。" % mark("notes-title"), cloud=True),
            "备忘录里要有一条备忘，名称等于标记。桌面上的文本不算。",
            [{"field": "NAME", "eq": "{marker}"}],
            {"KIND": "note", "NAME": "{marker}", "PLAIN": "{marker}", "FOLDER": "备忘录", "BODY": "", "ATTACH": ""},
        ),
        app_task(
            "notes-sentence", "Notes", "把种子句抄进备忘",
            face("备忘录已经打开。请读 %s，把里面的 KEEP-THIS-SENTENCE 原样写进一条新备忘，并另起一行写上 %s 第一行的标记。" % (brief, mark("notes-sentence")), cloud=True),
            "这条备忘的纯文本里同时有种子句和标记。",
            [{"field": "PLAIN", "has": "KEEP-THIS-SENTENCE"}, {"field": "PLAIN", "has": "{marker}"}],
            {"KIND": "note", "NAME": "KEEP-THIS-SENTENCE", "PLAIN": "KEEP-THIS-SENTENCE {marker}", "FOLDER": "备忘录", "BODY": "", "ATTACH": ""},
            seeds=[{"kind": "text", "path": brief, "text": "KEEP-THIS-SENTENCE\n"}],
            opens=[{"name": "Notes"}, {"name": "TextEdit", "file": brief}],
        ),
        app_task(
            "notes-folder", "Notes", "新建文件夹并在里面写备忘",
            face("备忘录已经打开。请新建一个文件夹，名字是 %s 第一行的标记；在这个文件夹里新建一条备忘，正文也包含同一个标记。" % mark("notes-folder"), cloud=True),
            "备忘的所在文件夹名称等于标记，纯文本里也有标记。",
            [{"field": "FOLDER", "eq": "{marker}"}, {"field": "PLAIN", "has": "{marker}"}],
            {"KIND": "note", "NAME": "{marker}", "PLAIN": "{marker}", "FOLDER": "{marker}", "BODY": "", "ATTACH": ""},
        ),
        app_task(
            "notes-attach", "Notes", "把种子文件附进备忘",
            face("备忘录已经打开。请新建一条备忘，正文包含 %s 第一行的标记，并把 %s 作为附件放进这条备忘。不要只把文件留在桌面。" % (mark("notes-attach"), attach), cloud=True),
            "备忘纯文本含标记，附件名里有 notes-brief.txt。",
            [{"field": "PLAIN", "has": "{marker}"}, {"field": "ATTACH", "has": "notes-brief.txt"}],
            {"KIND": "note", "NAME": "{marker}", "PLAIN": "{marker}", "FOLDER": "备忘录", "BODY": "", "ATTACH": "notes-brief.txt,"},
            seeds=[{"kind": "text", "path": attach, "text": "brief\n"}],
        ),
        app_task(
            "notes-two", "Notes", "备忘里写两行固定内容",
            face("备忘录已经打开。请新建一条备忘，正文里先出现 AGENDA，再出现 %s 第一行的标记。" % mark("notes-two"), cloud=True),
            "纯文本里 AGENDA 和标记都在。",
            [{"field": "PLAIN", "has": "AGENDA"}, {"field": "PLAIN", "has": "{marker}"}],
            {"KIND": "note", "NAME": "AGENDA", "PLAIN": "AGENDA {marker}", "FOLDER": "备忘录", "BODY": "", "ATTACH": ""},
        ),
    ]
    return rows


def reminder_specs():
    rows = [
        app_task(
            "rem-name", "Reminders", "新建一条提醒",
            face("提醒事项已经打开。请新建一条提醒，标题是 %s 第一行的标记。" % mark("rem-name"), cloud=True),
            "提醒标题等于标记。",
            [{"field": "NAME", "eq": "{marker}"}],
            {"KIND": "reminder", "NAME": "{marker}", "BODY": "", "LIST": "提醒事项", "COMPLETED": "false", "FLAGGED": "false", "PRIORITY": "0", "DUE": ""},
        ),
        app_task(
            "rem-body", "Reminders", "给提醒写备注",
            face("提醒事项已经打开。请新建一条提醒，标题写 E31提醒，备注里只写 %s 第一行的标记。" % mark("rem-body"), cloud=True),
            "标题是 E31提醒，备注含标记。",
            [{"field": "NAME", "eq": "E31提醒"}, {"field": "BODY", "has": "{marker}"}],
            {"KIND": "reminder", "NAME": "E31提醒", "BODY": "{marker}", "LIST": "提醒事项", "COMPLETED": "false", "FLAGGED": "false", "PRIORITY": "0", "DUE": ""},
        ),
        app_task(
            "rem-complete", "Reminders", "把提醒标成已完成",
            face("提醒事项已经打开。请新建一条提醒，标题是 %s 第一行的标记，并把它标为已完成。" % mark("rem-complete"), cloud=True),
            "标题等于标记，且已完成。",
            [{"field": "NAME", "eq": "{marker}"}, {"field": "COMPLETED", "eq": "true"}],
            {"KIND": "reminder", "NAME": "{marker}", "BODY": "", "LIST": "提醒事项", "COMPLETED": "true", "FLAGGED": "false", "PRIORITY": "0", "DUE": ""},
        ),
        app_task(
            "rem-high", "Reminders", "把提醒设为高优先级",
            face("提醒事项已经打开。请新建一条提醒，标题是 %s 第一行的标记，优先级设为高。" % mark("rem-high"), cloud=True),
            "标题等于标记，优先级数字在 1 到 4（提醒事项里的高）。",
            [{"field": "NAME", "eq": "{marker}"}, {"field": "PRIORITY", "gte": 1, "lte": 4}],
            {"KIND": "reminder", "NAME": "{marker}", "BODY": "", "LIST": "提醒事项", "COMPLETED": "false", "FLAGGED": "false", "PRIORITY": "1", "DUE": ""},
        ),
        app_task(
            "rem-flag", "Reminders", "给提醒加旗标",
            face("提醒事项已经打开。请新建一条提醒，标题是 %s 第一行的标记，并加上旗标。" % mark("rem-flag"), cloud=True),
            "标题等于标记，且已加旗标。",
            [{"field": "NAME", "eq": "{marker}"}, {"field": "FLAGGED", "eq": "true"}],
            {"KIND": "reminder", "NAME": "{marker}", "BODY": "", "LIST": "提醒事项", "COMPLETED": "false", "FLAGGED": "true", "PRIORITY": "0", "DUE": ""},
        ),
        app_task(
            "rem-due", "Reminders", "设置明天早上的截止时间",
            face("提醒事项已经打开。今天的日期写在 %s 第一行。请新建一条提醒，标题是 %s 第一行的标记，截止时间是明天 09:00。" % (today_path(), mark("rem-due")), cloud=True),
            "标题等于标记，截止时间是状态文件里「今天」的下一天 09:00。",
            [{"field": "NAME", "eq": "{marker}"}, {"field": "DUE", "prefix": "{tomorrow}T09:00"}],
            {"KIND": "reminder", "NAME": "{marker}", "BODY": "", "LIST": "提醒事项", "COMPLETED": "false", "FLAGGED": "false", "PRIORITY": "0", "DUE": "{tomorrow}T09:00"},
        ),
    ]
    return rows


def calendar_specs():
    rows = [
        app_task(
            "cal-timed", "Calendar", "新建今天下午的日程",
            face("日历已经打开。今天的日期在 %s。请在本机日历里新建日程，标题是 %s 第一行的标记，开始 15:00，结束 16:00，不要做成全天。" % (today_path(), mark("cal-timed")), cloud=True),
            "标题等于标记，开始今天 15:00，结束今天 16:00，不是全天。",
            [
                {"field": "SUMMARY", "eq": "{marker}"},
                {"field": "START", "prefix": "{today}T15:00"},
                {"field": "END", "prefix": "{today}T16:00"},
                {"field": "ALLDAY", "eq": "false"},
            ],
            {"KIND": "event", "SUMMARY": "{marker}", "LOCATION": "", "DESCRIPTION": "", "START": "{today}T15:00", "END": "{today}T16:00", "ALLDAY": "false", "ALARM": ""},
        ),
        app_task(
            "cal-location", "Calendar", "给日程填地点",
            face("日历已经打开。请新建日程，标题写 E31会面，地点写成 %s 第一行的标记。时间可以是今天下午一点到两点。" % mark("cal-location"), cloud=True),
            "标题是 E31会面，地点等于标记。",
            [{"field": "SUMMARY", "eq": "E31会面"}, {"field": "LOCATION", "eq": "{marker}"}],
            {"KIND": "event", "SUMMARY": "E31会面", "LOCATION": "{marker}", "DESCRIPTION": "", "START": "{today}T13:00", "END": "{today}T14:00", "ALLDAY": "false", "ALARM": ""},
        ),
        app_task(
            "cal-description", "Calendar", "给日程写备注",
            face("日历已经打开。请新建日程，标题写 E31备注，备注里写上 %s 第一行的标记。" % mark("cal-description"), cloud=True),
            "标题是 E31备注，备注含标记。",
            [{"field": "SUMMARY", "eq": "E31备注"}, {"field": "DESCRIPTION", "has": "{marker}"}],
            {"KIND": "event", "SUMMARY": "E31备注", "LOCATION": "", "DESCRIPTION": "{marker}", "START": "{today}T13:00", "END": "{today}T14:00", "ALLDAY": "false", "ALARM": ""},
        ),
        app_task(
            "cal-allday", "Calendar", "新建明天的全天日程",
            face("日历已经打开。今天的日期在 %s。请新建一条全天日程，日期是明天，标题是 %s 第一行的标记。" % (today_path(), mark("cal-allday")), cloud=True),
            "全天，标题等于标记，日期是今天的下一天。",
            [{"field": "SUMMARY", "eq": "{marker}"}, {"field": "ALLDAY", "eq": "true"}, {"field": "START", "prefix": "{tomorrow}"}],
            {"KIND": "event", "SUMMARY": "{marker}", "LOCATION": "", "DESCRIPTION": "", "START": "{tomorrow}T00:00", "END": "{tomorrow}T23:59", "ALLDAY": "true", "ALARM": ""},
        ),
        app_task(
            "cal-alarm", "Calendar", "提前 15 分钟提醒",
            face("日历已经打开。请新建日程，标题是 %s 第一行的标记，并加一个提前 15 分钟的提醒。" % mark("cal-alarm"), cloud=True),
            "标题等于标记，显示提醒的触发间隔是 -15 分钟。",
            [{"field": "SUMMARY", "eq": "{marker}"}, {"field": "ALARM", "eq": "-15"}],
            {"KIND": "event", "SUMMARY": "{marker}", "LOCATION": "", "DESCRIPTION": "", "START": "{today}T15:00", "END": "{today}T16:00", "ALLDAY": "false", "ALARM": "-15"},
        ),
    ]
    return rows


def finder_specs():
    rows = []
    folder = seed("find-alias")
    alias = out("find-alias")
    rows.append(base(
        "find-alias", "Finder", "给指定文件做替身",
        face("访达会打开 %s。里面有 target.txt、note-a.txt、note-b.txt。请给 target.txt 做一个替身，存到 %s。不要用符号链接代替替身。" % (folder, alias)),
        "alias",
        "替身文件以书签头开始，并且指向 target.txt。符号链接得 0。",
        ALIAS_BYPASS,
        {"kind": "finder_alias", "path": alias, "target_name": "target.txt", "marker_file": mark("find-alias"), "grade_note": "替身文件以书签头开始，并且指向 target.txt。符号链接得 0。"},
        [{"name": "Finder", "file": folder}],
        seeds=[{"kind": "bundle", "path": folder, "names": ["target.txt", "note-a.txt", "note-b.txt"]}],
        clear=[alias],
        outputs=[{"name": "find-alias", "path": alias}],
        target_name="target.txt",
    ))
    views = [
        ("find-icon", "图标视图", "icnv", "图标"),
        ("find-list", "列表视图", "Nlsv", "列表"),
        ("find-column", "分栏视图", "clmv", "分栏"),
    ]
    for task_id, feature, code, label in views:
        folder = seed(task_id)
        store = folder + "/.DS_Store"
        rows.append(base(
            task_id, "Finder", "把文件夹改成" + feature,
            face("访达会打开 %s。请把这个窗口的显示方式改成%s，然后关掉窗口，让访达把视图写进该文件夹的 .DS_Store。" % (folder, label)),
            "view",
            " .DS_Store 是 Bud1，并且视图记录是 %s。普通文本得 0。" % code,
            VIEW_BYPASS,
            {"kind": "finder_view", "path": store, "view": code, "grade_note": ".DS_Store 是 Bud1，并且视图记录是 %s。" % code},
            [{"name": "Finder", "file": folder}],
            seeds=[{"kind": "bundle", "path": folder, "names": ["one.txt", "two.txt"]}],
            clear=[store],
            outputs=[{"name": task_id + "-dsstore", "path": store}],
            view=code,
        ))
    return rows


def photos_specs():
    folder = seed("photos-import")
    rows = [
        app_task(
            "photos-album", "Photos", "新建相簿",
            face("照片已经打开。请新建一个相簿，名字是 %s 第一行的标记。不要登录 iCloud。" % mark("photos-album"), cloud=True),
            "照片图库里有一个相簿，名字等于标记。",
            [{"field": "KIND", "eq": "album"}, {"field": "NAME", "eq": "{marker}"}],
            {"KIND": "album", "NAME": "{marker}"},
            timeout=150,
        ),
        app_task(
            "photos-folder", "Photos", "新建文件夹",
            face("照片已经打开。请新建一个文件夹，名字是 %s 第一行的标记。不要登录 iCloud。" % mark("photos-folder"), cloud=True),
            "照片图库里有一个文件夹，名字等于标记。",
            [{"field": "KIND", "eq": "folder"}, {"field": "NAME", "eq": "{marker}"}],
            {"KIND": "folder", "NAME": "{marker}"},
            timeout=150,
        ),
        app_task(
            "photos-import", "Photos", "导入种子图片",
            face("照片已经打开。请把 %s 里的那张 PNG 导入图库。文件名里带有这次的标记。不要登录。" % folder, cloud=True),
            "图库里有一张图，文件名等于状态文件里记下的名字。只把 PNG 留在桌面得 0。",
            [{"field": "KIND", "eq": "item"}, {"field": "FILENAME", "eq": "{photo}"}],
            {"KIND": "item", "NAME": "{photo}", "FILENAME": "{photo}", "FAVORITE": "false"},
            seeds=[{"kind": "png", "path": folder, "as_dir": True, "name_file": photo_path("photos-import")}],
            opens=[{"name": "Photos"}, {"name": "Finder", "file": folder}],
            timeout=150,
        ),
        app_task(
            "photos-favorite", "Photos", "导入并标为喜欢",
            face("照片已经打开。请把 %s 里的那张 PNG 导入图库，并把它标为喜欢。" % seed("photos-favorite"), cloud=True),
            "导入的那张图文件名匹配，且喜欢为真。",
            [{"field": "KIND", "eq": "item"}, {"field": "FILENAME", "eq": "{photo}"}, {"field": "FAVORITE", "eq": "true"}],
            {"KIND": "item", "NAME": "{photo}", "FILENAME": "{photo}", "FAVORITE": "true"},
            seeds=[{"kind": "png", "path": seed("photos-favorite"), "as_dir": True, "name_file": photo_path("photos-favorite")}],
            opens=[{"name": "Photos"}, {"name": "Finder", "file": seed("photos-favorite")}],
            timeout=150,
        ),
    ]
    return rows


def shortcut_specs():
    rows = [
        app_task(
            "sc-name", "Shortcuts", "新建一个快捷指令",
            face("快捷指令已经打开。请新建一个快捷指令，名字是 %s 第一行的标记，里面至少放 1 个动作（例如「文本」或「显示结果」）。不要登录。" % mark("sc-name"), cloud=True),
            "快捷指令列表里有这个名字，动作数至少 1。",
            [{"field": "KIND", "eq": "shortcut"}, {"field": "NAME", "eq": "{marker}"}, {"field": "ACTIONS", "gte": 1}],
            {"KIND": "shortcut", "NAME": "{marker}", "FOLDER": "", "ACTIONS": "1", "ACCEPTS": "false"},
            bypass=SHORTCUT_BYPASS, timeout=120,
        ),
        app_task(
            "sc-two", "Shortcuts", "快捷指令里放两个动作",
            face("快捷指令已经打开。请新建一个快捷指令，名字是 %s 第一行的标记，里面按顺序放至少两个动作，例如先「文本」再「显示结果」。" % mark("sc-two"), cloud=True),
            "名字等于标记，动作数至少 2。评分看动作个数，不读动作里的字。",
            [{"field": "KIND", "eq": "shortcut"}, {"field": "NAME", "eq": "{marker}"}, {"field": "ACTIONS", "gte": 2}],
            {"KIND": "shortcut", "NAME": "{marker}", "FOLDER": "", "ACTIONS": "2", "ACCEPTS": "false"},
            bypass=SHORTCUT_BYPASS,
        ),
        app_task(
            "sc-folder", "Shortcuts", "新建文件夹并放进一条快捷指令",
            face("快捷指令已经打开。请新建一个文件夹，名字是 %s 第一行的标记，并在里面放一个至少有 1 个动作的快捷指令。" % mark("sc-folder"), cloud=True),
            "有一条快捷指令的所在文件夹等于标记，且动作数至少 1。",
            [{"field": "KIND", "eq": "shortcut"}, {"field": "FOLDER", "eq": "{marker}"}, {"field": "ACTIONS", "gte": 1}],
            {"KIND": "shortcut", "NAME": "inside", "FOLDER": "{marker}", "ACTIONS": "1", "ACCEPTS": "false"},
            bypass=SHORTCUT_BYPASS,
        ),
        app_task(
            "sc-input", "Shortcuts", "让快捷指令接收输入",
            face("快捷指令已经打开。请新建一个快捷指令，名字是 %s 第一行的标记，至少 1 个动作，并在设置里打开「接收输入」。" % mark("sc-input"), cloud=True),
            "名字等于标记，接收输入为真，动作数至少 1。",
            [{"field": "KIND", "eq": "shortcut"}, {"field": "NAME", "eq": "{marker}"}, {"field": "ACCEPTS", "eq": "true"}, {"field": "ACTIONS", "gte": 1}],
            {"KIND": "shortcut", "NAME": "{marker}", "FOLDER": "", "ACTIONS": "1", "ACCEPTS": "true"},
            bypass=SHORTCUT_BYPASS,
        ),
    ]
    return rows


def multi(task_id, apps, feature, instruction, note, bypass, parts, opens, seeds, clear, outputs, timeout=150):
    return base(
        task_id, apps, feature, instruction, "multi", note, bypass, {},
        opens, seeds=seeds, clear=clear, outputs=outputs, timeout=timeout, checks=parts,
    )


def deep_specs():
    brief = seed("deep-agenda.txt")
    rtf = out("deep-agenda.rtf")
    agenda_part = rtf_task(
        "deep-agenda-rtf", "议程富文本", "part",
        rtf, "富文本含 KEEP-BRIEF、15:00 和标记，原稿不被改写。",
        contains=["KEEP-BRIEF", "15:00", "{marker}"],
        keep={"path": brief, "contains": "KEEP-BRIEF", "file": "KEEP-BRIEF\n15:00\n"},
        good_text="KEEP-BRIEF\n15:00\n{marker}",
        opens=[{"name": "TextEdit", "file": brief}],
    )
    agenda_part["params"]["marker_file"] = mark("deep-agenda")
    cal_part = app_task(
        "deep-agenda-cal", "Calendar", "日程", "part",
        "日历里有标记为标题的 15:00 到 16:00 日程。",
        [
            {"field": "SUMMARY", "eq": "{marker}"},
            {"field": "START", "prefix": "{today}T15:00"},
            {"field": "END", "prefix": "{today}T16:00"},
            {"field": "ALLDAY", "eq": "false"},
        ],
        {"KIND": "event", "SUMMARY": "{marker}", "LOCATION": "", "DESCRIPTION": "", "START": "{today}T15:00", "END": "{today}T16:00", "ALLDAY": "false", "ALARM": ""},
    )
    cal_part["params"]["marker_file"] = mark("deep-agenda")
    note_part = app_task(
        "deep-note", "Notes", "备忘", "part",
        "备忘纯文本含种子句和标记。",
        [{"field": "PLAIN", "has": "KEEP-BRIEF"}, {"field": "PLAIN", "has": "{marker}"}],
        {"KIND": "note", "NAME": "KEEP-BRIEF", "PLAIN": "KEEP-BRIEF {marker}", "FOLDER": "备忘录", "BODY": "", "ATTACH": ""},
    )
    note_part["params"]["marker_file"] = mark("deep-note-rem")
    rem_part = app_task(
        "deep-rem", "Reminders", "提醒", "part",
        "提醒标题是标记，备注含 KEEP-BRIEF。",
        [{"field": "NAME", "eq": "{marker}"}, {"field": "BODY", "has": "KEEP-BRIEF"}],
        {"KIND": "reminder", "NAME": "{marker}", "BODY": "KEEP-BRIEF", "LIST": "提醒事项", "COMPLETED": "false", "FLAGGED": "false", "PRIORITY": "0", "DUE": ""},
    )
    rem_part["params"]["marker_file"] = mark("deep-note-rem")
    src = seed("deep-preview-alias.pdf")
    dest = out("deep-preview-alias.pdf")
    alias = out("deep-preview-alias-link")
    pdf_part = pdf_task("deep-preview-alias-pdf", "批注", "part", "freetext", "副本上有标记的自由文本批注。")
    pdf_part["id"] = "deep-preview-alias-pdf"
    pdf_part["params"]["path"] = dest
    pdf_part["params"]["marker_file"] = mark("deep-preview-alias")
    pdf_part["params"]["seed_token_file"] = token_path("deep-preview-alias")
    pdf_part["params"]["keep_path"] = src
    alias_part = base(
        "deep-preview-alias-link", "Finder", "替身", "part", "alias",
        "替身指向另存的 PDF。", ALIAS_BYPASS,
        {"kind": "finder_alias", "path": alias, "target_name": "deep-preview-alias.pdf", "marker_file": mark("deep-preview-alias"), "grade_note": "替身指向另存的 PDF。"},
        [], target_name="deep-preview-alias.pdf",
    )
    album_part = app_task(
        "deep-photos-album", "Photos", "相簿", "part",
        "相簿名字等于标记。",
        [{"field": "KIND", "eq": "album"}, {"field": "NAME", "eq": "{marker}"}],
        {"KIND": "album", "NAME": "{marker}"},
    )
    album_part["params"]["marker_file"] = mark("deep-photos-note")
    note2 = app_task(
        "deep-photos-note-body", "Notes", "备忘", "part",
        "备忘里有标记和 ALBUM。",
        [{"field": "PLAIN", "has": "{marker}"}, {"field": "PLAIN", "has": "ALBUM"}],
        {"KIND": "note", "NAME": "ALBUM", "PLAIN": "ALBUM {marker}", "FOLDER": "备忘录", "BODY": "", "ATTACH": ""},
    )
    note2["params"]["marker_file"] = mark("deep-photos-note")
    rows = [
        multi(
            "deep-agenda", ["TextEdit", "Calendar"], "把简报写成议程并排进日历",
            face("今天的日期在 %s。简报 %s 里有 KEEP-BRIEF 和 15:00。请用文本编辑把简报整理成富文本，存到 %s：保留 KEEP-BRIEF 和 15:00，并写上 %s 第一行的标记。不要改简报原稿。再在日历里新建日程，标题用同一个标记，今天 15:00 到 16:00，不要做成全天。不要登录。" % (today_path(), brief, rtf, mark("deep-agenda")), cloud=True),
            "富文本和日历日程都要出现同一个标记；简报原稿保持原样。",
            FILE_BYPASS + " 日历部分：" + APP_BYPASS,
            [agenda_part, cal_part],
            [{"name": "TextEdit", "file": brief}, {"name": "Calendar"}],
            [{"kind": "text", "path": brief, "text": "KEEP-BRIEF\n15:00\n"}],
            [rtf],
            [{"name": "deep-agenda-rtf", "path": rtf}],
        ),
        multi(
            "deep-note-rem", ["Notes", "Reminders"], "同一标记写进备忘和提醒",
            face("请读 %s。在备忘录里新建一条备忘，正文包含 KEEP-BRIEF 和 %s 第一行的标记。在提醒事项里新建一条提醒，标题用同一个标记，备注里写上 KEEP-BRIEF。不要登录。" % (seed("deep-note-rem.txt"), mark("deep-note-rem")), cloud=True),
            "备忘和提醒都要带上同一个标记，提醒备注里还有种子句。",
            APP_BYPASS,
            [note_part, rem_part],
            [{"name": "Notes"}, {"name": "Reminders"}, {"name": "TextEdit", "file": seed("deep-note-rem.txt")}],
            [{"kind": "text", "path": seed("deep-note-rem.txt"), "text": "KEEP-BRIEF\n"}],
            [], [],
        ),
        multi(
            "deep-preview-alias", ["Preview", "Finder"], "批注 PDF 再做替身",
            face("预览会打开 %s。请加一条自由文本批注，内容是 %s 第一行的标记，另存到 %s。不要删页面上的 SEED- 那行，也不要改原稿。然后在访达里给这份另存的 PDF 做替身，存到 %s。" % (src, mark("deep-preview-alias"), dest, alias)),
            "PDF 副本带标记批注，替身指向这个副本的文件名。符号链接得 0。",
            PDF_BYPASS + " " + ALIAS_BYPASS,
            [pdf_part, alias_part],
            [{"name": "Preview", "file": src}, {"name": "Finder", "file": HOME + "/out"}],
            [{"kind": "pdf", "path": src, "token_file": token_path("deep-preview-alias")}],
            [dest, alias],
            [{"name": "deep-preview-alias-pdf", "path": dest}, {"name": "deep-preview-alias-link", "path": alias}],
        ),
        multi(
            "deep-photos-note", ["Photos", "Notes"], "建相簿并在备忘里记下名字",
            face("请在照片里新建相簿，名字是 %s 第一行的标记。再在备忘录里新建一条备忘，正文同时包含 ALBUM 和同一个标记。不要登录。" % mark("deep-photos-note"), cloud=True),
            "相簿名等于标记，备忘纯文本里有 ALBUM 和标记。",
            APP_BYPASS + " 照片第一次打开若停在欢迎页，这题会得 0。",
            [album_part, note2],
            [{"name": "Photos"}, {"name": "Notes"}],
            [], [], [], timeout=150,
        ),
    ]
    return rows


def all_specs():
    return (
        textedit_specs()
        + preview_specs()
        + notes_specs()
        + reminder_specs()
        + calendar_specs()[:2]
        + calendar_specs()[2:]
        + finder_specs()
        + photos_specs()
        + shortcut_specs()
        + deep_specs()
    )


SPECS = all_specs()


def params_of(spec):
    if spec["fixture"] == "multi":
        return {"kind": "all", "checks": [params_of(part) for part in spec["checks"]], "grade_note": spec["grade_note"]}
    return spec["params"]


SETUP_TEXT = r'''import datetime, os, subprocess, sys, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup
import nologin_seed as seed

MARKER_PATH = __MARKER__
TODAY_PATH = __TODAY__
CLEAR = __CLEAR__
OPENS = __OPENS__
SEEDS = __SEEDS__


class Setup(BaseSetup):
    def run(self, context):
        today = datetime.date.today().isoformat()
        seed.write_text(TODAY_PATH, today + "\n")
        marker = seed.alphabet_token("E31-")
        seed.write_text(MARKER_PATH, marker + "\n")
        for rel in CLEAR:
            path = os.path.expanduser(rel)
            if os.path.lexists(path) and not os.path.isdir(path):
                os.remove(path)
        seed.apply(SEEDS, marker, today)
        opened = []
        errors = []
        for item in OPENS:
            cmd = ["open", "-a", item["name"]]
            if item.get("file"):
                cmd.append(os.path.expanduser(item["file"]))
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                errors.append({"name": item["name"], "code": proc.returncode, "stderr": (proc.stderr or "")[:400]})
            else:
                opened.append(item["name"])
        if len(opened) != len(OPENS):
            sys.stderr.write("open failed\n")
            return {"status": "failed", "state": {"errors": errors, "opened": opened}}
        time.sleep(2)
        return {"status": "completed", "state": {"opened": opened, "marker_path": MARKER_PATH}}
'''


EVAL_TEXT = r'''import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads(__PARAMS__)


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
'''


def render_setup(spec):
    text = SETUP_TEXT
    text = text.replace("__MARKER__", repr(mark(spec["id"])))
    text = text.replace("__TODAY__", repr(today_path()))
    text = text.replace("__CLEAR__", repr(spec["clear"]))
    text = text.replace("__OPENS__", repr(spec["opens"]))
    text = text.replace("__SEEDS__", repr(spec["seeds"]))
    return text


def render_eval(spec):
    payload = json.dumps(params_of(spec), ensure_ascii=False, separators=(",", ":"))
    return EVAL_TEXT.replace("__PARAMS__", repr(payload))


def task_json(spec):
    apps = []
    for name in spec["apps"]:
        display, bundles = APPS[name]
        apps.append({"name": display, "bundle_ids": bundles})
    data = {
        "protocol": "task-package-v4",
        "id": spec["id"],
        "category": "e31-nologin",
        "instruction": spec["instruction"],
        "setup": {
            "timeout_seconds": 180,
            "files": [{"source": "shared/nologin_seed.py", "destination": "nologin_seed.py"}],
        },
        "evaluation": {
            "timeout_seconds": spec["timeout"],
            "files": [{"source": "shared/nologin_grade.py", "destination": "nologin_grade.py"}],
        },
        "requirements": {"apps": apps},
        "metadata": {
            "batch": BATCH,
            "app": " + ".join(spec["apps"]),
            "feature": spec["feature"],
            "gradeable": True,
            "needs_login": False,
            "bypass": spec["bypass"],
            "grade_note": spec["grade_note"],
        },
    }
    if spec["outputs"]:
        data["outputs"] = [
            {"name": item["name"], "path": item["path"], "capture": "best_effort"}
            for item in spec["outputs"]
        ]
    return data


def smoke_for(specs):
    want = [
        "te-rtf-marker", "pv-freetext", "notes-title", "rem-name", "cal-timed",
        "find-alias", "photos-album", "sc-name", "deep-agenda",
    ]
    have = {item["id"] for item in specs}
    return [item for item in want if item in have]


def build(limit=None):
    specs = SPECS if limit is None else SPECS[:limit]
    tasks_root = ROOT / "tasks"
    if tasks_root.exists():
        for child in tasks_root.iterdir():
            if child.is_dir():
                for item in child.iterdir():
                    item.unlink()
                child.rmdir()
    rels = []
    for spec in specs:
        folder = tasks_root / spec["id"]
        folder.mkdir(parents=True)
        (folder / "task.json").write_text(json.dumps(task_json(spec), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (folder / "initial_setup.py").write_text(render_setup(spec), encoding="utf-8")
        (folder / "evaluation.py").write_text(render_eval(spec), encoding="utf-8")
        rels.append("tasks/%s/task.json" % spec["id"])
    suite = {
        "schema_version": 1,
        "tasks": rels,
        "smoke": smoke_for(specs),
        "metadata": {
            "batch": BATCH,
            "needs_login": False,
            "task_count": len(specs),
            "image": "仓库里没有 digest 705c043 的逐应用清单。11-05 那份 inventory 是另一次运行。这包只用 Mac 系统自带应用。",
            "note": "每题 selftest 都有空跑 0 分和终端捷径 0 分。没有提交集群，没有改生产机。",
        },
    }
    (ROOT / "suite.json").write_text(json.dumps(suite, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return specs


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    written = build(limit)
    print(len(written), "tasks")
