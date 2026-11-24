import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-15-ps-fill-objects-selections-layers.png', 'width': 48, 'height': 48, 'require_app_signature': True, 'samples': [{'x': 10, 'y': 10, 'rgb': [255, 0, 0], 'tol': 5}, {'x': 24, 'y': 24, 'rgb': [255, 0, 0], 'tol': 5}, {'x': 38, 'y': 38, 'rgb': [255, 0, 0], 'tol': 5}]}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
