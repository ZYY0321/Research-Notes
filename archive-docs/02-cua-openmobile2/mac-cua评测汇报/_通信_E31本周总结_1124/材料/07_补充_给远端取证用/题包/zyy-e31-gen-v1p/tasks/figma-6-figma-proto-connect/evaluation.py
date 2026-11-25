import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '原型连接存在于 Figma 云端文档内部，不产生可核查的本地成品文件；此题不可程序评分，score 恒为 0。两个顶层 Frame 之间的连接（hotspot、连接线、destination 为顶层 Frame）只能人工确认。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
