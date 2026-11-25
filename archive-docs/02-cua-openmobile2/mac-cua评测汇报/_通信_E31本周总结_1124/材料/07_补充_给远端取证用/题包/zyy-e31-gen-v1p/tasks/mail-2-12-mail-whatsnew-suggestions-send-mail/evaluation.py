import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'mail_draft', 'subject': 'E31-M212 Suggestions Send', 'body_contains': 'E31-M212-SENT-BODY', 'to_contains': 'e31-m212@example.com', 'grade_note': 'Sent 结果：主题、收件人、正文三项都要对上；收件人为空等于只存草稿，不给分。selftest 用 dump，不读真邮箱。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
