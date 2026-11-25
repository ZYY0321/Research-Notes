import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'all', 'checks': [{'kind': 'prefix', 'path': '~/Desktop/e31-newapps/out/ps-2-11-object-mask.psd', 'prefix': '8BPS'}, {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-11-object-mask.png', 'width': 48, 'height': 32, 'color_type': 6, 'require_app_signature': True, 'samples': [{'x': 24, 'y': 16, 'rgb': [178, 34, 34], 'tol': 16}, {'x': 14, 'y': 10, 'rgb': [178, 34, 34], 'tol': 16}]}], 'grade_note': '核 PSD 存在且以 8BPS 开头；导出 PNG 为 48×32 RGBA、带 Photoshop 署名，对象区域两处采样仍为深红。蒙版方向反了则对象处不再是深红，不给分。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
