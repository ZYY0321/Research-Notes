import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-18-sharpen.png', 'width': 48, 'height': 48, 'require_app_signature': True, 'differ_from': {'path': '~/Desktop/e31-newapps/seed/ps-2-18-sharpen-seed.png', 'min_mean_abs': 3}, 'grade_note': '核导出 PNG 为 48×48、带 Photoshop 署名，且像素与种子图有可见差异（锐化已应用）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
