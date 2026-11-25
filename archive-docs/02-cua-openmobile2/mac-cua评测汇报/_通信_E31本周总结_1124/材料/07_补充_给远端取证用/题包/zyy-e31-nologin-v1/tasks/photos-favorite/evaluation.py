import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"photos","marker_file":"~/Desktop/e31-nologin/state/photos-favorite-mark.txt","where":[{"field":"KIND","eq":"item"},{"field":"FILENAME","eq":"{photo}"},{"field":"FAVORITE","eq":"true"}],"grade_note":"导入的那张图文件名匹配，且喜欢为真。","photo_file":"~/Desktop/e31-nologin/state/photos-favorite-photo.txt"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
