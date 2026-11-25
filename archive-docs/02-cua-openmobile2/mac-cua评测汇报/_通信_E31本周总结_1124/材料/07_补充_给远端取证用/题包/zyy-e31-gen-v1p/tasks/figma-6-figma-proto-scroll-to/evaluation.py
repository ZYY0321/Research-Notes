import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': 'Scroll to 交互是原型行为，不进静态导出图；Figma 文件格式私有，无法程序化核验 trigger、action 和 destination 是否指向同一顶层 Frame 内部。按 manual 处理，score 恒为 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
