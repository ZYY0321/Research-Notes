import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/figma-new.png', 'min_width': 32, 'min_height': 32, 'grade_note': '只核导出的 PNG 能解码，且宽高都不小于 32。不核文件内容。登录墙时没有这张图，得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
