import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'reason': '评分点是导出 PNG 与原始照片在构图上的可见差异，需人工对照原图核对；新功能页没写结果怎样落进文件，未核到可程序评分的读法。', 'grade_note': '不可程序评分，score 恒为 0，构图差异由人工对照原图核对。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
