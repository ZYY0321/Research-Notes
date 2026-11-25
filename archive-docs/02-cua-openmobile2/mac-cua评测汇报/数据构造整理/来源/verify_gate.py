#!/usr/bin/env python3
"""Local gate for an E31 task pack.

    python3 verify_gate.py <题包目录>
    python3 verify_gate.py <题包目录> --out 报告.md

Grades existing selftest fakes and on-disk real exports with
maccua-tasks/_shared_tightened_1124_b, which honors PARAMS["allowed"].
Compares formats, paths, and numbers in the instruction with PARAMS.
Does not open apps, call osascript, contact production or the cluster,
or modify the pack or the grader libraries.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import traceback
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

EXP = Path("/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据")
TIGHT = Path("/Users/zhangyingying/CUA/评测集建设/maccua-tasks/_shared_tightened_1124_b")
GOLDEN_ROOTS = [
    EXP / "raw/figma导出图_1124",
    EXP / "raw/假阴性回归_1124/prod",
    EXP / "raw/假阴性回归_1124/seed",
    EXP / "raw/psd真文件_1124",
]
PATH_KEYS = {"path", "baseline_path", "skip_path", "contains_file", "draft_baseline_path", "flag_seal_path"}
SIDE_DICTS = {"keep", "differ_from"}
CONTENT_KEYS = {
    "width", "height", "min_width", "min_height", "samples", "not_flat",
    "differ_from", "contains", "exact", "subject", "body_contains",
    "to_contains", "attachment_contains", "layer_count_in", "keep", "allowed",
}
PROVENANCE_KEYS = {"draft_baseline_path", "flag_seal_path", "baseline_path"}
PREAMBLE = (
    "能用终端就先用终端。请在题面里的那个应用里把事情做完，成品由这个应用自己交出来。"
    "不要用 AppleScript 去驱动应用，也不要结束、杀掉或重启它的进程，更不要用别的程序生成成品文件。"
    "终端做不成就改用界面。做完后用一两句说明用了什么方法，以及有没有做题面没要求的改动。"
)
EXTRA_BOILER = "这道题的成品必须由 Photoshop 自己存出来，不要用别的程序生成同名文件来代替。"
FILE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".psd", ".pdf", ".svg", ".gif", ".txt"}
FORMATS = {
    "PNG": {"exts": {".png"}, "kinds": {"png", "png_rgba"}, "words": ("PNG",)},
    "JPEG": {"exts": {".jpg", ".jpeg"}, "kinds": {"jpeg"}, "words": ("JPEG", "JPG")},
    "TIFF": {"exts": {".tif", ".tiff"}, "kinds": set(), "words": ("TIFF", "TIF"), "prefix": ("II", "MM")},
    "PSD": {"exts": {".psd"}, "kinds": {"psd"}, "words": ("PSD",), "prefix": ("8BPS",)},
    "PDF": {"exts": {".pdf"}, "kinds": set(), "words": ("PDF",), "prefix": ("%PDF",)},
    "SVG": {"exts": {".svg"}, "kinds": set(), "words": ("SVG",), "prefix": ("<svg", "<?xml")},
    "TXT": {"exts": {".txt"}, "kinds": {"text"}, "words": ()},
}
STUB_SRC = '''class BaseSetup:
    def run(self, context=None, **kwargs):
        return {"status": "completed", "state": {}}


class BaseEvaluation:
    def run(self, context=None, **kwargs):
        return {"status": "not_evaluated", "score": None}
'''


def sha12(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def load_params(text: str):
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PARAMS":
                    return ast.literal_eval(node.value)
    raise ValueError("no PARAMS")


def leaves(params):
    if not isinstance(params, dict):
        return []
    if params.get("kind") == "all":
        found = []
        for check in params.get("checks") or []:
            found.extend(leaves(check))
        return found
    return [params]


def task_body(instruction: str) -> str:
    body = instruction or ""
    if body.startswith(PREAMBLE):
        body = body[len(PREAMBLE):].lstrip()
    if body.startswith(EXTRA_BOILER):
        body = body[len(EXTRA_BOILER):].lstrip()
    return body


def clean_token(value: str) -> str:
    return value.strip().rstrip(").,，。；、：:）]」")


def basename_of(value: str) -> str:
    return Path(os.path.expanduser(clean_token(value).rstrip("/"))).name


def display_path(value: str) -> str:
    text = clean_token(value).rstrip("/")
    path = Path(os.path.expanduser(text))
    parent = path.parent.name
    if parent and parent not in (".", "/", "~"):
        return parent + "/" + path.name
    return path.name or text


def iter_paths(params):
    """Yield (role, original path). role is product for a check's own path, else side."""
    found = []

    def walk(obj, side):
        if isinstance(obj, dict):
            for key, val in obj.items():
                next_side = side or key in SIDE_DICTS
                if key in PATH_KEYS and isinstance(val, str):
                    role = "side" if next_side or key != "path" else "product"
                    found.append((role, val))
                else:
                    walk(val, next_side)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, side)

    walk(params, False)
    return found


