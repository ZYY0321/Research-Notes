import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'psd_saved_selection', 'path': '~/Desktop/e31-newapps/out/ps-2-10-ps-save-load-selection.psd', 'require_app_signature': True, 'grade_note': '核另存 PSD 的通道数比颜色模式的底色通道多，并且写了 Alpha 通道名。这是保存选区后文件里会多出来的通道。只有三个 RGB 通道得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
