import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'all', 'checks': [{'kind': 'mail_draft', 'subject': 'E31-MAIL24-GROUP', 'to_contains': 'e31.alice@example.com'}, {'kind': 'mail_draft', 'subject': 'E31-MAIL24-GROUP', 'to_contains': 'e31.bob@example.com'}], 'grade_note': '草稿主题含 E31-MAIL24-GROUP，且收件人同时含两位成员地址；只填列表名未展开则判 0。selftest 用 dump，不读真邮箱。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
