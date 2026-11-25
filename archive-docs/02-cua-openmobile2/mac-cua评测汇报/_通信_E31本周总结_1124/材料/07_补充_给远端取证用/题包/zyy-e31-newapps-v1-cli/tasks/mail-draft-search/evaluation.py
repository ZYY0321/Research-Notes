import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'mail_draft', 'subject': 'E31搜索探针', 'body_contains': 'E31-SEARCH-TOKEN', 'grade_note': '终态只核这封草稿在不在，不核搜索框。无账户时得 0。同主题旧草稿会直接得 1。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
