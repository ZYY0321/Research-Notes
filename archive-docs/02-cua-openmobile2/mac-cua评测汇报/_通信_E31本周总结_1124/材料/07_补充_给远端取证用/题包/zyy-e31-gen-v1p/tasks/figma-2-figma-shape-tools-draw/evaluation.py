import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-figma-shape-tools-draw.png', 'width': 120, 'height': 80, 'samples': [{'x': 20, 'y': 20, 'rgb': [255, 0, 0], 'tol': 10}, {'x': 65, 'y': 42, 'rgb': [255, 0, 0], 'tol': 10}, {'x': 102, 'y': 60, 'rgb': [255, 0, 0], 'tol': 10}], 'not_flat': True}

class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
