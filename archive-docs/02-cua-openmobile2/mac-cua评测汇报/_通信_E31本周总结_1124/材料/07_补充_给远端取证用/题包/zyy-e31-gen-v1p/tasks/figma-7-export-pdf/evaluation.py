import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'prefix', 'path': '~/Desktop/e31-newapps/out/figma-7-export-pdf.pdf', 'prefix': '%PDF-1.7', 'grade_note': '只核指定路径下存在文件且文件头为 %PDF-1.7，对应规格的两条评分点。不核文字提取，不核软件署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
