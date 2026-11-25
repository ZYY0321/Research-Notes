import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '不可程序评分。slot 的逐步操作未核到，组件与实例的插槽替换关系不在导出图里，API 也未核到，只能人工看文件里组件是否含 slot、实例是否完成了插槽内容替换。score 恒为 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
