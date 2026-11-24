import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-21-ps-action-play-on-image.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'samples': [{'x': 0, 'y': 0, 'rgb': [225, 135, 55], 'tol': 8}, {'x': 47, 'y': 31, 'rgb': [225, 135, 55], 'tol': 8}, {'x': 24, 'y': 16, 'rgb': [225, 135, 55], 'tol': 8}], 'grade_note': '核保存的 PNG 为 48×32、三处取样为动作（反相）施加后的颜色 (225,135,55)，并且带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
