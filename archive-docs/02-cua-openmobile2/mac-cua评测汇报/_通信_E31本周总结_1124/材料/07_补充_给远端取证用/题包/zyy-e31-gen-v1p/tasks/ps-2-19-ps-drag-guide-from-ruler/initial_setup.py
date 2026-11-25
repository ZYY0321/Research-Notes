import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED_DIR = os.path.expanduser("~/Desktop/e31-newapps/seed")
OUT_DIR = os.path.expanduser("~/Desktop/e31-newapps/out")
SEED_PNG = os.path.join(SEED_DIR, "ps-2-19-image.png")
NOTE_TXT = os.path.join(SEED_DIR, "ps-2-19-instructions.txt")
TARGET = os.path.join(OUT_DIR, "ps-2-19-ps-drag-guide-from-ruler.png")


def _chunk(tag, data):
    body = struct.pack(">I", len(data)) + tag + data
    return body + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _png(width, height):
    rows = []
    for y in range(height):
        if y < height // 2:
            rgb = (70, 130, 180)
        else:
            rgb = (245, 222, 120)
        rows.append(b"\x00" + bytes(rgb) * width)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"".join(rows))
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")


class Setup(BaseSetup):
    def run(self, context):
        os.makedirs(SEED_DIR, exist_ok=True)
        os.makedirs(OUT_DIR, exist_ok=True)
        if os.path.lexists(TARGET):
            os.remove(TARGET)
        with open(SEED_PNG, "wb") as f:
            f.write(_png(48, 32))
        note = (
            "请在 Adobe Photoshop 2026 中打开这张图像：\n"
            "~/Desktop/e31-newapps/seed/ps-2-19-image.png\n\n"
            "操作：先用 View > Rulers 显示标尺，\n"
            "再从水平标尺往下拖出一条水平参考线，\n"
            "放在距图像顶部 16 像素处。\n"
        )
        with open(NOTE_TXT, "w", encoding="utf-8") as f:
            f.write(note)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", SEED_PNG], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
