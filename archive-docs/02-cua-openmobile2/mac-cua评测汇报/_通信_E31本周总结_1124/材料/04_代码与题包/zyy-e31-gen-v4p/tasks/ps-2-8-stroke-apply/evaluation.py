import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-8-stroke-apply.png', 'width': 64, 'height': 64, 'require_app_signature': True, 'samples': [{'x': 7, 'y': 16, 'rgb': [255, 0, 0], 'tol': 10}, {'x': 16, 'y': 7, 'rgb': [255, 0, 0], 'tol': 10}, {'x': 56, 'y': 16, 'rgb': [255, 0, 0], 'tol': 10}, {'x': 16, 'y': 56, 'rgb': [255, 0, 0], 'tol': 10}]}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
