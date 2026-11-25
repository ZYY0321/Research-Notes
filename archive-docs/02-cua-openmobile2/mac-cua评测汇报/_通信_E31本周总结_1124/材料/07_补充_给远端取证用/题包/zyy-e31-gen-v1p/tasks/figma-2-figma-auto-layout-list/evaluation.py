import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-figma-auto-layout-list.png', 'width': 32, 'height': 40, 'samples': [{'x': 16, 'y': 2, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 16, 'y': 3, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 16, 'y': 4, 'rgb': [230, 60, 40], 'tol': 10}, {'x': 16, 'y': 8, 'rgb': [230, 60, 40], 'tol': 10}, {'x': 16, 'y': 11, 'rgb': [230, 60, 40], 'tol': 10}, {'x': 16, 'y': 12, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 16, 'y': 15, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 16, 'y': 16, 'rgb': [230, 60, 40], 'tol': 10}, {'x': 16, 'y': 20, 'rgb': [230, 60, 40], 'tol': 10}, {'x': 16, 'y': 23, 'rgb': [230, 60, 40], 'tol': 10}, {'x': 16, 'y': 24, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 16, 'y': 27, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 16, 'y': 28, 'rgb': [230, 60, 40], 'tol': 10}, {'x': 16, 'y': 32, 'rgb': [230, 60, 40], 'tol': 10}, {'x': 16, 'y': 35, 'rgb': [230, 60, 40], 'tol': 10}, {'x': 16, 'y': 36, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 16, 'y': 38, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 2, 'y': 20, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 3, 'y': 20, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 4, 'y': 20, 'rgb': [230, 60, 40], 'tol': 10}, {'x': 27, 'y': 20, 'rgb': [230, 60, 40], 'tol': 10}, {'x': 28, 'y': 20, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 30, 'y': 20, 'rgb': [255, 255, 255], 'tol': 10}], 'grade_note': '核导出 PNG 为 32×40 的 RGBA，按像素抽样核对三个子项沿垂直方向排列、四边 Padding 为 4、子项间 Gap 为 4。不核 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
