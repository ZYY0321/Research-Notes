import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'prefix', 'path': '~/e31-newapps/out/ps-2-25-ps-save-as-format.tif', 'prefix': 'II*', 'grade_note': '核目标路径存在另存出来的 TIFF 文件：文件头为 II 小端字节序的 TIFF 签名，能和直接改名的 PSD、导出的 PNG、以及 MM 字节序区分开。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
