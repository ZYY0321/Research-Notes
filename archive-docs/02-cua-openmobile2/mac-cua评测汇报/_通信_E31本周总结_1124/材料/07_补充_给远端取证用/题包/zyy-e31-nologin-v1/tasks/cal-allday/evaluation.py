import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"calendar","marker_file":"~/Desktop/e31-nologin/state/cal-allday-mark.txt","where":[{"field":"SUMMARY","eq":"{marker}"},{"field":"ALLDAY","eq":"true"},{"field":"START","prefix":"{tomorrow}"}],"grade_note":"全天，标题等于标记，日期是今天的下一天。","today_file":"~/Desktop/e31-nologin/state/today.txt"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
