import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-11-vector-mask.png', 'width': 48, 'height': 48, 'require_app_signature': True, 'samples': [{'x': 24, 'y': 24, 'rgb': [208, 64, 48], 'tol': 24}, {'x': 3, 'y': 3, 'rgb': [245, 246, 248], 'tol': 24}, {'x': 44, 'y': 3, 'rgb': [245, 246, 248], 'tol': 24}], 'grade_note': '核导出 PNG 为 48×48 且带 Photoshop 署名；圆心处为图层红色、圆外两角为底色，验证矢量蒙版合成后的像素效果。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
