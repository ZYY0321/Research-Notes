import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'pdf_annot', 'path': '~/Desktop/e31-newapps/out/mail-2-5-mail-pdf-handwritten-sign.pdf', 'grade_note': '核保存下来的 PDF 里有手写或图章类注释（Subtype 为 Ink 或 Stamp）。链接注释、高亮注释，或一份没有注释的 PDF，得 0。不打开邮件库。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
