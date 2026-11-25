import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser("~/Desktop/e31-newapps/out")
        os.makedirs(out_dir, exist_ok=True)
        for path in ["~/Desktop/e31-newapps/out/ps-2-1-ps-whatsnew-generative-recompose.png"]:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
