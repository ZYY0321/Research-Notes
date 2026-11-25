import os, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseEvaluation
import e31_grade_ext

PARAMS = {'kind': 'psd_frame_animation', 'path': '~/Desktop/e31-newapps/out/ps-2-20-ps-video-create-animation-frames.psd', 'require_app_signature': True, 'grade_note': '核另存 PSD 的图层元数据里有帧动画列表 mlst，并且版本信息是 Photoshop 写下的。只有别的元数据、没有 mlst，得 0。'}


class Evaluation(BaseEvaluation):
    def run(self, context):
        return e31_grade_ext.grade(PARAMS)
