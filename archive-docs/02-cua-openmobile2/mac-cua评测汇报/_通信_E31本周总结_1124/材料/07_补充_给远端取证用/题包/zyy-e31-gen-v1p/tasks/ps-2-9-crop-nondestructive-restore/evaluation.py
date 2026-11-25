import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'all', 'checks': [{'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-9-crop-nondestructive-restore-cropped.png', 'width': 40, 'height': 30, 'require_app_signature': True}, {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-9-crop-nondestructive-restore-restored.png', 'width': 64, 'height': 64, 'require_app_signature': True, 'samples': [{'x': 32, 'y': 32, 'rgb': [80, 120, 160], 'tol': 10}]}]}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
