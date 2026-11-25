import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-16-ps-draw-straight-line.png', 'width': 64, 'height': 64, 'require_app_signature': True, 'not_flat': True, 'samples': [{'x': 0, 'y': 0, 'rgb': [240, 240, 240], 'tol': 10}, {'x': 63, 'y': 0, 'rgb': [240, 240, 240], 'tol': 10}, {'x': 0, 'y': 63, 'rgb': [240, 240, 240], 'tol': 10}, {'x': 63, 'y': 63, 'rgb': [240, 240, 240], 'tol': 10}]}

class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
