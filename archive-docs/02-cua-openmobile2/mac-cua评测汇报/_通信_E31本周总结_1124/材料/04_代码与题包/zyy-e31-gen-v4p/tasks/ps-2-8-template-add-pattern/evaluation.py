import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/e31-newapps/out/ps-2-8-template-add-pattern.png', 'width': 64, 'height': 64, 'require_app_signature': True, 'not_flat': True, 'grade_note': '检查导出的 PNG 包含图案填充效果（非纯色）且带 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
