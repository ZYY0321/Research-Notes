import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-canvas.png', 'width': 640, 'height': 480, 'keep': {'path': '~/Desktop/e31-newapps/seed/poster.png', 'width': 800, 'height': 600}, 'require_app_signature': True, 'grade_note': '只核导出 PNG 为 640×480，且种子图仍是 800×600。不核重采样内容。输出文件必须带 Photoshop 署名，没有则 0（reason=no_app_signature）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
