import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'psd_smart_object', 'path': '~/Desktop/e31-newapps/out/ps-2-7-ps-smart-object.psd', 'require_app_signature': True, 'grade_note': '核另存 PSD 里有智能对象标记（SoLd、SoLE 或 plLd），并且版本信息是 Photoshop 写下的。普通图层得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
