import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"textedit_rtf","path":"~/Desktop/e31-nologin/out/te-rtf-two.rtf","marker_file":"~/Desktop/e31-nologin/state/te-rtf-two-mark.txt","grade_note":"AGENDA 在前，标记在后。","contains":["AGENDA","{marker}"],"order":true}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