def apply_mapping(params, mapping):
    def walk(obj):
        if isinstance(obj, dict):
            out = {}
            for key, val in obj.items():
                if key in PATH_KEYS and isinstance(val, str) and val in mapping:
                    out[key] = mapping[val]
                else:
                    out[key] = walk(val)
            return out
        if isinstance(obj, list):
            return [walk(item) for item in obj]
        return obj

    return walk(copy.deepcopy(params))


def present(value):
    return value not in (None, "", [], {})


def assign_level(params):
    if not isinstance(params, dict) or params.get("kind") == "manual":
        return "L0", "手工题。评分固定返回 0。这一级不说明模型做没做成。"
    found = []
    provenance = []
    for leaf in leaves(params):
        for key in CONTENT_KEYS:
            if present(leaf.get(key)):
                found.append(key)
        for key in PROVENANCE_KEYS:
            if present(leaf.get(key)):
                provenance.append(key)
    if provenance:
        extra = "题里写了 " + "、".join(sorted(set(provenance))) + "。这次仍标到这里为止：没有用旧文件和新文件各打一遍，也没有人工金标准。"
    else:
        extra = "没有核「是不是这次新做的」，也没有人工金标准。脚本不标 L3、L4。"
    if not found:
        return "L1", "只有文件能不能解析这一层（魔数、后缀或署名），PARAMS 里没有尺寸、抽样、正文或图层条件。" + extra
    names = "、".join(sorted(set(found)))
    return "L2", "PARAMS 里有书面条件（" + names + "）。" + extra


def index_golden():
    files = []
    missing_roots = []
    for root in GOLDEN_ROOTS:
        if not root.is_dir():
            missing_roots.append(str(root))
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in FILE_SUFFIXES:
                continue
            if path.name.startswith("结束截图"):
                continue
            files.append(path)
    return files, missing_roots


def locate(task_id, original, role, files):
    base = basename_of(original)
    exact = [path for path in files if path.name == base]
    tagged = []
    for path in files:
        name = path.name
        in_task = ("/tasks/%s/" % task_id) in str(path)
        marked = ("__%s__" % task_id) in name and name.endswith(base)
        if path in exact and in_task:
            tagged.append(path)
        elif marked and path not in tagged:
            tagged.append(path)
    if tagged:
        chosen = tagged
    elif len(exact) == 1:
        chosen = exact
    elif len(exact) > 1:
        return "ambiguous", exact
    else:
        return "missing", []
    if role == "product":
        produced = [path for path in chosen if "/seed/" not in str(path)]
        if produced:
            chosen = produced
    return "ok", chosen


def flatten_problems(details):
    if not isinstance(details, dict):
        return []
    found = []
    for item in details.get("problems") or []:
        found.append(str(item))
    reason = details.get("reason")
    if reason and reason not in ("ok",):
        found.append(str(reason))
    for part in details.get("parts") or []:
        if isinstance(part, dict):
            found.extend(flatten_problems(part))
    unique = []
    for item in found:
        if item not in unique:
            unique.append(item)
    return unique


def seal(module, patch_clock=False):
    """Stop osascript. Clock patching stays inside the selftest process."""
    calls = {"n": 0}
    start = module.time.time()
    ticks = {"n": 0}
    real_run = module.subprocess.run

    def blocked(*_args, **_kwargs):
        calls["n"] += 1
        return None, "verify_gate_blocked"

    def guarded(args, *args_, **kwargs):
        flat = list(args) if isinstance(args, (list, tuple)) else [args]
        if any("osascript" in str(part) for part in flat):
            calls["n"] += 1
            raise RuntimeError("osascript blocked by verify_gate")
        return real_run(args, *args_, **kwargs)

    def fast_time():
        ticks["n"] += 1
        return start + ticks["n"] * 1000

    module.run_osascript = blocked
    module.subprocess.run = guarded
    if patch_clock:
        module.time.sleep = lambda *_a, **_k: None
        module.time.time = fast_time
    return calls


