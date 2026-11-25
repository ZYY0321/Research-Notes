import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'jpeg', 'path': '~/Desktop/e31-newapps/out/ps-q60.jpg', 'width': 800, 'height': 600, 'require_app_signature': True, 'grade_note': '只核 JPEG 文件和 800×600。质量数值 60 不进通过条件。输出文件必须带 Photoshop 署名，没有则 0（reason=no_app_signature）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
