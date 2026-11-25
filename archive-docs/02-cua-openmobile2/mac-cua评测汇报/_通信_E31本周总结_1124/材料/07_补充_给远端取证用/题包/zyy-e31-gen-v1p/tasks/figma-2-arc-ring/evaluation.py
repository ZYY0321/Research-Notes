import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png_rgba', 'path': '~/Desktop/e31-newapps/out/figma-2-arc-ring.png', 'width': 64, 'height': 64, 'not_flat': True, 'grade_note': '核导出 PNG 为 64×64、RGBA（带 alpha 通道），且图像非平色（存在环形图形像素，排除整幅纯色填充）。不核 Photoshop 署名。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
