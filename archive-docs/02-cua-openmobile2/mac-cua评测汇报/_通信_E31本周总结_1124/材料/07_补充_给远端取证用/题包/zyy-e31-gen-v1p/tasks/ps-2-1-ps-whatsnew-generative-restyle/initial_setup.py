import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED_URL = "https://picsum.photos/seed/ps21/800/600"
SEED_PATH = "~/Desktop/e31-newapps/seed/ps-2-1-seed.jpg"
OUT_PATH = "~/Desktop/e31-newapps/out/ps-2-1-ps-whatsnew-generative-restyle.png"

class Setup(BaseSetup):
    def run(self, context):
        out = os.path.expanduser(OUT_PATH)
        if os.path.lexists(out):
            os.remove(out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        seed = os.path.expanduser(SEED_PATH)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        if not os.path.exists(seed):
            proc = subprocess.run(["curl", "-L", "--fail", "--max-time", "120", "-o", seed, SEED_URL], capture_output=True, text=True)
            if proc.returncode != 0 or not os.path.exists(seed) or os.path.getsize(seed) == 0:
                return {"status": "failed", "state": {"step": "download_seed", "code": proc.returncode}}
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"step": "open_app", "code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
