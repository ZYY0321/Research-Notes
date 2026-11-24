import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'manual', 'path': '~/e31-newapps/out/ps-2-19-ps-show-rulers.png', 'grade_note': '不可程序评分：标尺显示是界面状态，不写进文件。人工看截图里图像窗口上方与左侧是否可见标尺，以及 View 菜单中 Rulers 是否勾选。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
