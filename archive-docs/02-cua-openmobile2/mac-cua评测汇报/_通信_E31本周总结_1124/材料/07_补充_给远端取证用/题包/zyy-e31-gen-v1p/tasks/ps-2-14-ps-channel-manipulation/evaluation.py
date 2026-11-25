import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-14-ps-channel-manipulation.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'keep': {'path': '~/Desktop/e31-newapps/seed/ps-2-14-ps-channel-manipulation-seed.png', 'width': 48, 'height': 32}, 'samples': [{'x': 0, 'y': 0, 'rgb': [120, 255, 200], 'tol': 6}, {'x': 47, 'y': 31, 'rgb': [120, 255, 200], 'tol': 6}, {'x': 24, 'y': 16, 'rgb': [120, 255, 200], 'tol': 6}], 'grade_note': '核保存出的 PNG 为 48×32、带 Photoshop 署名，合成像素为绿色通道填满 255 后的 (120,255,200)，且种子图仍是 48×32。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
