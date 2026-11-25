import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'mail_draft', 'subject': 'E31附件探针', 'attachment_contains': 'attach-note.txt', 'grade_note': '核草稿主题，以及附件名里有 attach-note.txt。无账户或 AppleScript 读不到附件时得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
