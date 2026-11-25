import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-7-fill-show-in-exports-off.png', 'width': 40, 'height': 24, 'samples': [{'x': 2, 'y': 2, 'rgb': [0, 0, 0], 'tol': 2}, {'x': 20, 'y': 12, 'rgb': [0, 0, 0], 'tol': 2}, {'x': 37, 'y': 21, 'rgb': [0, 0, 0], 'tol': 2}], 'grade_note': '核导出 PNG 为 40×24 且 color_type=6（RGBA），抽样点 RGB 为 0（透明像素按 0 读），近似核取消 Show in exports 后填充未被导出。不核署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
