import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"finder_alias","path":"~/Desktop/e31-nologin/out/find-alias","target_name":"target.txt","marker_file":"~/Desktop/e31-nologin/state/find-alias-mark.txt","grade_note":"替身文件以书签头开始，并且指向 target.txt。符号链接得 0。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
