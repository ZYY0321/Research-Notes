import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"preview_pdf","path":"~/Desktop/e31-nologin/out/pv-freetext.pdf","mode":"freetext","marker_file":"~/Desktop/e31-nologin/state/pv-freetext-mark.txt","seed_token_file":"~/Desktop/e31-nologin/state/pv-freetext-seed.txt","keep_path":"~/Desktop/e31-nologin/seed/pv-freetext.pdf","keep_contains":"{seed}","keep_lacks":"{marker}","grade_note":"在副本上加一条自由文本批注，内容是标记；原页上的 SEED- 那行还在。批注要带预览写进 PDF 的富文本字段。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
