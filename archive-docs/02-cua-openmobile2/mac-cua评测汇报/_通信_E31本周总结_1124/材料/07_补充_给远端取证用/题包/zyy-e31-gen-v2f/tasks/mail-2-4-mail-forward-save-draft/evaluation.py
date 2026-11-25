import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'mail_draft', 'subject': 'Fwd: E31-MAIL-2-4 status report', 'to_contains': 'e31.forward.target@example.com', 'grade_note': 'Drafts 新增草稿，主题为转发主题且含 E31-MAIL-2-4，收件人含指定地址。selftest 用 dump，不读真邮箱。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
