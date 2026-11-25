import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '新动作（名称 E31 Rotate Action、动作集 E31 Set、功能键 Shift+Command+F3、按钮颜色红色）只存在于 Actions 面板里，是否随 PSD 保存官方页未写，程序读不到，只能人工界面核查，score 恒为 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
