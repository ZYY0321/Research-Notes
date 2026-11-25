import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"notes","marker_file":"~/Desktop/e31-nologin/state/notes-sentence-mark.txt","where":[{"field":"PLAIN","has":"KEEP-THIS-SENTENCE"},{"field":"PLAIN","has":"{marker}"}],"grade_note":"这条备忘的纯文本里同时有种子句和标记。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
