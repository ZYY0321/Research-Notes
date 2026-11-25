import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-13-ps-repair-remove-tool.png', 'width': 60, 'height': 60, 'require_app_signature': True, 'samples': [{'x': 30, 'y': 30, 'rgb': [100, 150, 200], 'tol': 30}, {'x': 5, 'y': 5, 'rgb': [100, 150, 200], 'tol': 5}, {'x': 55, 'y': 55, 'rgb': [100, 150, 200], 'tol': 5}]}

class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
