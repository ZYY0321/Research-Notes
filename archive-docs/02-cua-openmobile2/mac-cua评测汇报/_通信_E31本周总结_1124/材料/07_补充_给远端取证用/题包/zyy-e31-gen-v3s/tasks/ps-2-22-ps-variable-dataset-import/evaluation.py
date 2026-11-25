import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'psd_resource_text', 'path': '~/Desktop/e31-newapps/out/ps-2-22-ps-variable-dataset-import.psd', 'resource_id': 7001, 'token': 'dataset', 'require_app_signature': True, 'grade_note': '核另存 PSD 的图像资源 7001 里有数据集（文本中含 dataset），并且版本信息是 Photoshop 写下的。只定义了变量、没有数据集，得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
