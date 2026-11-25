import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'plist_flag', 'key': 'SignaturePlacedAboveQuotedText', 'expect': False, 'paths': ['~/Library/Preferences/com.apple.mail.plist', '~/Library/Containers/com.apple.mail/Data/Library/Preferences/com.apple.mail.plist'], 'grade_note': '核 Mail 偏好里 SignaturePlacedAboveQuotedText 为假，也就是「Place signature above quoted text」没有勾上。键不存在、或值仍为真，得 0。只读调用方给出的 plist 路径，不读邮箱。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
