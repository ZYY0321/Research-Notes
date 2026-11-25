import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'path': '~/Desktop/e31-newapps/out/ps-2-12-ps-blend-auto-blend-layers.png', 'grade_note': '规格标注 program_gradeable=false：Auto-Blend Layers 的合成像素不可预先确定，无法程序判定保存文件是否来自该操作。按 manual 处理，score 恒为 0，留待人工核查文件存在且与任一单张输入照片不完全相同。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
