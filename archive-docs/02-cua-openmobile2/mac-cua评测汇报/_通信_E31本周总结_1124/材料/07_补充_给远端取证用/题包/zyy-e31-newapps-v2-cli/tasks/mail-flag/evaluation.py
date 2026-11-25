import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'mail_flag', 'skip_path': '~/Desktop/e31-newapps/out/mail-flag-skip.txt', 'baseline_path': '~/Desktop/e31-newapps/state/mail-flag-before.txt', 'grade_note': '初始化会先数收件箱封数和已旗标封数。空收件箱只认跳过文件；有信则要求旗标数变多。基线脚本失败时得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