def grade_mapped(grade, params, mapping):
    got = grade(apply_mapping(params, mapping))
    details = got.get("details") or {}
    return {
        "score": got.get("score"),
        "reason": details.get("reason"),
        "problems": flatten_problems(details),
    }


def true_export_gate(task_id, params, grade, files):
    refs = iter_paths(params)
    products = [(role, original) for role, original in refs if role == "product"]
    sides = [(role, original) for role, original in refs if role == "side"]
    if not products:
        return {"status": "未覆盖", "reason": "PARAMS 里没有成品路径", "files": []}
    located = []
    for role, original in products + sides:
        state, paths = locate(task_id, original, role, files)
        located.append({"role": role, "original": original, "state": state, "paths": paths})
    missing = [item for item in located if item["state"] == "missing"]
    ambiguous = [item for item in located if item["state"] == "ambiguous"]
    if missing or ambiguous:
        bits = []
        seen_missing = set()
        for item in missing:
            label = "成品" if item["role"] == "product" else "配套"
            shown = display_path(item["original"])
            key = (label, shown)
            if key in seen_missing:
                continue
            seen_missing.add(key)
            bits.append("%s %s 不在本机这几个目录里" % (label, shown))
        for item in ambiguous:
            names = "、".join(str(path) for path in item["paths"][:3])
            bits.append("%s 有多份同名文件，对不上这一道：%s" % (basename_of(item["original"]), names))
        return {"status": "未覆盖", "reason": "；".join(bits), "files": []}
    product_items = [item for item in located if item["role"] == "product"]
    side_items = [item for item in located if item["role"] == "side"]
    count = max(len(item["paths"]) for item in product_items)
    rows = []
    for index in range(count):
        mapping = {}
        used = []
        for item in side_items:
            mapping[item["original"]] = str(item["paths"][0])
            used.append(item["paths"][0])
        for item in product_items:
            path = item["paths"][min(index, len(item["paths"]) - 1)]
            mapping[item["original"]] = str(path)
            used.append(path)
        try:
            graded = grade_mapped(grade, params, mapping)
        except Exception as exc:
            graded = {"score": None, "reason": type(exc).__name__, "problems": [str(exc)]}
        graded["files"] = [str(path) for path in used]
        graded["products"] = [
            str(item["paths"][min(index, len(item["paths"]) - 1)]) for item in product_items
        ]
        rows.append(graded)
    bad = [row for row in rows if row["score"] != 1]
    if bad:
        parts = []
        for row in bad:
            names = "、".join(Path(path).name for path in row["products"])
            problems = "、".join(row["problems"]) if row["problems"] else row["reason"]
            parts.append("成品 %s 分数 %s（%s）" % (names, row["score"], problems))
        return {"status": "失败", "reason": "；".join(parts), "files": rows}
    names = []
    for row in rows:
        for path in row["products"]:
            base = Path(path).name
            if base not in names:
                names.append(base)
    return {"status": "通过", "reason": "重打 %d 份，都是 1：%s" % (len(rows), "、".join(names)), "files": rows}


def instruction_paths(body: str):
    found = []
    stop = r"[^\s，。；、：:\"'“”<>|*?\n（()【】\[\]「」]"
    for match in re.finditer(r"~/" + stop + "+", body):
        found.append(clean_token(match.group(0)))
    stripped = body
    for path in found:
        stripped = stripped.replace(path, " ")
    for match in re.finditer(
        r"(?<![A-Za-z0-9_./~-])([A-Za-z0-9_.-]+\.(?:png|jpe?g|tiff?|psd|pdf|svg|gif|txt))\b",
        stripped,
        re.I,
    ):
        found.append(clean_token(match.group(1)))
    unique = []
    seen = set()
    for item in found:
        base = basename_of(item)
        if base and base not in seen:
            seen.add(base)
            unique.append(item)
    return unique


def mentioned_formats(body: str, paths):
    found = []
    for name, spec in FORMATS.items():
        hit = False
        for path in paths:
            if Path(basename_of(path)).suffix.lower() in spec["exts"]:
                hit = True
        for word in spec["words"]:
            if re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % word, body):
                hit = True
        if hit:
            found.append(name)
    return found


def format_covered(name, params):
    spec = FORMATS[name]
    for _role, original in iter_paths(params):
        if Path(basename_of(original)).suffix.lower() in spec["exts"]:
            return True
    for leaf in leaves(params):
        if leaf.get("kind") in spec["kinds"]:
            return True
        prefix = str(leaf.get("prefix") or "")
        for head in spec.get("prefix") or ():
            if prefix.startswith(head):
                return True
    return False


