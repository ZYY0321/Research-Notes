import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"reminders","marker_file":"~/Desktop/e31-nologin/state/rem-complete-mark.txt","where":[{"field":"NAME","eq":"{marker}"},{"field":"COMPLETED","eq":"true"}],"grade_note":"标题等于标记，且已完成。","today_file":"~/Desktop/e31-nologin/state/today.txt"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
