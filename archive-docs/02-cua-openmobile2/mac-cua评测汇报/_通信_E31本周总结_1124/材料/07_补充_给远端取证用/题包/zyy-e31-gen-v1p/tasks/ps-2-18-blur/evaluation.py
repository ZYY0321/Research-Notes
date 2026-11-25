import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-18-blur.png', 'width': 32, 'height': 32, 'require_app_signature': True, 'differ_from': {'path': '~/Desktop/e31-newapps/seeds/ps-2-18-blur-baseline.png', 'min_mean_abs': 10}}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
