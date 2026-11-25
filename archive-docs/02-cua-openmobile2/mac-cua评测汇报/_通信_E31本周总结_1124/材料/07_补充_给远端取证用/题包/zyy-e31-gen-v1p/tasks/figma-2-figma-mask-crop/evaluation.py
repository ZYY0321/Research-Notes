import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-figma-mask-crop.png', 'width': 48, 'height': 32, 'samples': [{'x': 20, 'y': 12, 'rgb': [30, 120, 220], 'tol': 6}, {'x': 27, 'y': 19, 'rgb': [30, 120, 220], 'tol': 6}, {'x': 6, 'y': 6, 'rgb': [255, 255, 255], 'tol': 6}, {'x': 40, 'y': 24, 'rgb': [255, 255, 255], 'tol': 6}, {'x': 12, 'y': 20, 'rgb': [255, 255, 255], 'tol': 6}], 'grade_note': '核导出 PNG 为 48×32 且为 RGBA：蒙版矩形 (16,8)-(31,23) 内取样为内容色 #1E78DC；蒙版外、内容图层原本覆盖的区域取样为白色背景。不核 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
