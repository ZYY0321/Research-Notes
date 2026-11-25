import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        base = os.path.expanduser("~/Desktop/e31-newapps")
        os.makedirs(os.path.join(base, "out"), exist_ok=True)
        out_path = os.path.join(base, "out", "ps-2-1-ps-whatsnew-prompt-to-edit.png")
        if os.path.lexists(out_path):
            os.remove(out_path)
        prompt_path = os.path.join(base, "ps-2-1-prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write("Prompt to edit 提示词：把画面中的天空改成橙红色的日落效果。\n")
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026"], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"prompt_file": prompt_path}}
