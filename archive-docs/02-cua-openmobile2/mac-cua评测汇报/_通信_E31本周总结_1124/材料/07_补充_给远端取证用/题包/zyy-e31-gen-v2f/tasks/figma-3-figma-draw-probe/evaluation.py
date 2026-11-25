import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '不可程序评分，score 恒为 0。人工核对：1) Figma 桌面应用已打开并进入一个设计文件；2) 界面上可见与 Figma Draw 对应的功能入口或其界面已被打开（具体形态材料未核到，以人工观察为准）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
