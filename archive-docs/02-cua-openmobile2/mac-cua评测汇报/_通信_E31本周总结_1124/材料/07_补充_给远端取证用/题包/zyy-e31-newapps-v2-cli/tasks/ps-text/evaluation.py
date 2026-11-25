import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'all', 'checks': [{'kind': 'psd', 'path': '~/Desktop/e31-newapps/out/ps-text.psd', 'contains_file': '~/Desktop/e31-newapps/state/ps-text-mark.txt', 'require_app_signature': True}, {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-text.png', 'width': 800, 'height': 600, 'keep': {'path': '~/Desktop/e31-newapps/seed/poster.png', 'width': 800, 'height': 600}, 'require_app_signature': True}], 'grade_note': '文字核 PSD 字节里有标记文件第一行；PNG 只核 800×600。压缩后的文字引擎数据可能让字节搜索失败。输出文件必须带 Photoshop 署名，没有则 0（reason=no_app_signature）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
