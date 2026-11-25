import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-combine-boolean.png', 'width': 48, 'height': 32, 'samples': [{'x': 8, 'y': 8, 'rgb': [220, 30, 30], 'tol': 12}, {'x': 36, 'y': 20, 'rgb': [220, 30, 30], 'tol': 12}, {'x': 24, 'y': 14, 'rgb': [220, 30, 30], 'tol': 12}, {'x': 40, 'y': 6, 'rgb': [235, 235, 235], 'tol': 12}, {'x': 6, 'y': 26, 'rgb': [235, 235, 235], 'tol': 12}], 'grade_note': '核 48×32 的 RGBA PNG：矩形 A 独有区 (8,8)、矩形 B 独有区 (36,20)、重叠区 (24,14) 都是红色，形状外 (40,6)、(6,26) 是底色。只画单个矩形时 B 独有区取不到红色，判 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
