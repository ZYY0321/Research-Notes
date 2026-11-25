import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'account_description', 'text': 'E31 Research Mail', 'paths': ['~/Library/Accounts/Accounts4.sqlite', '~/Library/Accounts/Accounts3.sqlite', '~/Library/Mail/V11/MailData/Accounts.plist', '~/Library/Mail/V10/MailData/Accounts.plist', '~/Library/Mail/V9/MailData/Accounts.plist'], 'grade_note': '核账号描述原文等于 E31 Research Mail。读的是 Accounts sqlite 里带 DESCRIPTION 或 ACCOUNTNAME 的列，或 Accounts.plist 里的完整字符串；同一行若有 bundle 标识，必须含 mail。描述不对、写在别的列里、或只是一份含这句话的文本，得 0。不读邮件库。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
