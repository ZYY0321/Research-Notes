import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED_DIR = os.path.expanduser("~/e31-newapps/seed")
SEED_PNG = os.path.join(SEED_DIR, "ps-2-21-seed.png")
SEED_TXT = os.path.join(SEED_DIR, "ps-2-21-instructions.txt")

INSTRUCTIONS = (
    "ps-2-21 录制新动作的设置说明\n"
    "1. 先在 Actions 面板菜单里 New Set，动作集名称：E31 Set\n"
    "2. 再从面板菜单选 New Action，对话框里填：\n"
    "   名称：E31 Rotate Action\n"
    "   Set：E31 Set\n"
    "   Function Key：F3，勾选 Shift 和 Command\n"
    "   Color（按钮模式颜色）：Red\n"
    "3. 点 Record 开始录制，对种子图执行以下编辑步骤：\n"
    "   a) Image > Image Rotation > 180°\n"
    "   b) Image > Adjustments > Invert\n"
    "4. 按 Actions 面板底部的 Stop 停止录制。\n"
)

def make_png(width, height, rgb):
    def chunk(tag, data):
        raw = tag + data
        return struct.pack(">I", len(data)) + raw + struct.pack(">I", zlib.crc32(raw) & 0xffffffff)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes(rgb) * width
    body = zlib.compress(row * height)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", body) + chunk(b"IEND", b""))

class Setup(BaseSetup):
    def run(self, context):
        os.makedirs(SEED_DIR, exist_ok=True)
        with open(SEED_PNG, "wb") as handle:
            handle.write(make_png(64, 64, (180, 120, 60)))
        with open(SEED_TXT, "w", encoding="utf-8") as handle:
            handle.write(INSTRUCTIONS)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", SEED_PNG], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": SEED_PNG, "instructions": SEED_TXT}}
