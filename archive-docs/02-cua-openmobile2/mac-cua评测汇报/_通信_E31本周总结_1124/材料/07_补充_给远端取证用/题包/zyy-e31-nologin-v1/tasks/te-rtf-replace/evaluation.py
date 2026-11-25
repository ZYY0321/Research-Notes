import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"textedit_rtf","path":"~/Desktop/e31-nologin/seed/te-rtf-replace.rtf","marker_file":"~/Desktop/e31-nologin/state/te-rtf-replace-mark.txt","grade_note":"标记替换 TOKEN，原句还在。文件里不能再出现 TOKEN。","contains":["KEEP-THIS-SENTENCE","{marker}"],"forbids":["TOKEN"]}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
