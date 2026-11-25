import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"calendar","marker_file":"~/Desktop/e31-nologin/state/cal-alarm-mark.txt","where":[{"field":"SUMMARY","eq":"{marker}"},{"field":"ALARM","eq":"-15"}],"grade_note":"标题等于标记，显示提醒的触发间隔是 -15 分钟。","today_file":"~/Desktop/e31-nologin/state/today.txt"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
