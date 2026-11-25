import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'reason': '把图层转为组件这一操作的结果（组件身份）不出现在导出的 PNG 里，只能在 Figma 界面上人工核验；程序无法区分转了组件再导出和没转组件直接导出。', 'grade_note': '人工核验题。score 永远 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
