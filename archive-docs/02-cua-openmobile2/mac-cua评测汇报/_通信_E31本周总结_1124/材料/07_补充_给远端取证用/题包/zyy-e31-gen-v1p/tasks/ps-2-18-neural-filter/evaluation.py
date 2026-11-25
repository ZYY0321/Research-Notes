import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-18-neural-filter.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'differ_from': {'path': '~/Desktop/e31-newapps/seed/ps-2-18-neural-filter-seed.png', 'min_mean_abs': 3}, 'keep': {'path': '~/Desktop/e31-newapps/seed/ps-2-18-neural-filter-seed.png', 'width': 48, 'height': 32}, 'grade_note': '核导出 PNG 为 48×32、带 Photoshop 署名、像素与种子图有差异，且种子图保持 48×32 未被覆盖。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
