import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"textedit_rtf","path":"~/Desktop/e31-nologin/seed/te-rtf-append.rtf","marker_file":"~/Desktop/e31-nologin/state/te-rtf-append-mark.txt","grade_note":"保留 KEEP-THIS-SENTENCE，并在它后面出现标记。纯文本或 textutil 转档没有窗口字段。","contains":["KEEP-THIS-SENTENCE","{marker}"],"order":true}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
