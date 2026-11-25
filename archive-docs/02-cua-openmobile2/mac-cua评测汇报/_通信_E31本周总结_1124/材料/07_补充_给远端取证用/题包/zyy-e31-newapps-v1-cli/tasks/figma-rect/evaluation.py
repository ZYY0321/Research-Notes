import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/figma-rect.png', 'width': 800, 'height': 600, 'not_flat': True, 'grade_note': '核 PNG 正好 800×600，且不是整张纯色。不核矩形的位置和大小。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
