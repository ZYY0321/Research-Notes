import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"shortcuts","marker_file":"~/Desktop/e31-nologin/state/sc-input-mark.txt","where":[{"field":"KIND","eq":"shortcut"},{"field":"NAME","eq":"{marker}"},{"field":"ACCEPTS","eq":"true"},{"field":"ACTIONS","gte":1}],"grade_note":"名字等于标记，接收输入为真，动作数至少 1。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
