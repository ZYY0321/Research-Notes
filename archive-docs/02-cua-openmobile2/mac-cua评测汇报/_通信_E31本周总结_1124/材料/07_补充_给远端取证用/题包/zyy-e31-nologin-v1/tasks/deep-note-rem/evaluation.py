import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"all","checks":[{"kind":"app_state","app":"notes","marker_file":"~/Desktop/e31-nologin/state/deep-note-rem-mark.txt","where":[{"field":"PLAIN","has":"KEEP-BRIEF"},{"field":"PLAIN","has":"{marker}"}],"grade_note":"备忘纯文本含种子句和标记。"},{"kind":"app_state","app":"reminders","marker_file":"~/Desktop/e31-nologin/state/deep-note-rem-mark.txt","where":[{"field":"NAME","eq":"{marker}"},{"field":"BODY","has":"KEEP-BRIEF"}],"grade_note":"提醒标题是标记，备注含 KEEP-BRIEF。","today_file":"~/Desktop/e31-nologin/state/today.txt"}],"grade_note":"备忘和提醒都要带上同一个标记，提醒备注里还有种子句。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
