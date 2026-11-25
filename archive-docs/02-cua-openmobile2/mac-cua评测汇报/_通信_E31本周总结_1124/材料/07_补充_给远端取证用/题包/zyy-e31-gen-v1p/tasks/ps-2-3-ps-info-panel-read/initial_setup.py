import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup
from PIL import Image, ImageDraw

class Setup(BaseSetup):
    def run(self, context):
        seed_path = os.path.expanduser('~/Desktop/e31-newapps/seed-ps-2-3-ps-info-panel-read.psd')
        instruction_path = os.path.expanduser('~/Desktop/e31-newapps/instruction-ps-2-3-ps-info-panel-read.txt')
        os.makedirs(os.path.dirname(seed_path), exist_ok=True)
        
        img = Image.new('RGB', (200, 150), color=(120, 80, 200))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 100, 100], fill=(255, 128, 64))
        img.save(seed_path, 'PNG')
        
        instruction_text = '''请将鼠标移动到图像中坐标 (75, 75) 的位置。\n\nInfo 面板应显示该位置的 RGB 值为 R:255 G:128 B:64（或接近该值）。\n\n请观察 Info 面板是否正确显示了坐标和颜色信息。'''
        with open(instruction_path, 'w', encoding='utf-8') as f:
            f.write(instruction_text)
        
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(2)
        return {'status': 'completed', 'state': {}}
