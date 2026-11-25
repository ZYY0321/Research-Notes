import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'text', 'path': '~/Desktop/e31-newapps/out/feishu-minutes.md', 'contains': ['E31会议纪要', '参会人：探针'], 'grade_note': '只核本地 md 里有标题和正文那一句。飞书若不能导出到这个路径，登录后也会得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
