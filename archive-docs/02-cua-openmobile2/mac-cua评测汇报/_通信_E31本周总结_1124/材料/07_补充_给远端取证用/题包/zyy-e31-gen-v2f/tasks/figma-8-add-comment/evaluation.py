import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'grade_note': '不可程序评分。评论对象存在于 Figma 云端文件内，评分点是云端界面中可见一条新增评论且文字与题面一致，只能人工核查，manual 永远给 0。留档 txt 仅供人工比对，不作为通过条件。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
