import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '不可程序化评分：魔棒选区只存在于 Photoshop 的运行时状态，脚本读不到是否有激活选区，score 恒为 0，需人工看屏确认蚂蚁线。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
