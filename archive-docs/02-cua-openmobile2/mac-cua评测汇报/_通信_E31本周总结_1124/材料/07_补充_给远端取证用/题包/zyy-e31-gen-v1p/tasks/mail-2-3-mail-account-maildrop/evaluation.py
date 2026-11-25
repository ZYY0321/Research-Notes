import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '人工或截图核对：指定账号的 Account Information 面板中 Send large attachments with Mail Drop 处于勾选状态。账号属性的脚本名未核到，无法程序评分。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
