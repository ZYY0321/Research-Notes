import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'psd_artboard', 'path': '~/Desktop/e31-newapps/out/ps-2-8-artboard-add-to-doc.psd', 'require_app_signature': True, 'grade_note': '核另存 PSD 里至少有一个画板标记（artb、artd 或 abdd），并且版本信息是 Photoshop 写下的。只有普通图层得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
