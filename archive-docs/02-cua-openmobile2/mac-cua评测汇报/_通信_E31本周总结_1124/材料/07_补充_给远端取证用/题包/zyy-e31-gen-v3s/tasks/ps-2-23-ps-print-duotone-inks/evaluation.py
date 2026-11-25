import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'psd_duotone', 'path': '~/Desktop/e31-newapps/out/ps-2-23-ps-print-duotone-inks.psd', 'require_app_signature': True, 'grade_note': '核另存 PSD 的颜色模式是双色调（文件头模式值 8）并且带双色调数据。灰度或 CMYK 得 0。版本信息还要是 Photoshop 写下的。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
