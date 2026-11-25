import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'text', 'path': '~/Desktop/e31-newapps/out/mail-2-6-mail-mailbox-create-sub.txt', 'contains': 'MBOX=E31P26/E31S26', 'grade_note': 'dump 脚本写出的邮箱清单里必须有 MBOX=E31P26/E31S26 这一行，代表子邮箱存在且位于父邮箱 E31P26 之下。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
