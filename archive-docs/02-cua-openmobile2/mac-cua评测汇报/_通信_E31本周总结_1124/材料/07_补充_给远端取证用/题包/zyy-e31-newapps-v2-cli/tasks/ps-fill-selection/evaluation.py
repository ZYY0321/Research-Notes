import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-fill.png', 'width': 800, 'height': 600, 'keep': {'path': '~/Desktop/e31-newapps/seed/poster.png', 'width': 800, 'height': 600}, 'samples': [{'x': 150, 'y': 150, 'rgb': [255, 0, 0], 'tol': 20}, {'x': 10, 'y': 10, 'rgb': [51, 102, 153], 'tol': 12}], 'require_app_signature': True, 'grade_note': '抽样 (150,150) 接近纯红、(10,10) 仍接近种子色 #336699。选区略有偏移会得 0。输出文件必须带 Photoshop 署名，没有则 0（reason=no_app_signature）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
