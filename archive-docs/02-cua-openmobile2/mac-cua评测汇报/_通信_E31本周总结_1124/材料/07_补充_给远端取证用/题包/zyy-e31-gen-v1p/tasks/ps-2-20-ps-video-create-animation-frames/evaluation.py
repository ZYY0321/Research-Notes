import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '不可程序评分。动画帧是否创建需人工在 Photoshop 会话内核对时间轴面板，文件读取无法验证帧动画（PS 调研 2.20 该项能否程序评分未核到）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
