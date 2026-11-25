import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-1-ps-whatsnew-generative-upscale.png', 'min_width': 33, 'min_height': 25, 'require_app_signature': True}

class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
