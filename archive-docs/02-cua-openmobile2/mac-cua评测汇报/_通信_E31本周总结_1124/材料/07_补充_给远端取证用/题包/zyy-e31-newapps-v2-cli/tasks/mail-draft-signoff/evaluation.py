import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'mail_draft', 'subject': 'E31落款探针', 'body_contains': '— E31', 'grade_note': '核草稿主题和正文里的落款。无账户时得 0。同主题旧草稿会直接得 1。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