def dimension_pairs(obj, acc):
    if isinstance(obj, dict):
        if "width" in obj and "height" in obj:
            try:
                acc.add((int(obj["width"]), int(obj["height"])))
            except (TypeError, ValueError):
                pass
        for val in obj.values():
            dimension_pairs(val, acc)
    elif isinstance(obj, list):
        for item in obj:
            dimension_pairs(item, acc)


def collect_rgb(obj, acc):
    if isinstance(obj, dict):
        for key in ("rgb", "flat_rgb"):
            val = obj.get(key)
            if isinstance(val, (list, tuple)) and len(val) == 3:
                try:
                    acc.add(tuple(int(part) for part in val))
                except (TypeError, ValueError):
                    pass
        for val in obj.values():
            collect_rgb(val, acc)
    elif isinstance(obj, list):
        for item in obj:
            collect_rgb(item, acc)


def collect_ints(obj, acc):
    if isinstance(obj, bool):
        return
    if isinstance(obj, int):
        acc.add(obj)
        return
    if isinstance(obj, dict):
        for val in obj.values():
            collect_ints(val, acc)
    elif isinstance(obj, list):
        for item in obj:
            collect_ints(item, acc)


def consistency_gate(body, params):
    if not body.strip():
        return {"status": "未覆盖", "reason": "task.json 没有题面正文", "gaps": []}
    gaps = []
    paths = instruction_paths(body)
    param_bases = {basename_of(original) for _role, original in iter_paths(params)}
    for path in paths:
        base = basename_of(path)
        if base not in param_bases:
            gaps.append("路径 %s 在题面里，PARAMS 的路径字段里没有" % display_path(path))
    for name in mentioned_formats(body, paths):
        if not format_covered(name, params):
            gaps.append("格式 %s 在题面里，PARAMS 没有对应的 kind、后缀或文件头" % name)
    pairs = set()
    dimension_pairs(params, pairs)
    body_dims = []
    dim_numbers = set()
    for match in re.finditer(r"(\d{1,5})\s*[×xX]\s*(\d{1,5})", body):
        pair = (int(match.group(1)), int(match.group(2)))
        body_dims.append(pair)
        dim_numbers.update(pair)
    seen_pairs = set()
    for pair in body_dims:
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        if pair not in pairs:
            gaps.append("尺寸 %d×%d 在题面里，PARAMS 的 width/height 里没有这一对" % pair)
    colors = set()
    collect_rgb(params, colors)
    seen_rgb = set()
    rgb_re = re.compile(
        r"(?:[（(]\s*|(?:RGB|rgb|颜色)\s*[:：]?\s*)(\d{1,3})\s*[,，]\s*(\d{1,3})\s*[,，]\s*(\d{1,3})"
    )
    for match in rgb_re.finditer(body):
        rgb = tuple(int(part) for part in match.groups())
        if rgb in seen_rgb or any(part > 255 for part in rgb):
            continue
        seen_rgb.add(rgb)
        if rgb not in colors:
            gaps.append("颜色 (%d, %d, %d) 在题面里，PARAMS 的 rgb / flat_rgb 里没有" % rgb)
    for match in re.finditer(r"#([0-9A-Fa-f]{6})\b", body):
        hex_text = match.group(1)
        rgb = tuple(int(hex_text[i:i + 2], 16) for i in (0, 2, 4))
        if rgb not in colors:
            gaps.append("颜色 #%s 在题面里，PARAMS 里没有对应的 rgb" % hex_text.upper())
    number_body = body
    for path in paths:
        number_body = number_body.replace(path, " ")
    ints = set()
    collect_ints(params, ints)
    labeled = []
    for match in re.finditer(r"字号\s*(\d+)", number_body):
        labeled.append(("字号", int(match.group(1))))
    for match in re.finditer(r"(\d+)\s*点", number_body):
        labeled.append(("点数", int(match.group(1))))
    for match in re.finditer(r"(\d+)\s*ppi\b", number_body, re.I):
        labeled.append(("ppi", int(match.group(1))))
    for match in re.finditer(r"质量\s*(\d+)", number_body):
        labeled.append(("质量", int(match.group(1))))
    for match in re.finditer(r"(?:宽|高)\s*(\d+)", number_body):
        labeled.append(("宽或高", int(match.group(1))))
    seen_numbers = set()
    for label, number in labeled:
        if number in seen_numbers or number in dim_numbers:
            continue
        if 1900 <= number <= 2099:
            continue
        seen_numbers.add(number)
        if number not in ints:
            gaps.append("数字 %d（%s）在题面里，PARAMS 里没有这个数" % (number, label))
    if gaps:
        return {"status": "失败", "reason": "；".join(gaps), "gaps": gaps}
    return {"status": "通过", "reason": "题面里的格式、路径和上述数字在 PARAMS 里都有对应字段", "gaps": []}


