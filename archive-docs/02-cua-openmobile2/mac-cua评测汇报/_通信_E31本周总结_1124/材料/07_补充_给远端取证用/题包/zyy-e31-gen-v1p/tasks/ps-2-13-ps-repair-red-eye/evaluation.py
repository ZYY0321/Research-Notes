import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-13-ps-repair-red-eye.png', 'width': 64, 'height': 64, 'require_app_signature': True, 'samples': [{'x': 20, 'y': 26, 'rgb': [30, 30, 34], 'tol': 45}, {'x': 44, 'y': 26, 'rgb': [30, 30, 34], 'tol': 45}], 'grade_note': '核导出 PNG 为 64×64、带 Photoshop 署名，且左右两个瞳孔采样点不再是种子图的红色而是深色。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
