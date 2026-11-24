import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-16-ps-shape-rectangle.png', 'width': 64, 'height': 48, 'require_app_signature': True, 'samples': [{'x': 2, 'y': 2, 'rgb': [230, 230, 230], 'tol': 12}, {'x': 61, 'y': 2, 'rgb': [230, 230, 230], 'tol': 12}, {'x': 2, 'y': 45, 'rgb': [230, 230, 230], 'tol': 12}, {'x': 61, 'y': 45, 'rgb': [230, 230, 230], 'tol': 12}, {'x': 20, 'y': 16, 'rgb': [200, 30, 40], 'tol': 12}, {'x': 32, 'y': 24, 'rgb': [200, 30, 40], 'tol': 12}, {'x': 44, 'y': 32, 'rgb': [200, 30, 40], 'tol': 12}], 'grade_note': '核导出 PNG 为 64×48，矩形区 (16,12)-(47,35) 内采样为填充色 RGB(200,30,40)，四角采样仍为底图色 RGB(230,230,230)，并带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