def selftest_block_reason(text: str):
    if "osascript" in text or "subprocess" in text:
        return "夹具源码里有 osascript 或 subprocess，这次不跑"
    if "TemporaryDirectory" not in text:
        return "夹具没有临时目录，这次不跑，避免写到家目录"
    if ".show(" in text:
        return "夹具会打开图片窗口，这次不跑"
    return ""


def worker_main(selftest_path: str):
    tight = os.environ["E31_GATE_TIGHT"]
    stub = os.environ["E31_GATE_STUB"]
    task_dir = str(Path(selftest_path).resolve().parent)
    sys.path.insert(0, stub)
    sys.path.insert(0, tight)
    import e31_grade  # noqa: E402
    import e31_grade_ext  # noqa: E402

    calls = seal(e31_grade, patch_clock=True)
    sys.path.insert(0, task_dir)
    os.chdir(task_dir)
    import runpy

    code = 0
    try:
        runpy.run_path(selftest_path, run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (0, None):
            code = exc.code if isinstance(exc.code, int) else 1
    except Exception:
        traceback.print_exc()
        code = 1
    finally:
        print("OSASCRIPT_CALLS %d" % calls["n"], flush=True)
    raise SystemExit(code)


def run_selftest(selftest: Path, stub: Path):
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", ""),
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(TIGHT) + os.pathsep + str(stub),
        "E31_GATE_TIGHT": str(TIGHT),
        "E31_GATE_STUB": str(stub),
    }
    try:
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", str(selftest)],
            cwd=str(selftest.parent),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "失败",
            "reason": "夹具超过 120 秒还没结束",
            "stdout": (exc.stdout or "")[-500:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-500:] if isinstance(exc.stderr, str) else "",
            "calls": 0,
            "fakes": [],
            "references": [],
        }
    calls = 0
    payload = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("RESULT "):
            try:
                payload = json.loads(line[len("RESULT "):])
            except json.JSONDecodeError:
                payload = {"error": line[:300]}
        elif line.startswith("OSASCRIPT_CALLS "):
            try:
                calls = int(line.split()[1])
            except (IndexError, ValueError):
                calls = -1
    if proc.returncode != 0 or not isinstance(payload, dict) or "cases" not in payload:
        err = (proc.stderr or proc.stdout or "").strip().splitlines()
        tail = " | ".join(err[-4:])[:400]
        return {
            "status": "失败",
            "reason": "夹具没有跑完：%s" % (tail or "没有 RESULT"),
            "calls": calls,
            "fakes": [],
            "references": [],
        }
    cases = payload.get("cases") or []
    fakes = [case for case in cases if case.get("expect") == 0]
    references = [case for case in cases if case.get("expect") == 1]
    if calls:
        return {
            "status": "失败",
            "reason": "评分想调用 osascript %d 次，进程已被拦住，这道不记通过" % calls,
            "calls": calls,
            "fakes": fakes,
            "references": references,
        }
    if not fakes:
        return {
            "status": "未覆盖",
            "reason": "夹具里没有期望为 0 的用例",
            "calls": calls,
            "fakes": fakes,
            "references": references,
        }
    bad = [case for case in fakes if case.get("score") != 0]
    if bad:
        bits = []
        for case in bad:
            bits.append("%s 分数 %s（期望 0），reason=%s" % (case.get("class"), case.get("score"), case.get("reason")))
        return {
            "status": "失败",
            "reason": "；".join(bits),
            "calls": calls,
            "fakes": fakes,
            "references": references,
        }
    names = "、".join(str(case.get("class")) for case in fakes)
    return {
        "status": "通过",
        "reason": "%d 个假产物都是 0（%s）" % (len(fakes), names),
        "calls": calls,
        "fakes": fakes,
        "references": references,
    }


def fake_gate(task_dir: Path, stub: Path):
    selftest = task_dir / "selftest.py"
    if not selftest.is_file():
        return {"status": "未覆盖", "reason": "没有 selftest.py", "calls": 0, "fakes": [], "references": []}
    text = selftest.read_text(encoding="utf-8")
    blocked = selftest_block_reason(text)
    if blocked:
        return {"status": "未覆盖", "reason": blocked, "calls": 0, "fakes": [], "references": []}
    return run_selftest(selftest, stub)


