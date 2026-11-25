import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_dir = os.path.expanduser('~/Desktop/e31-newapps/seeds/ps-2-21-ps-batch-process-files')
        os.makedirs(seed_dir, exist_ok=True)
        for i in range(4):
            img = Image.new('RGB', (32, 32), color=(50 + i * 20, 100, 150))
            img.save(os.path.join(seed_dir, f'image_{i+1}.jpg'))
        instructions = os.path.expanduser('~/Desktop/e31-newapps/seeds/ps-2-21-ps-batch-process-files-instructions.txt')
        with open(instructions, 'w', encoding='utf-8') as f:
            f.write('对所有图像执行以下处理：\n1. 调整图像大小为 64×64 像素\n2. 转换为 PNG 格式\n3. 保存到输出文件夹')
        out_dir = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-21-ps-batch-process-files')
        os.makedirs(out_dir, exist_ok=True)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(1)
        return {'status': 'completed', 'state': {}}
