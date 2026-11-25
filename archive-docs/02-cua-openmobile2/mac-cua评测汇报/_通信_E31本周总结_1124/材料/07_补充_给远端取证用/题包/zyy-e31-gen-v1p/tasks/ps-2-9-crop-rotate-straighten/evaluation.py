import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-9-crop-rotate-straighten.png', 'width': 48, 'height': 48, 'require_app_signature': True, 'samples': [{'x': 3, 'y': 3, 'rgb': [200, 40, 40], 'tol': 30}, {'x': 44, 'y': 3, 'rgb': [40, 80, 200], 'tol': 30}, {'x': 3, 'y': 44, 'rgb': [200, 40, 40], 'tol': 30}, {'x': 44, 'y': 44, 'rgb': [40, 80, 200], 'tol': 30}, {'x': 29, 'y': 4, 'rgb': [40, 80, 200], 'tol': 30}, {'x': 20, 'y': 43, 'rgb': [200, 40, 40], 'tol': 30}], 'grade_note': '核转正后保存的 PNG 为 48×48、六个取样点颜色与转正参考一致，并带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
