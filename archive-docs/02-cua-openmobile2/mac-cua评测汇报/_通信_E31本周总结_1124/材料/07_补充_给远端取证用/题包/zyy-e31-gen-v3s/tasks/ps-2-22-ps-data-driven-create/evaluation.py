import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'psd_resource_text', 'path': '~/Desktop/e31-newapps/out/ps-2-22-ps-data-driven-create.psd', 'resource_id': 7000, 'token': 'variables', 'require_app_signature': True, 'grade_note': '核另存 PSD 的图像资源 7000 里有变量定义（文本中含 variables），并且版本信息是 Photoshop 写下的。只有数据集、没有变量定义，得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
