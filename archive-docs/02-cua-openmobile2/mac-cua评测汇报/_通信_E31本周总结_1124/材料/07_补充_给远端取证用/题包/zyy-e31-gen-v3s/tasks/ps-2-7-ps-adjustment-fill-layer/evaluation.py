import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'psd_adjustment', 'path': '~/Desktop/e31-newapps/out/ps-2-7-ps-adjustment-fill-layer.psd', 'require_app_signature': True, 'grade_note': '核另存 PSD 里至少有一个调整图层或填充图层标记（亮度/对比度、曲线、色阶、色彩平衡、纯色、渐变、图案等），并且版本信息是 Photoshop 写下的。只多了一个普通图层、或文件不是 Photoshop 存的，得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
