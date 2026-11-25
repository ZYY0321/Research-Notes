import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'psd_layer_comp', 'path': '~/Desktop/e31-newapps/out/ps-2-7-ps-layer-comps.psd', 'require_app_signature': True, 'grade_note': '核另存 PSD 的图像资源 1065（图层复合）有内容，并且版本信息是 Photoshop 写下的。没有这份资源得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
