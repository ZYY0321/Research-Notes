import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/ps-2-15-ps-brushes-presets.png', 'width': 64, 'height': 64, 'require_app_signature': True, 'not_flat': True, 'samples': [{'x': 16, 'y': 32, 'rgb': [0, 0, 0], 'tol': 60}, {'x': 32, 'y': 32, 'rgb': [0, 0, 0], 'tol': 60}, {'x': 48, 'y': 32, 'rgb': [0, 0, 0], 'tol': 60}, {'x': 32, 'y': 6, 'rgb': [255, 255, 255], 'tol': 24}, {'x': 32, 'y': 57, 'rgb': [255, 255, 255], 'tol': 24}], 'grade_note': '核导出 PNG 为 64×64、带 Photoshop 署名、画面非单色；水平中线上三处取样为黑（笔触覆盖），上下边缘取样为白（未被笔触覆盖），以区分画笔笔触与整幅填充。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
