import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'all', 'checks': [{'kind': 'mail_draft', 'subject': 'E31-MAIL-2-11-HELLO', 'to_contains': 'alice.e31@example.com'}, {'kind': 'mail_draft', 'subject': 'E31-MAIL-2-11-HELLO', 'to_contains': 'bob.e31@example.com'}], 'grade_note': '评到 Mail 已接受为止：每位联系人各一封、主题一致。对方是否收到未核到，不评；正文不评。selftest 用 dump，不读真邮箱。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
