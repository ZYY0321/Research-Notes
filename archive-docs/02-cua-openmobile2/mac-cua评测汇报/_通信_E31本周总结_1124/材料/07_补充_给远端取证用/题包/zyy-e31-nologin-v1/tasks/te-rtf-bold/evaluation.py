import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"textedit_rtf","path":"~/Desktop/e31-nologin/out/te-rtf-bold.rtf","marker_file":"~/Desktop/e31-nologin/state/te-rtf-bold-mark.txt","grade_note":"标记必须落在粗体开关之间，同时要有文本编辑的窗口字段。","contains":["{marker}"],"bold":true,"bold_text":"{marker}"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
