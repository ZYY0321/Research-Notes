import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-14-ps-color-effect.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'samples': [{'x': 2, 'y': 2, 'rgb': [150, 118, 82], 'tol': 10}, {'x': 24, 'y': 16, 'rgb': [150, 118, 82], 'tol': 10}, {'x': 45, 'y': 29, 'rgb': [150, 118, 82], 'tol': 10}], 'grade_note': '核导出 PNG 为 48×32，三处取样点与参考图的暖褐色一致，并且带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
