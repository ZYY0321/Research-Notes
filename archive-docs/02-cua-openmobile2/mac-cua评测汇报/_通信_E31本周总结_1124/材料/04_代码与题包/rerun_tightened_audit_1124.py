#!/usr/bin/env python3
"""Re-run the 11-24 adversarial audit on the tightened shared grader.

The original script and the three task packages are not modified. osascript
stays patched out. Output JSON is a new file, not the 11-24 audit dump.
"""
from __future__ import annotations

from pathlib import Path

AUDIT = Path(
    "/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/scripts/grade_adversarial_audit_1124.py"
)
TIGHT = Path("/Users/zhangyingying/CUA/评测集建设/maccua-tasks/_shared_tightened_1124")
OUT = Path(
    "/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/raw/评分器收紧_1124.json"
)

src = AUDIT.read_text(encoding="utf-8")
src = src.replace(
    'GRADE_SRC = ROOTS[0] / "shared" / "e31_grade.py"',
    'GRADE_SRC = Path("%s/e31_grade.py")' % TIGHT,
)
src = src.replace(
    'EXT_SRC = ROOTS[0] / "shared" / "e31_grade_ext.py"',
    'EXT_SRC = Path("%s/e31_grade_ext.py")' % TIGHT,
)
src = src.replace(
    "/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/raw/评分器对抗审计_1124.json",
    str(OUT),
)
old_hash = '''    hashes = {
        "v1p_grade": sha256(GRADE_SRC),
        "v2f_grade": sha256(ROOTS[1] / "shared" / "e31_grade.py"),
        "v2cli_grade": sha256(ROOTS[2] / "shared" / "e31_grade.py"),
        "v1p_ext": sha256(EXT_SRC),
        "v2f_ext": sha256(ROOTS[1] / "shared" / "e31_grade_ext.py"),
    }
    if len({hashes["v1p_grade"], hashes["v2f_grade"], hashes["v2cli_grade"]}) != 1:
        raise SystemExit("e31_grade.py differs across packages")
    if hashes["v1p_ext"] != hashes["v2f_ext"]:
        raise SystemExit("e31_grade_ext.py differs")
'''
new_hash = '''    hashes = {
        "tight_grade": sha256(GRADE_SRC),
        "v1p_grade": sha256(ROOTS[0] / "shared" / "e31_grade.py"),
        "v2f_grade": sha256(ROOTS[1] / "shared" / "e31_grade.py"),
        "v2cli_grade": sha256(ROOTS[2] / "shared" / "e31_grade.py"),
        "tight_ext": sha256(EXT_SRC),
        "v1p_ext": sha256(ROOTS[0] / "shared" / "e31_grade_ext.py"),
        "v2f_ext": sha256(ROOTS[1] / "shared" / "e31_grade_ext.py"),
    }
    if len({hashes["v1p_grade"], hashes["v2f_grade"], hashes["v2cli_grade"]}) != 1:
        raise SystemExit("e31_grade.py differs across packages")
    if hashes["v1p_ext"] != hashes["v2f_ext"]:
        raise SystemExit("e31_grade_ext.py differs")
'''
if old_hash not in src:
    raise SystemExit("hash block not found")
src = src.replace(old_hash, new_hash, 1)

old_flag = '''    ok, why = e31_grade.grade_flag_logic("no-message", "flagged=0\\ninbox=0\\n", 0)
    assert ok and why == "skipped_empty_inbox"
'''
new_flag = '''    ok, why = e31_grade.grade_flag_logic("no-message", "flagged=0\\ninbox=0\\n", 0)
    assert (not ok) and why == "empty_inbox_unsealed", (ok, why)
    ok, why = e31_grade.grade_flag_logic(
        "no-message", "flagged=0\\ninbox=0\\n", 0, "flagged=0\\ninbox=0\\n"
    )
    assert ok and why == "skipped_empty_inbox", (ok, why)
'''
if old_flag not in src:
    raise SystemExit("flag unit block not found")
src = src.replace(old_flag, new_flag, 1)

old_text = '''        out = e31_grade.grade_text({"kind": "text", "path": str(target), "contains": "DELETED"})
        assert out["score"] == 1, out
        out = e31_grade.grade_text({"kind": "text", "path": str(target), "contains": ["DELETED"]})
        assert out["score"] == 0, out
        notes.append("unit: contains as a string checks each character; DELTA scores 1 for DELETED")
'''
new_text = '''        out = e31_grade.grade_text({"kind": "text", "path": str(target), "contains": "DELETED"})
        assert out["score"] == 0, out
        out = e31_grade.grade_text({"kind": "text", "path": str(target), "contains": ["DELETED"]})
        assert out["score"] == 0, out
        target.write_text("DELETED", encoding="utf-8")
        out = e31_grade.grade_text({"kind": "text", "path": str(target), "contains": "DELETED"})
        assert out["score"] == 1, out
        notes.append("unit: a contains string is one phrase; DELTA scores 0, DELETED scores 1")
'''
if old_text not in src:
    raise SystemExit("text unit block not found")
src = src.replace(old_text, new_text, 1)

exec(compile(src, str(AUDIT), "exec"), {"__name__": "__main__"})
