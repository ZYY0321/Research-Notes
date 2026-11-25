import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        for path in ['~/Desktop/e31-newapps/out/figma-4-create-slots.png']:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        os.makedirs(os.path.expanduser('~/Desktop/e31-newapps/out'), exist_ok=True)
        proc = subprocess.run(["open", "-a", 'Figma'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
