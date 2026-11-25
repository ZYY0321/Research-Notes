import datetime, os, subprocess, sys, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup
import nologin_seed as seed

MARKER_PATH = '~/Desktop/e31-nologin/state/te-rtf-append-mark.txt'
TODAY_PATH = '~/Desktop/e31-nologin/state/today.txt'
CLEAR = ['~/Desktop/e31-nologin/seed/te-rtf-append.rtf']
OPENS = [{'name': 'TextEdit', 'file': '~/Desktop/e31-nologin/seed/te-rtf-append.rtf'}]
SEEDS = [{'kind': 'rtf', 'path': '~/Desktop/e31-nologin/seed/te-rtf-append.rtf', 'text': 'KEEP-THIS-SENTENCE\n'}]


class Setup(BaseSetup):
    def run(self, context):
        today = datetime.date.today().isoformat()
        seed.write_text(TODAY_PATH, today + "\n")
        marker = seed.alphabet_token("E31-")
        seed.write_text(MARKER_PATH, marker + "\n")
        for rel in CLEAR:
            path = os.path.expanduser(rel)
            if os.path.lexists(path) and not os.path.isdir(path):
                os.remove(path)
        seed.apply(SEEDS, marker, today)
        opened = []
        errors = []
        for item in OPENS:
            cmd = ["open", "-a", item["name"]]
            if item.get("file"):
                cmd.append(os.path.expanduser(item["file"]))
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                errors.append({"name": item["name"], "code": proc.returncode, "stderr": (proc.stderr or "")[:400]})
            else:
                opened.append(item["name"])
        if len(opened) != len(OPENS):
            sys.stderr.write("open failed\n")
            return {"status": "failed", "state": {"errors": errors, "opened": opened}}
        time.sleep(2)
        return {"status": "completed", "state": {"opened": opened, "marker_path": MARKER_PATH}}
