import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"textedit_rtf","path":"~/Desktop/e31-nologin/out/te-rtf-keep.rtf","marker_file":"~/Desktop/e31-nologin/state/te-rtf-keep-mark.txt","grade_note":"新文件是带窗口字段的富文本；原稿仍含 TOKEN，且没有这次的标记。","contains":["KEEP-THIS-SENTENCE","{marker}"],"forbids":["TOKEN"],"keep_path":"~/Desktop/e31-nologin/seed/te-rtf-keep.txt","keep_contains":"TOKEN","keep_lacks":"{marker}"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
