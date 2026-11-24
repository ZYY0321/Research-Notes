import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-11-mask-from-transparency.png', 'width': 32, 'height': 32, 'require_app_signature': True, 'samples': [{'x': 16, 'y': 8, 'rgb': [255, 0, 0], 'tol': 10}]}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
