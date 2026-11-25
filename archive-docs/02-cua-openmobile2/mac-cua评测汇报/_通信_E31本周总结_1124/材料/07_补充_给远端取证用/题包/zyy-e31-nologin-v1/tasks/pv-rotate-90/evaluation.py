import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"preview_pdf","path":"~/Desktop/e31-nologin/out/pv-rotate-90.pdf","mode":"rotate","marker_file":"~/Desktop/e31-nologin/state/pv-rotate-90-mark.txt","seed_token_file":"~/Desktop/e31-nologin/state/pv-rotate-90-seed.txt","keep_path":"~/Desktop/e31-nologin/seed/pv-rotate-90.pdf","keep_contains":"{seed}","keep_lacks":"{marker}","grade_note":"把这一页按给定角度旋转后另存。页面上的 SEED- 那行要还在，不要把页面重画成一张图。","angle":90}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
