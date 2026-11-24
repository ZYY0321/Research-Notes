import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '人工核查：已对该文档执行硬打样输出。材料写明打印结果不落在图像文件里，本题没有可供程序读取的文件级结果，程序评分固定 0 分。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
