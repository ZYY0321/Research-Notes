import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-6-new-doc-custom.png', 'width': 800, 'height': 600, 'require_app_signature': True, 'samples': [{'x': 400, 'y': 300, 'rgb': [255, 255, 255], 'tol': 0}]}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
