import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-15-ps-create-fill-patterns.png', 'width': 32, 'height': 32, 'require_app_signature': True, 'not_flat': True, 'samples': [{'x': 2, 'y': 2, 'rgb': [180, 40, 40], 'tol': 12}, {'x': 10, 'y': 2, 'rgb': [40, 60, 180], 'tol': 12}, {'x': 2, 'y': 10, 'rgb': [40, 60, 180], 'tol': 12}, {'x': 10, 'y': 10, 'rgb': [180, 40, 40], 'tol': 12}, {'x': 18, 'y': 18, 'rgb': [180, 40, 40], 'tol': 12}, {'x': 26, 'y': 18, 'rgb': [40, 60, 180], 'tol': 12}], 'grade_note': '核导出 PNG 为 32×32、按 8 像素格交错的红蓝棋盘（左上格为红），非纯色，并且带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
