import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"all","checks":[{"kind":"app_state","app":"photos","marker_file":"~/Desktop/e31-nologin/state/deep-photos-note-mark.txt","where":[{"field":"KIND","eq":"album"},{"field":"NAME","eq":"{marker}"}],"grade_note":"相簿名字等于标记。"},{"kind":"app_state","app":"notes","marker_file":"~/Desktop/e31-nologin/state/deep-photos-note-mark.txt","where":[{"field":"PLAIN","has":"{marker}"},{"field":"PLAIN","has":"ALBUM"}],"grade_note":"备忘里有标记和 ALBUM。"}],"grade_note":"相簿名等于标记，备忘纯文本里有 ALBUM 和标记。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
