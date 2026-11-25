import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"textedit_rtf","path":"~/Desktop/e31-nologin/out/te-rtf-marker.rtf","marker_file":"~/Desktop/e31-nologin/state/te-rtf-marker-mark.txt","grade_note":"正文去掉空白后必须正好是标记，并且文件带文本编辑存储时写上的窗口字段。","exact":"{marker}"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
