import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-8-frame-place-image.png', 'width': 48, 'height': 48, 'require_app_signature': True, 'samples': [{'x': 24, 'y': 24, 'rgb': [210, 120, 40], 'tol': 12}], 'grade_note': '核导出 PNG 为 48×48、画框中心像素为照片颜色 (210,120,40)，并带 Photoshop 署名；空画框的导出中心仍是底色，过不了。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
