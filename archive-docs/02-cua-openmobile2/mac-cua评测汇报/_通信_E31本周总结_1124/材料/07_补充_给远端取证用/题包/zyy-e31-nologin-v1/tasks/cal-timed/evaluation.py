import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"calendar","marker_file":"~/Desktop/e31-nologin/state/cal-timed-mark.txt","where":[{"field":"SUMMARY","eq":"{marker}"},{"field":"START","prefix":"{today}T15:00"},{"field":"END","prefix":"{today}T16:00"},{"field":"ALLDAY","eq":"false"}],"grade_note":"标题等于标记，开始今天 15:00，结束今天 16:00，不是全天。","today_file":"~/Desktop/e31-nologin/state/today.txt"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
