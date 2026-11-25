import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-11-layer-mask-add.png', 'width': 48, 'height': 32, 'not_flat': True, 'require_app_signature': True, 'samples': [{'x': 4, 'y': 16, 'rgb': [220, 40, 40], 'tol': 8}, {'x': 44, 'y': 16, 'rgb': [30, 90, 200], 'tol': 8}], 'grade_note': '核导出 PNG 为 48×32、非纯色，左半取样为底色红 (220,40,40)、右半取样为上层蓝 (30,90,200)，并带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
