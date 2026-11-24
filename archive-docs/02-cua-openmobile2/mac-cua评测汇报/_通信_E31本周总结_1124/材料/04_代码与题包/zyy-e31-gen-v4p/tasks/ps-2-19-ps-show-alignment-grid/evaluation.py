import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '不可程序评分。对齐网格只显示在界面上、不打印；材料未核到它是否写进 PSD，没有可靠的文件读法。由人工看截图中图像上是否出现覆盖整个画面的网格。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
