import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '材料未给出账号关联状态的文件落点，只能人工核对 Content Credentials 界面中的社交账号关联状态，程序评分恒为 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
