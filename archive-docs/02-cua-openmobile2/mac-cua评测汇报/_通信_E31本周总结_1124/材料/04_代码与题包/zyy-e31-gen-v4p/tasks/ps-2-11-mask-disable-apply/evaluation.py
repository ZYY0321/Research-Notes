import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-11-mask-disable-apply.png', 'width': 48, 'height': 48, 'not_flat': True, 'require_app_signature': True, 'samples': [{'x': 12, 'y': 12, 'rgb': [220, 30, 30], 'tol': 16}, {'x': 12, 'y': 36, 'rgb': [220, 30, 30], 'tol': 16}, {'x': 36, 'y': 12, 'rgb': [0, 64, 224], 'tol': 16}, {'x': 36, 'y': 36, 'rgb': [0, 64, 224], 'tol': 16}], 'grade_note': '核导出 PNG 为 48×48：左半从上到下全红（含上半，说明蒙版已停用）、右半为种子蓝，整图非纯色，且带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
