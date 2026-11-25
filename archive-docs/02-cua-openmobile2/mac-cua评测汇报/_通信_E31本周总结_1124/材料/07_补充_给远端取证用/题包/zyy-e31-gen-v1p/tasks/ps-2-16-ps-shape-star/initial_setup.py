import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_dir = os.path.expanduser("~/Desktop/e31-newapps/seed")
        out_dir = os.path.expanduser("~/Desktop/e31-newapps/out")
        os.makedirs(seed_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)
        base_path = os.path.join(seed_dir, "ps-2-16-ps-shape-star-base.png")
        img = Image.new('RGB', (64, 64), (200, 200, 200))
        img.save(base_path)
        instruction_path = os.path.expanduser("~/Desktop/e31-newapps/ps-2-16-ps-shape-star-instruction.txt")
        with open(instruction_path, 'w', encoding='utf-8') as f:
            f.write(f"底图路径：{base_path}\n")
            f.write("星形填充颜色：RGB(255, 0, 0)\n")
            f.write("导出尺寸：64×64\n")
            f.write("导出路径：~/Desktop/e31-newapps/out/ps-2-16-ps-shape-star.png\n")
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", base_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(2)
        return {"status": "completed", "state": {}}
