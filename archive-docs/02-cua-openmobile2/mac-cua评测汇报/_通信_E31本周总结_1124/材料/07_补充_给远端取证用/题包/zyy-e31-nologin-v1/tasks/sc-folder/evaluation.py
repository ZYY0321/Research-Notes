import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"shortcuts","marker_file":"~/Desktop/e31-nologin/state/sc-folder-mark.txt","where":[{"field":"KIND","eq":"shortcut"},{"field":"FOLDER","eq":"{marker}"},{"field":"ACTIONS","gte":1}],"grade_note":"有一条快捷指令的所在文件夹等于标记，且动作数至少 1。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
