import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/assets/icons/figma-7-export-slash-nested-folder.png', 'width': 32, 'height': 16, 'samples': [{'x': 0, 'y': 0, 'rgb': [16, 120, 200], 'tol': 6}], 'grade_note': '核嵌套目录 assets/icons/ 下的导出 PNG 为 32×16、RGBA、左上角颜色 #1078C8。不核 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
