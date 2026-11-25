import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-11-clipping-mask.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'not_flat': True, 'samples': [{'x': 6, 'y': 16, 'rgb': [220, 40, 40], 'tol': 12}, {'x': 40, 'y': 16, 'rgb': [200, 200, 200], 'tol': 12}], 'grade_note': '核导出 PNG 为 48×32、左半红（220,40,40）右半灰（200,200,200）的剪贴蒙版合成效果，且带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
