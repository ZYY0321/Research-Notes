import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'all', 'checks': [{'kind': 'prefix', 'path': '~/Desktop/e31-newapps/out/figma-7-export-svg-editable-text.svg', 'prefix': '<svg'}, {'kind': 'text', 'path': '~/Desktop/e31-newapps/out/figma-7-export-svg-editable-text.svg', 'contains': '<text'}, {'kind': 'text', 'path': '~/Desktop/e31-newapps/out/figma-7-export-svg-editable-text.svg', 'contains': 'E31 Editable'}], 'grade_note': '核指定路径存在以 <svg 开头的文件，文件里有 <text 元素且能读到 E31 Editable 这段文字（即未被转成字形轮廓）。不核软件署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
