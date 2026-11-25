import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-figma-combine-layers-boolean.png', 'width': 48, 'height': 48, 'samples': [{'x': 16, 'y': 24, 'rgb': [50, 100, 200], 'tol': 15}, {'x': 24, 'y': 24, 'rgb': [50, 100, 200], 'tol': 15}, {'x': 32, 'y': 24, 'rgb': [50, 100, 200], 'tol': 15}]}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
