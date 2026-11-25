import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'mail_draft', 'subject': 'Signature Test', 'body_contains': 'SignatureA-Content', 'grade_note': '草稿存在且正文包含被设置为默认的签名A内容'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
