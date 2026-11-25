import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-9-crop-drag-edges.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'samples': [{'x': 24, 'y': 16, 'rgb': [120, 180, 220], 'tol': 2}, {'x': 10, 'y': 10, 'rgb': [120, 180, 220], 'tol': 2}, {'x': 40, 'y': 25, 'rgb': [120, 180, 220], 'tol': 2}]}

class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
