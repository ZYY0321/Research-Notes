import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        brief_dir = os.path.expanduser('~/Desktop/e31-newapps/brief')
        brief_path = os.path.join(brief_dir, 'figma-8-create-branch.txt')
        if os.path.lexists(brief_path):
            os.remove(brief_path)
        os.makedirs(brief_dir, exist_ok=True)
        with open(brief_path, 'w', encoding='utf-8') as f:
            f.write('设计文件：产品界面草图\n')
            f.write('分支名称：feature-redesign\n')
            f.write('改动内容：将画布中的矩形填充颜色改为蓝色（#0066FF）\n')
        proc = subprocess.run(['open', '-a', 'Figma'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(1)
        return {'status': 'completed', 'state': {}}
