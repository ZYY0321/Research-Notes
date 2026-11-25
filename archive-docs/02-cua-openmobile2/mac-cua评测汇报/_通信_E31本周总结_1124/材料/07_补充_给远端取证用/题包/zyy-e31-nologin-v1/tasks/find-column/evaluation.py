import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"finder_view","path":"~/Desktop/e31-nologin/seed/find-column/.DS_Store","view":"clmv","grade_note":".DS_Store 是 Bud1，并且视图记录是 clmv。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
