import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"calendar","marker_file":"~/Desktop/e31-nologin/state/cal-location-mark.txt","where":[{"field":"SUMMARY","eq":"E31会面"},{"field":"LOCATION","eq":"{marker}"}],"grade_note":"标题是 E31会面，地点等于标记。","today_file":"~/Desktop/e31-nologin/state/today.txt"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
