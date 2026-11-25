import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'psd', 'path': '~/Desktop/e31-newapps/out/ps-layer.psd', 'contains_file': '~/Desktop/e31-newapps/state/ps-layer-mark.txt', 'require_app_signature': True, 'grade_note': '核 PSD 里有标记文件第一行（UTF-8 或 UTF-16）。图层名若被压缩存放会误判 0。不数图层张数。输出文件必须带 Photoshop 署名，没有则 0（reason=no_app_signature）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
