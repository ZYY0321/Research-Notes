import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-17-ps-text-font.png', 'width': 48, 'height': 24, 'require_app_signature': True, 'not_flat': True, 'differ_from': {'path': '~/e31-newapps/seed/ps-2-17-ps-text-font-seed.png', 'min_mean_abs': 8}, 'keep': {'path': '~/e31-newapps/seed/ps-2-17-ps-text-font-seed.png', 'width': 48, 'height': 24}, 'grade_note': '核导出 PNG 为 48×24、非纯色、与白底种子的平均像素差达标、带 Photoshop 署名，且种子图仍是 48×24 未被覆盖。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