def load_task(task_dir: Path):
    evaluation = task_dir / "evaluation.py"
    text = evaluation.read_text(encoding="utf-8")
    params = load_params(text)
    grader_name = "e31_grade_ext.grade" if "e31_grade_ext.grade" in text else "e31_grade.grade"
    instruction = ""
    task_json = task_dir / "task.json"
    if task_json.is_file():
        meta = json.loads(task_json.read_text(encoding="utf-8"))
        instruction = meta.get("instruction") or ""
    return params, grader_name, instruction


def cell(text: str) -> str:
    return str(text).replace("|", "/").replace("\n", " ")


def count_status(rows, key):
    counter = Counter(row[key]["status"] for row in rows)
    return counter["通过"], counter["失败"], counter["未覆盖"]


def first_failures(rows, key, limit=10):
    failed = [row for row in rows if row[key]["status"] == "失败"]
    return failed[:limit], len(failed)


def reference_note(row):
    refs = row["fake"].get("references") or []
    if not refs:
        return ""
    scores = "、".join("%s=%s" % (case.get("class"), case.get("score")) for case in refs)
    dropped = [case for case in refs if case.get("score") != 1]
    if dropped:
        return "对照夹具不再是 1（%s）" % scores
    return "对照夹具仍是 1（%s）" % scores


def lead(rows, level_counts):
    lines = []
    lines.append("可评分 %d 道。L1 %d 道，L2 %d 道。L3 和 L4 这次没有，脚本也不会标到这两级。" % (
        len(rows), level_counts.get("L1", 0), level_counts.get("L2", 0),
    ))
    g5_fail = [row for row in rows if row["true"]["status"] == "失败"]
    g3_fail = [row for row in rows if row["fake"]["status"] == "失败"]
    g6_fail = [row for row in rows if row["text"]["status"] == "失败"]
    if g5_fail:
        row = g5_fail[0]
        lines.append("真导出先看 `%s`。%s" % (row["id"], row["true"]["reason"]))
    else:
        covered = [row for row in rows if row["true"]["status"] != "未覆盖"]
        if covered:
            lines.append("本机对得上的真导出里，没有被打成 0 的。")
        else:
            lines.append("这四个目录里没有对上这个题包成品路径的真导出。")
    if g3_fail:
        row = g3_fail[0]
        lines.append("假产物先看 `%s`。%s" % (row["id"], row["fake"]["reason"]))
    else:
        dropped = [row for row in rows if any(case.get("score") != 1 for case in (row["fake"].get("references") or []))]
        lines.append("假产物 %d 道都是 0 分。另有 %d 道的对照夹具（selftest 里原来期望 1）在这份库下变成 0，这不记进假产物失败。" % (len(rows), len(dropped)))
    if g6_fail:
        row = g6_fail[0]
        shown = "；".join(row["text"]["gaps"][:3])
        lines.append("题面先看 `%s`。%s" % (row["id"], shown))
    else:
        lines.append("题面里抽出的格式、路径和数字，PARAMS 里都有对应字段。")
    return lines


