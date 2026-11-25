import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"shortcuts","marker_file":"~/Desktop/e31-nologin/state/sc-two-mark.txt","where":[{"field":"KIND","eq":"shortcut"},{"field":"NAME","eq":"{marker}"},{"field":"ACTIONS","gte":2}],"grade_note":"名字等于标记，动作数至少 2。评分看动作个数，不读动作里的字。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
