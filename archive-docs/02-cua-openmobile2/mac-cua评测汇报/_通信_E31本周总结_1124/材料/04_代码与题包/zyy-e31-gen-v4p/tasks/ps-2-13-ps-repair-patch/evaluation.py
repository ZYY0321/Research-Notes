import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-13-ps-repair-patch.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'samples': [{'x': 23, 'y': 15, 'rgb': [96, 144, 192], 'tol': 24}, {'x': 19, 'y': 11, 'rgb': [96, 144, 192], 'tol': 24}, {'x': 2, 'y': 2, 'rgb': [96, 144, 192], 'tol': 8}, {'x': 45, 'y': 29, 'rgb': [96, 144, 192], 'tol': 8}], 'grade_note': '核导出 PNG 为 48×32、带 Photoshop 署名，原瑕疵区域采样点呈干净背景色，画面四角等其余采样点与种子背景一致。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
