import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'mail_draft', 'subject': 'E31-MAIL-2-1-WT', 'body_contains': 'quarter', 'grade_note': '查主题匹配的草稿正文里是否出现 Writing Tools 修正后的拼写 quarter；种子正文只有错拼 quater，不改就不含 quarter。selftest 用 dump，不读真邮箱。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
