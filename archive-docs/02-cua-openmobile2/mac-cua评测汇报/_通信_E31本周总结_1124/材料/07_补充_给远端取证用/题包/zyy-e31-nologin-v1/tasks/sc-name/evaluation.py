import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"shortcuts","marker_file":"~/Desktop/e31-nologin/state/sc-name-mark.txt","where":[{"field":"KIND","eq":"shortcut"},{"field":"NAME","eq":"{marker}"},{"field":"ACTIONS","gte":1}],"grade_note":"快捷指令列表里有这个名字，动作数至少 1。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
