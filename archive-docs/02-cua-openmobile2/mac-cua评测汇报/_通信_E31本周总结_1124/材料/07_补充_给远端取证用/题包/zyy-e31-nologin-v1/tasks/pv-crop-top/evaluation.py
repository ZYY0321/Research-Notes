import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"preview_pdf","path":"~/Desktop/e31-nologin/out/pv-crop-top.pdf","mode":"crop","marker_file":"~/Desktop/e31-nologin/state/pv-crop-top-mark.txt","seed_token_file":"~/Desktop/e31-nologin/state/pv-crop-top-seed.txt","keep_path":"~/Desktop/e31-nologin/seed/pv-crop-top.pdf","keep_contains":"{seed}","keep_lacks":"{marker}","grade_note":"把页面裁成上半部分后另存。媒体框仍是原来的整页，裁剪框盖住上半页。SEED- 那行要还在。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
