import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': 'Mailbox > Rebuild 是维护操作，既不新增也不删除邮箱或邮件，材料里没有写出程序可读的结果落点，只能核对邮箱仍存在，区分不了有没有做。不可评分，score 恒为 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
