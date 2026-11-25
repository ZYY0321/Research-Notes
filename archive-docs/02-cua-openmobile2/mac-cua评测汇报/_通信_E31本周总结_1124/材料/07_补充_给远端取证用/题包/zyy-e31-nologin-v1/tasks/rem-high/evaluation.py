import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"reminders","marker_file":"~/Desktop/e31-nologin/state/rem-high-mark.txt","where":[{"field":"NAME","eq":"{marker}"},{"field":"PRIORITY","gte":1,"lte":4}],"grade_note":"标题等于标记，优先级数字在 1 到 4（提醒事项里的高）。","today_file":"~/Desktop/e31-nologin/state/today.txt"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
