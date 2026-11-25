import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'mail_draft', 'subject': 'E31-MAIL-BCC-DRAFT', 'body_contains': 'This is a test message', 'grade_note': 'Drafts邮箱主题E31-MAIL-BCC-DRAFT、正文包含This is a test message的草稿'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
