import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'path': '~/Desktop/e31-newapps/out/figma-4-component-properties.png', 'grade_note': '组件属性的定义与取值不在导出的 PNG 里，材料未核到可程序读取的途径，只能在界面上人工核验，程序评分恒为 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
