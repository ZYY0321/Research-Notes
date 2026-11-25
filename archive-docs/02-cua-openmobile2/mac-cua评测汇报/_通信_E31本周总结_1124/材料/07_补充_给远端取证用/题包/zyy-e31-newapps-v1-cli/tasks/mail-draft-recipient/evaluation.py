import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'mail_draft', 'subject': 'E31收件人探针', 'body_contains': '请勿发送', 'to_contains': 'e31-probe@example.com', 'grade_note': '核草稿的主题、正文和收件人地址。无账户时得 0。这是 example.com 地址，题面要求不要发送。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
