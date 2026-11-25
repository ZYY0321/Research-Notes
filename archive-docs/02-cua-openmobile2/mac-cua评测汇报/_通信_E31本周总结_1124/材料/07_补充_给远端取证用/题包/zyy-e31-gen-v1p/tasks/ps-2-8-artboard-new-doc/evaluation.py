import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-8-artboard-new-doc.png', 'width': 1080, 'height': 1080, 'require_app_signature': True, 'grade_note': '检查导出的 PNG 尺寸为 1080×1080 像素，并且由 Photoshop 生成。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
