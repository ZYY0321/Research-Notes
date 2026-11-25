import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-8-artboard-properties.png', 'width': 800, 'height': 600, 'require_app_signature': True, 'grade_note': '核导出的 PNG 是 800×600，并且带 Photoshop 署名。尺寸不对，或文件不是 Photoshop 写的，得 0。这一项只看导出图的宽高，不从 PSD 里读画板矩形。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
