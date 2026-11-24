import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-25-ps-save-copy.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'samples': [{'x': 0, 'y': 0, 'rgb': [30, 120, 200], 'tol': 8}, {'x': 47, 'y': 31, 'rgb': [30, 120, 200], 'tol': 8}], 'keep': {'path': '~/e31-newapps/seed/ps-2-25-ps-save-copy-seed.png', 'width': 48, 'height': 32}, 'grade_note': '核副本 PNG 为 48×32、两角颜色与种子一致、带 Photoshop 署名，且种子文件仍在原处尺寸不变。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
