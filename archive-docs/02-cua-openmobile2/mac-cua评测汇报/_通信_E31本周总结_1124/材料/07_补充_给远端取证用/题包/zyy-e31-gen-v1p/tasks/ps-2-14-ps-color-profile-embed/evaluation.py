import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-14-ps-color-profile-embed.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'samples': [{'x': 2, 'y': 2, 'rgb': [120, 60, 200], 'tol': 12}, {'x': 45, 'y': 29, 'rgb': [120, 60, 200], 'tol': 12}], 'grade_note': '核保存出的 PNG 为 48×32、像素仍是种子颜色，并且带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
