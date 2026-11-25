import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser("~/Desktop/e31-newapps/out")
        os.makedirs(out_dir, exist_ok=True)
        note = os.path.join(out_dir, "figma-1-figma-tour-file-browser.txt")
        if os.path.lexists(note):
            os.remove(note)
        proc = subprocess.run(["open", "-a", "Figma"], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
