import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-6-new-doc-preset.png', 'width': 64, 'height': 36, 'require_app_signature': True, 'samples': [{'x': 0, 'y': 0, 'rgb': [255, 255, 255], 'tol': 24}], 'grade_note': '核保存的 PNG 为 64×36（Web - Large 预设 1920×1080 的 1/30 等比缩小）、白底采样，并且带 Photoshop 署名；选错预设分类得到的其它宽高比会在高度上判负。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
