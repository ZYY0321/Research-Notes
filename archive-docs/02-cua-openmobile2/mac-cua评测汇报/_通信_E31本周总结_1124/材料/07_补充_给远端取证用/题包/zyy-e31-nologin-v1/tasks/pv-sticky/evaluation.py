import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"preview_pdf","path":"~/Desktop/e31-nologin/out/pv-sticky.pdf","mode":"sticky","marker_file":"~/Desktop/e31-nologin/state/pv-sticky-mark.txt","seed_token_file":"~/Desktop/e31-nologin/state/pv-sticky-seed.txt","keep_path":"~/Desktop/e31-nologin/seed/pv-sticky.pdf","keep_contains":"{seed}","keep_lacks":"{marker}","grade_note":"在副本上加一张便签批注，文字是标记；原页上的 SEED- 那行还在。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
