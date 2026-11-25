import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'all', 'checks': [{'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-7-multiple-export-settings.png'}, {'kind': 'jpeg', 'path': '~/Desktop/e31-newapps/out/figma-7-multiple-export-settings.jpg'}]}

class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
