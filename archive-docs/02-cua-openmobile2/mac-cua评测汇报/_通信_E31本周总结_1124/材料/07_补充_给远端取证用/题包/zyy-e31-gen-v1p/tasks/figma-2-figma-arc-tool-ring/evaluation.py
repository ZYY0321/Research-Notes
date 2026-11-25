import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-figma-arc-tool-ring.png', 'width': 48, 'height': 48, 'samples': [{'x': 24, 'y': 4, 'rgb': [235, 90, 30], 'tol': 10}, {'x': 4, 'y': 24, 'rgb': [235, 90, 30], 'tol': 10}, {'x': 24, 'y': 24, 'rgb': [0, 0, 0], 'tol': 6}, {'x': 1, 'y': 1, 'rgb': [0, 0, 0], 'tol': 6}], 'grade_note': '核 48×48 RGBA PNG：圆环带上两点为 #EB5A1E，孔心与角落透明（RGB 0,0,0）。不核 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
