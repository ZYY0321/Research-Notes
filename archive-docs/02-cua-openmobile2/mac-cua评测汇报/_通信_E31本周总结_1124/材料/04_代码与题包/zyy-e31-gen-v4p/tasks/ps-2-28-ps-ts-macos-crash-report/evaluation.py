import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '材料未写明崩溃报告落在哪个文件或如何读取，无法给出程序可核的结果点，只能人工核对是否拿到了 Photoshop 的 macOS 崩溃报告。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
