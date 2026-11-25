import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'psd_drop_shadow', 'path': '~/Desktop/e31-newapps/out/ps-2-7-ps-layer-effects.psd', 'require_app_signature': True, 'grade_note': '核另存 PSD 的图层效果里有投影。外发光、内阴影不算。文件还要带 Photoshop 的版本信息。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