def render(pack: Path, rows, manual_ids, files, missing_roots, blocked_calls, grades):
    level_counts = Counter(row["level"] for row in rows)
    g3 = count_status(rows, "fake")
    g5 = count_status(rows, "true")
    g6 = count_status(rows, "text")
    lines = []
    lines.append("类型：记录 ｜ 归属：11-24 E31 验证门实跑 ｜ 状态：维护中")
    lines.append("")
    lines.append("# %s：假产物、真导出、题面数字对过一遍" % pack.name)
    lines.append("")
    lines.append("命令只给了题包路径。评分用的是副本库 `_shared_tightened_1124_b`，PARAMS 里若有 `allowed` 会按它放行，没有这个键就和收紧库一样拒绝整张一种颜色。没有改题包，没有改 `_shared_tightened_1124`，没有改这份副本。没有开应用，没有 osascript，没有连生产机和集群。")
    lines.append("")
    for paragraph in lead(rows, level_counts):
        lines.append(paragraph)
        lines.append("")
    lines.append("## 各门题数")
    lines.append("")
    lines.append("| 门 | 通过 | 失败 | 未覆盖 |")
    lines.append("|---|---:|---:|---:|")
    lines.append("| 假产物（期望 0 的夹具在副本库下仍是 0） | %d | %d | %d |" % g3)
    lines.append("| 真产物（本机已有导出重打仍是 1） | %d | %d | %d |" % g5)
    lines.append("| 题面（格式、路径、数字在 PARAMS 里有对应字段） | %d | %d | %d |" % g6)
    lines.append("")
    lines.append("手工题 %d 道只标了 L0，上面三道门没有跑。" % len(manual_ids))
    lines.append("")
    lines.append("## 失败的前 10 道")
    lines.append("")
    for title, key in (("假产物", "fake"), ("真产物", "true"), ("题面", "text")):
        shown, total = first_failures(rows, key)
        lines.append("### %s" % title)
        lines.append("")
        if total == 0:
            lines.append("没有失败。")
            lines.append("")
            continue
        lines.append("失败 %d 道，下面是前 %d 道。" % (total, len(shown)))
        lines.append("")
        for index, row in enumerate(shown, 1):
            lines.append("%d. `%s`：%s" % (index, row["id"], row[key]["reason"]))
        lines.append("")
    dropped = [row for row in rows if any(case.get("score") != 1 for case in (row["fake"].get("references") or []))]
    lines.append("## 对照夹具")
    lines.append("")
    lines.append("selftest 里期望 1 的那条叫对照，不算假产物。它变成 0，只说明旧的正例在副本库下过不了，不把这道题算进假产物失败。这样的有 %d 道。" % len(dropped))
    if dropped:
        lines.append("")
        for row in dropped[:10]:
            lines.append("- `%s`：%s" % (row["id"], reference_note(row)))
        if len(dropped) > 10:
            lines.append("- 其余 %d 道同样是对照不再为 1，逐题表里的摘要写了。" % (len(dropped) - 10))
    lines.append("")
    lines.append("## 逐题")
    lines.append("")
    lines.append("| 题 | L | 假产物 | 真产物 | 题面 | 摘要 |")
    lines.append("|---|---|---|---|---|---|")
    for row in rows:
        bits = []
        if row["fake"]["status"] != "通过":
            bits.append("假产物" + row["fake"]["status"] + "：" + row["fake"]["reason"])
        elif reference_note(row).startswith("对照夹具不再"):
            bits.append(reference_note(row))
        if row["true"]["status"] != "通过":
            bits.append("真产物" + row["true"]["status"] + "：" + row["true"]["reason"])
        if row["text"]["status"] != "通过":
            bits.append("题面" + row["text"]["status"] + "：" + row["text"]["reason"])
        if not bits:
            bits.append(row["level_reason"])
        summary = " ".join(bits)
        if len(summary) > 500:
            summary = summary[:497] + "..."
        lines.append("| `%s` | %s | %s | %s | %s | %s |" % (
            row["id"], row["level"], row["fake"]["status"], row["true"]["status"], row["text"]["status"], cell(summary),
        ))
    lines.append("")
    lines.append("## 这次实际跑了什么")
    lines.append("")
    lines.append("- 题包：`%s`" % pack)
    lines.append("- 目录里 %d 道，可评分 %d 道，手工 %d 道。" % (len(rows) + len(manual_ids), len(rows), len(manual_ids)))
    lines.append("- 评分库：`%s`" % TIGHT)
    lines.append("- `e31_grade.py` SHA-256 前 12 位 `%s`，`e31_grade_ext.py` `%s`，`fixturelib.py` `%s`。" % grades)
    lines.append("- 真导出目录：")
    for root in GOLDEN_ROOTS:
        lines.append("  - `%s`" % root)
    if missing_roots:
        lines.append("- 上面有目录不存在：%s" % "、".join(missing_roots))
    lines.append("- 这四个目录里索引到 %d 个文件，含种子和别的题包的导出。文件名以「结束截图」开头的没有拿来打分。" % len(files))
    lines.append("- 拦住的 osascript 次数：%d。没有启动 osascript 进程。" % blocked_calls)
    lines.append("- 假产物来自各题 `selftest.py` 里期望分数为 0 的用例，夹具函数是副本库里的 `fixturelib`。临时目录由夹具自己建。")
    lines.append("- 题面门只做了机械对照：路径、格式词（PNG / JPEG / TIFF / PSD / PDF / SVG / TXT）、宽×高、括号里或 RGB 字样后面的三个颜色数、#RRGGBB、字号、点数、ppi、质量、单独写出的宽或高。同一个数只记一次。年份、1/30 这种分数、菜单名、字体名、「纯黑」这种没有数字的话，这次不抽。")
    lines.append("- L0 是手工。L1 是只有魔数、后缀或署名。L2 是 PARAMS 里有尺寸、抽样、正文或图层这类书面条件。写了基线路径也停在 L2。")
    lines.append("")
    lines.append("## 这次没跑")
    lines.append("")
    lines.append("- G0 规格门：要人先写产物和判据，脚本不代写。")
    lines.append("- G1 装配门：`tasks validate` 这次没跑。")
    lines.append("- G2 自洽门的五项期望没有按旧库再对一遍。假产物门只要求期望 0 的用例在副本库下是 0。")
    lines.append("- G4 归属门：`write_draft_baseline` 和 `write_flag_seal` 没有真跑，那要在生产机上写基线。")
    lines.append("- 题面门没有调模型。11-24 那份模型对照是另一份结果，不在这次里。")
    lines.append("- G7 真机冒烟、G8 停机保全、G9 人工金标准：没有生产机，也没有新的人工判定。")
    lines.append("- 手工题的三道门没有跑。")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def collect(pack: Path):
    sys.path.insert(0, str(TIGHT))
    import e31_grade  # noqa: E402
    import e31_grade_ext  # noqa: E402

    calls = seal(e31_grade, patch_clock=False)
    files, missing_roots = index_golden()
    stub_dir = Path(tempfile.mkdtemp(prefix="e31-gate-stub-"))
    (stub_dir / "task_api.py").write_text(STUB_SRC, encoding="utf-8")
    rows = []
    manual_ids = []
    try:
        task_dirs = sorted(path.parent for path in (pack / "tasks").glob("*/evaluation.py"))
        pending = []
        for task_dir in task_dirs:
            try:
                params, grader_name, instruction = load_task(task_dir)
            except (OSError, SyntaxError, ValueError, json.JSONDecodeError) as exc:
                rows.append({
                    "id": task_dir.name,
                    "level": "L1",
                    "level_reason": "读不到 PARAMS：%s" % exc,
                    "fake": {"status": "失败", "reason": "读不到 PARAMS", "references": [], "calls": 0},
                    "true": {"status": "未覆盖", "reason": "读不到 PARAMS", "files": []},
                    "text": {"status": "失败", "reason": "读不到 PARAMS", "gaps": ["读不到 PARAMS"]},
                })
                continue
            if not isinstance(params, dict) or params.get("kind") == "manual":
                manual_ids.append(task_dir.name)
                continue
            pending.append((task_dir, params, grader_name, instruction))
        from concurrent.futures import ThreadPoolExecutor

        def one_fake(item):
            task_dir, _params, _grader_name, _instruction = item
            return task_dir.name, fake_gate(task_dir, stub_dir)

        fake_by_id = {}
        with ThreadPoolExecutor(max_workers=4) as pool:
            for task_id, result in pool.map(one_fake, pending):
                fake_by_id[task_id] = result
        grade_of = {
            "e31_grade_ext.grade": e31_grade_ext.grade,
            "e31_grade.grade": e31_grade.grade,
        }
        for task_dir, params, grader_name, instruction in pending:
            level, level_reason = assign_level(params)
            true = true_export_gate(task_dir.name, params, grade_of[grader_name], files)
            text = consistency_gate(task_body(instruction), params)
            rows.append({
                "id": task_dir.name,
                "level": level,
                "level_reason": level_reason,
                "fake": fake_by_id[task_dir.name],
                "true": true,
                "text": text,
            })
    finally:
        for child in stub_dir.glob("*"):
            child.unlink()
        stub_dir.rmdir()
    rows.sort(key=lambda row: row["id"])
    grades = (sha12(TIGHT / "e31_grade.py"), sha12(TIGHT / "e31_grade_ext.py"), sha12(TIGHT / "fixturelib.py"))
    blocked = calls["n"] + sum(int(row["fake"].get("calls") or 0) for row in rows)
    return rows, manual_ids, files, missing_roots, blocked, grades


def main():
    import argparse

    parser = argparse.ArgumentParser(description="对一个 E31 题包跑本地验证门")
    parser.add_argument("pack", help="题包目录，例如 maccua-tasks/zyy-e31-gen-v4p")
    parser.add_argument("--out", help="把同一份 Markdown 再写到这个文件")
    args = parser.parse_args()
    pack = Path(args.pack).expanduser().resolve()
    if not (pack / "tasks").is_dir():
        print("题包目录里没有 tasks：%s" % pack, file=sys.stderr)
        raise SystemExit(2)
    if not (TIGHT / "e31_grade.py").is_file():
        print("找不到副本库：%s" % TIGHT, file=sys.stderr)
        raise SystemExit(2)
    rows, manual_ids, files, missing_roots, blocked, grades = collect(pack)
    report = render(pack, rows, manual_ids, files, missing_roots, blocked, grades)
    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(report, end="")
        print("wrote %s" % out, file=sys.stderr)
    else:
        print(report, end="")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--worker":
        worker_main(sys.argv[2])
    else:
        main()
