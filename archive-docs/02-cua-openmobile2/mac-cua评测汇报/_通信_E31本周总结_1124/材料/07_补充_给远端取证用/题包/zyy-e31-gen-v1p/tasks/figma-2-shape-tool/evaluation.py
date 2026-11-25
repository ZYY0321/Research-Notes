import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-shape-tool.png', 'width': 48, 'height': 48, 'samples': [{'x': 24, 'y': 24, 'rgb': [255, 0, 0], 'tol': 20}]}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
