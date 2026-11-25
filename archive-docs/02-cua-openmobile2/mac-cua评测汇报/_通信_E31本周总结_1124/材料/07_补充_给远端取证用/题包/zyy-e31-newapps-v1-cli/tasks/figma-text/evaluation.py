import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/figma-text.png', 'min_width': 32, 'min_height': 32, 'grade_note': '只核 PNG 能解码且宽高不小于 32。不识别图里有没有 E31-FIGMA 这几个字。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
