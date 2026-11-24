import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '不可程序评分。评的是界面状态：图像上浮着一条水平参考线，且位置在说明文件指定处附近，只能人工看截图。参考线是否写入 PSD 材料未核到，不能靠读文件来判。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
