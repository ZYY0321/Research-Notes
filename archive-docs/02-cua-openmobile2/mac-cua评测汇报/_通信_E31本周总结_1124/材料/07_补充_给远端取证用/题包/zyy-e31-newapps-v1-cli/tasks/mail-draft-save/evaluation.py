import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'mail_draft', 'subject': 'E31草稿探针', 'body_contains': 'E31-DRAFT-BODY', 'grade_note': '用 AppleScript 在各账户的 Drafts/草稿/草稿箱里找主题和正文。没有账户、草稿箱名字对不上、或同主题旧草稿还在，结果都不可靠。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
