import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'text', 'path': '~/Desktop/e31-newapps/out/feishu-roundtrip.txt', 'contains': ['E31-ATTACH'], 'grade_note': '只核下载路径里有 E31-ATTACH。不区分文件是云端往返还是本地复制。未登录时没有这个文件，得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
