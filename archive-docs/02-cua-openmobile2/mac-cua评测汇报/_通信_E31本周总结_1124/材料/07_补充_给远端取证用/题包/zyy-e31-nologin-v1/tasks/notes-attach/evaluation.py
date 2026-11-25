import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"notes","marker_file":"~/Desktop/e31-nologin/state/notes-attach-mark.txt","where":[{"field":"PLAIN","has":"{marker}"},{"field":"ATTACH","has":"notes-brief.txt"}],"grade_note":"备忘纯文本含标记，附件名里有 notes-brief.txt。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
