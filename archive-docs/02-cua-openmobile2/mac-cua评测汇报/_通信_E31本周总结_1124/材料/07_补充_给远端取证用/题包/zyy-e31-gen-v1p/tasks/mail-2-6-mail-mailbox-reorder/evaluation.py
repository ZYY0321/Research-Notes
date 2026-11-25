import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'reason': '拖动排序只改变边栏呈现顺序；只能核对邮箱存在，排序结果没有程序可读的落点，无法自动评分', 'grade_note': '不可评分题，score 永远 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
