import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-18-stylize.png', 'width': 48, 'height': 48, 'require_app_signature': True, 'keep': {'path': '~/Desktop/e31-newapps/ps-2-18-stylize-seed.png', 'width': 48, 'height': 48}, 'differ_from': {'path': '~/Desktop/e31-newapps/ps-2-18-stylize-seed.png', 'min_mean_abs': 8}, 'grade_note': '核输出 PNG 为 48×48、带 Photoshop 署名、像素与种子图有明显差异，且种子图原样保留。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
