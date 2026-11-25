import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-adjust.png', 'width': 800, 'height': 600, 'keep': {'path': '~/Desktop/e31-newapps/seed/poster.png', 'width': 800, 'height': 600}, 'differ_from': {'path': '~/Desktop/e31-newapps/seed/poster.png', 'min_mean_abs': 12}, 'require_app_signature': True, 'grade_note': '核 800×600，且相对种子图的像素平均绝对差至少 12。不逐项核色阶和亮度的具体数值。色彩管理造成的轻微变色可能不够 12，也可能让没做调整的另存被误判。输出文件必须带 Photoshop 署名，没有则 0（reason=no_app_signature）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
