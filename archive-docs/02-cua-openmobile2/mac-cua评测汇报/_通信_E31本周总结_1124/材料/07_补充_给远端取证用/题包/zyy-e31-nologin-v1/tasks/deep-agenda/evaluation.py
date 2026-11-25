import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"all","checks":[{"kind":"textedit_rtf","path":"~/Desktop/e31-nologin/out/deep-agenda.rtf","marker_file":"~/Desktop/e31-nologin/state/deep-agenda-mark.txt","grade_note":"富文本含 KEEP-BRIEF、15:00 和标记，原稿不被改写。","contains":["KEEP-BRIEF","15:00","{marker}"],"keep_path":"~/Desktop/e31-nologin/seed/deep-agenda.txt","keep_contains":"KEEP-BRIEF","keep_lacks":"{marker}"},{"kind":"app_state","app":"calendar","marker_file":"~/Desktop/e31-nologin/state/deep-agenda-mark.txt","where":[{"field":"SUMMARY","eq":"{marker}"},{"field":"START","prefix":"{today}T15:00"},{"field":"END","prefix":"{today}T16:00"},{"field":"ALLDAY","eq":"false"}],"grade_note":"日历里有标记为标题的 15:00 到 16:00 日程。","today_file":"~/Desktop/e31-nologin/state/today.txt"}],"grade_note":"富文本和日历日程都要出现同一个标记；简报原稿保持原样。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
