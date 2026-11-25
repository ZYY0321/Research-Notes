import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"photos","marker_file":"~/Desktop/e31-nologin/state/photos-import-mark.txt","where":[{"field":"KIND","eq":"item"},{"field":"FILENAME","eq":"{photo}"}],"grade_note":"图库里有一张图，文件名等于状态文件里记下的名字。只把 PNG 留在桌面得 0。","photo_file":"~/Desktop/e31-nologin/state/photos-import-photo.txt"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
