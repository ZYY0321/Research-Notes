import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-figma-pencil-sketch.png', 'width': 48, 'height': 32, 'samples': [{'x': 8, 'y': 16, 'rgb': [208, 2, 27], 'tol': 60}, {'x': 24, 'y': 16, 'rgb': [208, 2, 27], 'tol': 60}, {'x': 40, 'y': 16, 'rgb': [208, 2, 27], 'tol': 60}, {'x': 2, 'y': 2, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 45, 'y': 2, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 2, 'y': 29, 'rgb': [255, 255, 255], 'tol': 10}, {'x': 45, 'y': 29, 'rgb': [255, 255, 255], 'tol': 10}], 'grade_note': '核导出 PNG 为 48×32 RGBA；中线三处采样为笔迹色 #D0021B，四角采样为白色背景。不核 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
