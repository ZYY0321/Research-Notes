import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'reason': '签名与引用原文在回复草稿正文中的相对位置，材料没有给出脚本读法，只能界面核对', 'grade_note': '不可评分题，score 永远 0'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
