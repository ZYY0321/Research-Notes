import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade

PARAMS = {'kind': 'psd', 'path': '~/Desktop/e31-newapps/out/ps-merged.psd', 'layer_count_in': [0, 1], 'require_app_signature': True, 'grade_note': '读 PSD 图层个数，0 或 1 算通过（合并后一层，或压成没有图层记录的背景）。这是按文件头偏移的草稿解析，真文件若版本不是 8BPS v1 会得 0。输出文件必须带 Photoshop 署名，没有则 0（reason=no_app_signature）。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade.grade(PARAMS)
