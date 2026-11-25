import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'sample_text', 'path': '~/Desktop/e31-newapps/out/ps-2-28-ps-ts-sample-spindump.txt', 'grade_note': '核保存的文本像一份 sample 或 spindump：要有 Call graph 和 Binary Images 这两节，并且至少三行带 (in ...) 的栈。sample 还要有 Sampling process 一行；spindump 还要有 Spindump 和 Process。只有一段说明、没有这些结构，得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
