import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-figma-frame-nesting.png', 'width': 48, 'height': 32, 'samples': [{'x': 2, 'y': 2, 'rgb': [30, 60, 200], 'tol': 8}, {'x': 34, 'y': 16, 'rgb': [240, 180, 20], 'tol': 8}], 'grade_note': '核导出 PNG 为 48×32 的 RGBA；父 Frame 背景采样点 (2,2) 为 RGB(30,60,200)，子 Frame 区域采样点 (34,16) 为 RGB(240,180,20)。不核 Figma 署名（未核到）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
