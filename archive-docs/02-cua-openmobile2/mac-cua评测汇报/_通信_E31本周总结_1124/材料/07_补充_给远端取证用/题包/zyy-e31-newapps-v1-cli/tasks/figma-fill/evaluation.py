import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'png', 'path': '~/Desktop/e31-newapps/out/figma-fill.png', 'width': 400, 'height': 300, 'samples': [{'x': 200, 'y': 150, 'rgb': [227, 26, 26], 'tol': 24}, {'x': 2, 'y': 2, 'rgb': [227, 26, 26], 'tol': 24}], 'grade_note': '核 400×300，中心和靠近左上的像素都接近 #E31A1A。导出带白边或缩放不对会得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
