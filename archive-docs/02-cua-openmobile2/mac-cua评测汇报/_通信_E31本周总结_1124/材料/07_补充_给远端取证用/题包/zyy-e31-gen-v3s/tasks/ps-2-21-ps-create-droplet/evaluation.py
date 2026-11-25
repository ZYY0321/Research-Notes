import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'droplet_app', 'path': '~/Desktop/e31-newapps/out/ps-2-21-ps-create-droplet.app', 'grade_note': '核快捷批处理产物是一个 Mac 应用程序包：Contents/Info.plist 的类型是 APPL，包内有可执行文件，并且署名是 8BIM 或文字里有 Photoshop。普通文件夹、别的应用程序，得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
