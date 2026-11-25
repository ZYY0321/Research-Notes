import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-14-ps-choose-color-apply.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'samples': [{'x': 0, 'y': 0, 'rgb': [31, 119, 180], 'tol': 2}, {'x': 24, 'y': 16, 'rgb': [31, 119, 180], 'tol': 2}, {'x': 47, 'y': 31, 'rgb': [31, 119, 180], 'tol': 2}], 'grade_note': '核导出 PNG 为 48×32、三个取样点的像素都等于说明文件给出的颜色 RGB(31,119,180)，并且带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
