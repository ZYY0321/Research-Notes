import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'mail_draft', 'subject': 'E31-2-11-RULEHIT-K4', 'grade_note': '规则后果按邮箱成员核对：草稿箱里要有主题为 E31-2-11-RULEHIT-K4 的信。只核主题这个字典点过名的属性，草稿正文能否用脚本读回未核到，不作为通过条件。selftest 用 dump，不读真邮箱。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
