import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-13-ps-repair-clone-stamp.png', 'width': 48, 'height': 48, 'require_app_signature': True, 'samples': [{'x': 33, 'y': 33, 'rgb': [86, 124, 70], 'tol': 12}, {'x': 30, 'y': 37, 'rgb': [86, 124, 70], 'tol': 12}, {'x': 4, 'y': 4, 'rgb': [86, 124, 70], 'tol': 12}, {'x': 44, 'y': 10, 'rgb': [86, 124, 70], 'tol': 12}], 'grade_note': '核导出 PNG 为 48×48、带 Photoshop 署名；原红色图案区域内两处取样点与背景绿 (86,124,70) 接近，画面其余两处取样点仍为背景绿。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
