import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-13-ps-repair-content-aware-fill.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'samples': [{'x': 23, 'y': 15, 'rgb': [96, 140, 190], 'tol': 30}, {'x': 20, 'y': 12, 'rgb': [96, 140, 190], 'tol': 30}, {'x': 27, 'y': 19, 'rgb': [96, 140, 190], 'tol': 30}, {'x': 2, 'y': 2, 'rgb': [96, 140, 190], 'tol': 8}, {'x': 45, 'y': 2, 'rgb': [96, 140, 190], 'tol': 8}, {'x': 2, 'y': 29, 'rgb': [96, 140, 190], 'tol': 8}, {'x': 45, 'y': 29, 'rgb': [96, 140, 190], 'tol': 8}], 'grade_note': '核导出 PNG 为 48×32、原物体区域像素接近背景色、画面其余采样点保持种子底色，并带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
