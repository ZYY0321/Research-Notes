import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-13-ps-repair-remove-bg.png', 'width': 64, 'height': 64, 'require_app_signature': True, 'samples': [{'x': 32, 'y': 32, 'rgb': [200, 50, 50], 'tol': 10}], 'differ_from': {'path': '~/Desktop/e31-newapps/seed/ps-2-13-ps-repair-remove-bg.png', 'min_mean_abs': 20}}

class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)