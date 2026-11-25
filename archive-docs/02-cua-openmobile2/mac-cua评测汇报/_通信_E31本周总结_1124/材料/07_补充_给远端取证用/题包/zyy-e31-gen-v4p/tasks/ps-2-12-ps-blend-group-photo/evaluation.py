import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'reason': '规格标注 program_gradeable=false：「多人合影」条目所指的功能未核到，是否用该功能把多张合影合成为一张需要人工核验，脚本无法区分。', 'grade_note': '不可程序评分，score 恒为 0，需人工核验成品是否由 Photoshop 的「多人合影」功能合成。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
