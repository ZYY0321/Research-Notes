"""Render and copy traceable report assets from immutable run evidence."""

from pathlib import Path
import html
import json
import shutil
from PIL import Image, ImageDraw
from truncator.source.binding import active_records, select_record
from truncator.imaging.geometry import rectangle
from truncator.mutation.mutations import mutation_patches
from truncator.common.storage import read, digest
from truncator.common.capture_files import capture_image, evidence_files


def escaped(value):
    return html.escape(str(value))


def document(title, body):
    return (
        '<!doctype html><html lang="zh"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width"><title>'
        + escaped(title)
        + "</title>"
        "<style>body{font:16px/1.65 system-ui,sans-serif;max-width:1400px;margin:30px auto;padding:0 20px;"
        "color:#172431;background:#f4f6f8}a{color:#1261a0}article,section{background:white;padding:20px;"
        "margin:20px 0;border:1px solid #dce1e6;border-radius:8px}pre{white-space:pre-wrap;"
        "overflow-wrap:anywhere;background:#eef2f5;padding:12px;font:13px/1.6 monospace}"
        ".pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}.pair img{max-width:100%}"
        ".line{display:block;white-space:pre}.line:target{background:#fff3ab}"
        ".num{display:inline-block;color:#74808a;width:4em;user-select:none}table{border-collapse:collapse;"
        "width:100%}td,th{border:1px solid #ddd;padding:8px;text-align:left}"
        "@media(max-width:700px){.pair{grid-template-columns:1fr}}</style><h1>"
        + escaped(title)
        + "</h1>"
        + body
        + "</html>"
    )


def json_block(value):
    return "<pre>" + escaped(json.dumps(value, ensure_ascii=False, indent=2)) + "</pre>"


def source_html(path, content):
    body = (
        "<pre>"
        + "".join(
            '<span class="line" id="L'
            + str(i)
            + '"><span class="num">'
            + str(i)
            + "</span>"
            + escaped(line)
            + "</span>"
            for i, line in enumerate(content.splitlines(), 1)
        )
        + "</pre>"
    )
    path.write_text(document(path.name, body), encoding="utf-8")


def copy_capture(source, destination):
    destination.mkdir(parents=True, exist_ok=True)
    if source is None:
        return
    for name in (
        *evidence_files(source),
        "geometry-observation.json",
        "diagnostics.json",
        "image-quality.json",
        "display.json",
        "replay.json",
        "page-wait.json",
        "initial-state.json",
        "startup-waits.json",
        "layout-impact.json",
    ):
        if (source / name).exists():
            shutil.copy2(source / name, destination / name)
    for path in sorted(source.glob("action-*.json")):
        shutil.copy2(path, destination / path.name)
    logs = destination / "logs"
    logs.mkdir(exist_ok=True)
    for path in sorted(source.glob("*.log")):
        shutil.copy2(path, logs / path.name)
    index = (
        "<ul>"
        + "".join(
            '<li><a href="' + p.name + '">' + p.name + "</a></li>"
            for p in sorted(logs.glob("*.log"))
        )
        + "</ul>"
    )
    (logs / "index.html").write_text(document("采集命令日志", index), encoding="utf-8")


def som(folder, marked):
    screenshot = capture_image(folder)
    if not screenshot.exists():
        return
    with Image.open(screenshot) as source:
        image = source.convert("RGB")
    draw = ImageDraw.Draw(image)
    width = max(2, round(image.width / 550))
    for number, bounds in marked:
        x0, y0, x1, y1 = bounds
        draw.rectangle((x0, y0, x1, y1), outline="#e53b36", width=width)
        label = str(number)
        side = max(26, width * 10)
        left = max(0, min(image.width - side, x0))
        top = max(0, min(image.height - side, y0 - side))
        draw.rectangle((left, top, left + side, top + side), fill="#e53b36")
        draw.text(
            (left + side / 2, top + side / 2),
            label,
            fill="white",
            anchor="mm",
            font_size=side * 0.65,
        )
    image.save(folder / "som.png")


def locate(folder, selector):
    if folder is None:
        return {"status": "capture_missing"}
    try:
        record = select_record(
            active_records(read(folder / "tree-before.json")), selector
        )
        attrs = record["attributes"]
        return {
            "status": "located",
            "bounds": rectangle(attrs["bounds"]),
            "origBounds": attrs.get("origBounds"),
            "text": attrs.get("text"),
            "id": attrs.get("id"),
        }
    except (ValueError, OSError, KeyError) as error:
        return {"status": "target_unresolved", "reason": str(error)}


def component_preview(source, location, output):
    if source is None or location["status"] != "located":
        return False
    with Image.open(capture_image(source)) as image:
        left, top, right, bottom = location["bounds"]
        box = (
            max(0, left - 8),
            max(0, top - 8),
            min(image.width, right + 8),
            min(image.height, bottom + 8),
        )
        if box[2] <= box[0] or box[3] <= box[1]:
            return False
        output.parent.mkdir(parents=True, exist_ok=True)
        image.crop(box).save(output)
    return True


def source_changes(plan, member, run, folder):
    changes = []
    all_edits = plan.get("patches") or mutation_patches(plan)
    for edit in mutation_patches(member):
        relative = edit["file"]
        before = (Path(plan["source_root"]) / relative).read_bytes().decode("utf-8")
        after = (run / "project" / relative).read_bytes().decode("utf-8")
        if digest(before) != plan["file_hashes"][relative]:
            raise ValueError("Original source changed since planning: " + relative)
        post_scan = read(run / "post-scan.json")
        if digest(after) != post_scan["files"][relative]:
            raise ValueError("Modified source changed since preparation: " + relative)
        token = digest(relative)[:12]
        target = folder / "sources" / token
        target.mkdir(parents=True, exist_ok=True)
        (target / "before.ets").write_bytes(before.encode("utf-8"))
        (target / "after.ets").write_bytes(after.encode("utf-8"))
        source_html(target / "before.html", before)
        source_html(target / "after.html", after)
        shift = sum(
            len(e["after"]) - len(e["before"])
            for e in all_edits
            if e["file"] == relative and e["start"] < edit["start"]
        )
        before_line = before[: edit["start"]].count("\n") + 1
        after_line = after[: edit["start"] + shift].count("\n") + 1
        changes.append(
            {
                "file": relative,
                "before_line": before_line,
                "after_line": after_line,
                "before": edit["before"],
                "after": edit["after"],
                "before_link": "sources/" + token + "/before.html#L" + str(before_line),
                "after_link": "sources/" + token + "/after.html#L" + str(after_line),
            }
        )
    return changes
