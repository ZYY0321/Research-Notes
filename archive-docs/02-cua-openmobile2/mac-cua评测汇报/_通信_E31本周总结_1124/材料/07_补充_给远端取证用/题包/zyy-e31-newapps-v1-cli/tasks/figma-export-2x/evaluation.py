import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/figma-2x.png', 'width': 800, 'height': 600, 'grade_note': '只核导出 PNG 为 800×600。不核 2 倍是不是从 400×300 来的。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
