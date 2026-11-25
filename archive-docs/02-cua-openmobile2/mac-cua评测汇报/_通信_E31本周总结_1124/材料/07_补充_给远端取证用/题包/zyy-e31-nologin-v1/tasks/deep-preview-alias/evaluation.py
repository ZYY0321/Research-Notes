import json, os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import nologin_grade

PARAMS = json.loads('{"kind":"all","checks":[{"kind":"preview_pdf","path":"~/Desktop/e31-nologin/out/deep-preview-alias.pdf","mode":"freetext","marker_file":"~/Desktop/e31-nologin/state/deep-preview-alias-mark.txt","seed_token_file":"~/Desktop/e31-nologin/state/deep-preview-alias-seed.txt","keep_path":"~/Desktop/e31-nologin/seed/deep-preview-alias.pdf","keep_contains":"{seed}","keep_lacks":"{marker}","grade_note":"副本上有标记的自由文本批注。"},{"kind":"finder_alias","path":"~/Desktop/e31-nologin/out/deep-preview-alias-link","target_name":"deep-preview-alias.pdf","marker_file":"~/Desktop/e31-nologin/state/deep-preview-alias-mark.txt","grade_note":"替身指向另存的 PDF。"}],"grade_note":"PDF 副本带标记批注，替身指向这个副本的文件名。符号链接得 0。"}')


class Evaluation(BaseEvaluation):
    def run(self, context):
        return nologin_grade.grade(PARAMS)
