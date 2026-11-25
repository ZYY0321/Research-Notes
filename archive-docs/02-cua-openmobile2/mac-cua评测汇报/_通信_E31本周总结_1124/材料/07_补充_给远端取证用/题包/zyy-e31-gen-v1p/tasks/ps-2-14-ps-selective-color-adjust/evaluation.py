import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-14-ps-selective-color-adjust.png', 'width': 48, 'height': 32, 'require_app_signature': True, 'not_flat': True, 'samples': [{'x': 4, 'y': 4, 'rgb': [30, 160, 70], 'tol': 8}, {'x': 12, 'y': 16, 'rgb': [30, 160, 70], 'tol': 8}, {'x': 20, 'y': 28, 'rgb': [30, 160, 70], 'tol': 8}, {'x': 28, 'y': 4, 'rgb': [40, 60, 200], 'tol': 8}, {'x': 36, 'y': 16, 'rgb': [40, 60, 200], 'tol': 8}, {'x': 44, 'y': 28, 'rgb': [40, 60, 200], 'tol': 8}], 'grade_note': '核 48×32 PNG：红色区域样本变为目标绿色 (30,160,70)，蓝色区域样本保持原色 (40,60,200)，并带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
