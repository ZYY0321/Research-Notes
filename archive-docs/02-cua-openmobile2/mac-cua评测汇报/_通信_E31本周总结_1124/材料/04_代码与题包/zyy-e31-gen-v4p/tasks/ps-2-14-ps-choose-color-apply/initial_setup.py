import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED_DIR = os.path.expanduser("~/e31-newapps/seed")
OUT_DIR = os.path.expanduser("~/e31-newapps/out")
SEED_PNG = os.path.join(SEED_DIR, "ps-2-14-seed.png")
SEED_TXT = os.path.join(SEED_DIR, "ps-2-14-instructions.txt")
OUT_PNG = os.path.join(OUT_DIR, "ps-2-14-ps-choose-color-apply.png")


def write_png(path, width, height, rgb):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    blob = b"\x89PNG\r\n\x1a\n"
    blob += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    blob += chunk(b"IDAT", zlib.compress(raw))
    blob += chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(blob)


class Setup(BaseSetup):
    def run(self, context):
        os.makedirs(SEED_DIR, exist_ok=True)
        os.makedirs(OUT_DIR, exist_ok=True)
        if os.path.lexists(OUT_PNG):
            os.remove(OUT_PNG)
        write_png(SEED_PNG, 48, 32, (60, 60, 60))
        lines = [
            "目标图像：~/e31-newapps/seed/ps-2-14-seed.png",
            "选定颜色：RGB(31, 119, 180)，十六进制 #1F77B4",
            "上色区域：整个画面",
            "保存：导出 PNG 到 ~/e31-newapps/out/ps-2-14-ps-choose-color-apply.png，画布尺寸保持 48x32",
        ]
        with open(SEED_TXT, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", SEED_PNG], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
