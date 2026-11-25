import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-mask.png', 'width': 48, 'height': 48, 'samples': [{'x': 6, 'y': 6, 'rgb': [45, 120, 220], 'tol': 24}, {'x': 18, 'y': 18, 'rgb': [45, 120, 220], 'tol': 24}, {'x': 36, 'y': 12, 'rgb': [255, 255, 255], 'tol': 24}, {'x': 12, 'y': 36, 'rgb': [255, 255, 255], 'tol': 24}, {'x': 40, 'y': 40, 'rgb': [255, 255, 255], 'tol': 24}], 'grade_note': '核导出 PNG 为 48×48 RGBA；左上 24×24 遮罩区内为 #2D78DC，区外为白底。不核 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
