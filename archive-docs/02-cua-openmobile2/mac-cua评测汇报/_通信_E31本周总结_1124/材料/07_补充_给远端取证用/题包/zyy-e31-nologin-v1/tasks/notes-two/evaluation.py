import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"notes","marker_file":"~/Desktop/e31-nologin/state/notes-two-mark.txt","where":[{"field":"PLAIN","has":"AGENDA"},{"field":"PLAIN","has":"{marker}"}],"grade_note":"纯文本里 AGENDA 和标记都在。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
