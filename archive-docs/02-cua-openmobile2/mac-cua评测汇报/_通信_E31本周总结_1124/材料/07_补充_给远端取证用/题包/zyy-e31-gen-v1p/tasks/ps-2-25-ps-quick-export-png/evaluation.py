import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-25-ps-quick-export-png.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'samples': [{'x': 0, 'y': 0, 'rgb': [34, 120, 200], 'tol': 8}, {'x': 47, 'y': 31, 'rgb': [34, 120, 200], 'tol': 8}], 'grade_note': '核导出 PNG 为 48×32、像素颜色与种子文档一致，并且带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
