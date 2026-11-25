import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-17-ps-text-on-path.png', 'width': 64, 'height': 64, 'require_app_signature': True, 'differ_from': {'path': '~/Desktop/e31-newapps/ps-2-17-seed.png', 'min_mean_abs': 2}, 'grade_note': '核导出 PNG 为 64×64、带 Photoshop 署名，并且像素与种子图有可见差异（说明路径文字已经渲染进画布，而不是原样导出种子图）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
