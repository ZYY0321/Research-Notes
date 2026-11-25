import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-13-ps-repair-generate-background.png', 'width': 48, 'height': 48, 'require_app_signature': True, 'not_flat': True, 'samples': [{'x': 24, 'y': 24, 'rgb': [200, 60, 60], 'tol': 12}, {'x': 18, 'y': 29, 'rgb': [200, 60, 60], 'tol': 12}, {'x': 29, 'y': 18, 'rgb': [200, 60, 60], 'tol': 12}], 'differ_from': {'path': '~/Desktop/e31-newapps/seed/ps-2-13-ps-repair-generate-background-seed.png', 'min_mean_abs': 25}, 'grade_note': '核导出 PNG 为 48×48、带 Photoshop 署名、非纯色；主体区域采样点与种子一致，整图与种子有足够差异，说明原透明背景被生成内容填上了。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
