import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"notes","marker_file":"~/Desktop/e31-nologin/state/notes-folder-mark.txt","where":[{"field":"FOLDER","eq":"{marker}"},{"field":"PLAIN","has":"{marker}"}],"grade_note":"备忘的所在文件夹名称等于标记，纯文本里也有标记。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
