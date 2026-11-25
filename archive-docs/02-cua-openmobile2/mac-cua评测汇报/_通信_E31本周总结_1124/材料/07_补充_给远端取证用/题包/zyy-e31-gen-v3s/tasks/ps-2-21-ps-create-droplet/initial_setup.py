import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

INSTRUCTIONS_PATH = "~/Desktop/e31-newapps/ps-2-21-ps-create-droplet-instructions.txt"
OUT_DIR = "~/Desktop/e31-newapps/out"
INSTRUCTIONS_TEXT = (
    "快捷批处理创建要求（ps-2-21-ps-create-droplet）\n"
    "1. 在 Adobe Photoshop 2026 中准备一个可用的动作（动作面板里任一现有动作即可，没有就先录一个简单动作，例如执行一次图像大小调整）。\n"
    "2. 使用 Photoshop 的快捷批处理功能，基于该动作创建一个快捷批处理。材料未提供菜单步骤与产物位置，以应用内该功能的实际入口为准。\n"
    "3. 把生成的快捷批处理保存到 ~/Desktop/e31-newapps/out/ 目录，命名为 ps-2-21-ps-create-droplet（应用会自行决定后缀，不要改动它生成的格式）。\n"
    "4. 完成后记录你走的入口和实际产物落点。\n"
)

class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser(OUT_DIR)
        os.makedirs(out_dir, exist_ok=True)
        for path in ["~/Desktop/e31-newapps/out/ps-2-21-ps-create-droplet.app"]:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                if os.path.isdir(expanded) and not os.path.islink(expanded):
                    import shutil
                    shutil.rmtree(expanded)
                else:
                    os.remove(expanded)
        instructions = os.path.expanduser(INSTRUCTIONS_PATH)
        os.makedirs(os.path.dirname(instructions), exist_ok=True)
        with open(instructions, "w", encoding="utf-8") as handle:
            handle.write(INSTRUCTIONS_TEXT)
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"instructions": INSTRUCTIONS_PATH}}
