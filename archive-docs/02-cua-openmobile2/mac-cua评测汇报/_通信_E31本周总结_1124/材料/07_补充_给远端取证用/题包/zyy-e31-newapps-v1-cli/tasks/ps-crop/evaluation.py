import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-crop.png', 'width': 320, 'height': 200, 'keep': {'path': '~/Desktop/e31-newapps/seed/poster.png', 'width': 800, 'height': 600}, 'require_app_signature': True, 'grade_note': '只核导出 PNG 为 320×200，且种子图仍在。不核裁切起点是不是左上角。输出文件必须带 Photoshop 署名，没有则 0（reason=no_app_signature）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
