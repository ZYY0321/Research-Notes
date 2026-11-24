import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '材料未写明采集结果落在哪个文件或如何读取，无法给出程序可核的结果点，只能人工核对是否产出了 Sample Process 或 Spindump。manual 题，score 恒为 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
