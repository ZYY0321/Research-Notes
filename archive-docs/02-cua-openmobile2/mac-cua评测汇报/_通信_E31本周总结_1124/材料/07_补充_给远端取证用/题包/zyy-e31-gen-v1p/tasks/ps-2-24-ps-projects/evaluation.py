import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'reason': 'Projects 的云端状态在本地没有可核验产物，专页读法未核到，无法程序评分', 'grade_note': '不可程序评分：云端状态只在 Adobe 账户侧，固定 0 分，人工复核。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
