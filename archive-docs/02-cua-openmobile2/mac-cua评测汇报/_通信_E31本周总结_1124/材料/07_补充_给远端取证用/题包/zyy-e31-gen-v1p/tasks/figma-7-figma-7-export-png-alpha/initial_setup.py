import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_path = os.path.expanduser('~/Desktop/e31-newapps/out/figma-7-figma-7-export-png-alpha.png')
        if os.path.lexists(out_path):
            os.remove(out_path)
        proc = subprocess.run(["open", "-a", 'Figma'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
