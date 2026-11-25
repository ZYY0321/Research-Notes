import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"preview_pdf","path":"~/Desktop/e31-nologin/out/pv-highlight.pdf","mode":"highlight","marker_file":"~/Desktop/e31-nologin/state/pv-highlight-mark.txt","seed_token_file":"~/Desktop/e31-nologin/state/pv-highlight-seed.txt","keep_path":"~/Desktop/e31-nologin/seed/pv-highlight.pdf","keep_contains":"{seed}","keep_lacks":"{marker}","grade_note":"把页面上 SEED- 开头的那行高亮，存成副本。不要删掉那行文字。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
