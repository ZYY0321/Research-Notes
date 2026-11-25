import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '同一页面多条 flow、各自起始 Frame、同一 Frame 属多条 flow 仍只有一个 starting point，这些都在 Figma 文档内部，静态导出不含原型连接，无法程序化核验，score 恒为 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
