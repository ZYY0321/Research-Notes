import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-auto-layout.png', 'width': 24, 'height': 56, 'samples': [{'x': 12, 'y': 12, 'rgb': [255, 0, 0], 'tol': 2}, {'x': 12, 'y': 28, 'rgb': [0, 255, 0], 'tol': 2}, {'x': 12, 'y': 44, 'rgb': [0, 0, 255], 'tol': 2}, {'x': 12, 'y': 20, 'rgb': [255, 255, 255], 'tol': 2}, {'x': 12, 'y': 36, 'rgb': [255, 255, 255], 'tol': 2}, {'x': 12, 'y': 3, 'rgb': [255, 255, 255], 'tol': 2}, {'x': 12, 'y': 53, 'rgb': [255, 255, 255], 'tol': 2}, {'x': 3, 'y': 28, 'rgb': [255, 255, 255], 'tol': 2}, {'x': 21, 'y': 28, 'rgb': [255, 255, 255], 'tol': 2}]}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
