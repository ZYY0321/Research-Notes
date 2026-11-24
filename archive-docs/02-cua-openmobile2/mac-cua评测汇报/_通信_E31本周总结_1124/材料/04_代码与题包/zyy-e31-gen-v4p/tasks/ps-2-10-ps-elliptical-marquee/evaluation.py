import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '椭圆选框选区是否激活（蚂蚁线）属于应用内瞬态状态，无文件产物可核，程序评分恒为 0，需人工看屏确认。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
