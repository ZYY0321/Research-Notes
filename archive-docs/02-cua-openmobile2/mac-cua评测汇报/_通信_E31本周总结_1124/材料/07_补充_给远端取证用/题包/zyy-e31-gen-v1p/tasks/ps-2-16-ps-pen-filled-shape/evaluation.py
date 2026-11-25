import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-16-ps-pen-filled-shape.png', 'width': 48, 'height': 48, 'require_app_signature': True, 'samples': [{'x': 24, 'y': 24, 'rgb': [190, 30, 60], 'tol': 24}, {'x': 3, 'y': 3, 'rgb': [220, 220, 220], 'tol': 16}, {'x': 44, 'y': 3, 'rgb': [220, 220, 220], 'tol': 16}, {'x': 3, 'y': 44, 'rgb': [220, 220, 220], 'tol': 16}, {'x': 44, 'y': 44, 'rgb': [220, 220, 220], 'tol': 16}], 'grade_note': '核导出 48×48 PNG：画布中心是填充色 RGB(190,30,60) 的闭合形状合成像素，四角仍是底图原色 RGB(220,220,220)，并带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
