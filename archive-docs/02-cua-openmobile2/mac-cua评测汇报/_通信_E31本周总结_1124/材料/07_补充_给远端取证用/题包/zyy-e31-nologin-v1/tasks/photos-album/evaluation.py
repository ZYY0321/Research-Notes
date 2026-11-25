import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"app_state","app":"photos","marker_file":"~/Desktop/e31-nologin/state/photos-album-mark.txt","where":[{"field":"KIND","eq":"album"},{"field":"NAME","eq":"{marker}"}],"grade_note":"照片图库里有一个相簿，名字等于标记。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
