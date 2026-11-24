import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-14-ps-color-correction-neutral.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'samples': [{'x': 2, 'y': 2, 'rgb': [128, 128, 128], 'tol': 8}, {'x': 45, 'y': 29, 'rgb': [128, 128, 128], 'tol': 8}], 'grade_note': '核 48×32 PNG 两处采样像素回到中性灰 128,128,128（容差 8），并带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
