import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'jpeg', 'path': '~/Desktop/e31-newapps/out/figma-7-export-jpg-no-alpha.jpg', 'width': 32, 'height': 16, 'grade_note': '核目标路径存在 32×16 的 JPEG 文件；JPEG 格式本身不含 alpha 通道，即满足无透明度。不核软件署名（Figma 署名未核到）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
