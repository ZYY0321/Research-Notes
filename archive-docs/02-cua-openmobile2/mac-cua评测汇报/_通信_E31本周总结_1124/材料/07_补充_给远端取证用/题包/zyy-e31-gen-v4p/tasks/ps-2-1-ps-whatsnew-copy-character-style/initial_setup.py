import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

NOTES_PATH = "~/e31-newapps/in/ps-2-1-notes.txt"
OUT_PATH = "~/e31-newapps/out/ps-2-1-ps-whatsnew-copy-character-style.psd"
NOTES_TEXT = (
    "ps-2-1 说明\n"
    "种子 PSD 里有两个文字块：\n"
    "源文字块：图层名 SOURCE（上方的标题文字块）\n"
    "目标文字块：图层名 TARGET（下方的正文文字块）\n"
    "请把 SOURCE 的字符样式拷贝到 TARGET 上，文字内容不要改。\n"
)

class Setup(BaseSetup):
    def run(self, context):
        out_expanded = os.path.expanduser(OUT_PATH)
        if os.path.lexists(out_expanded):
            os.remove(out_expanded)
        os.makedirs(os.path.dirname(out_expanded), exist_ok=True)
        notes_expanded = os.path.expanduser(NOTES_PATH)
        os.makedirs(os.path.dirname(notes_expanded), exist_ok=True)
        with open(notes_expanded, "w", encoding="utf-8") as handle:
            handle.write(NOTES_TEXT)
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"notes": NOTES_PATH}}
