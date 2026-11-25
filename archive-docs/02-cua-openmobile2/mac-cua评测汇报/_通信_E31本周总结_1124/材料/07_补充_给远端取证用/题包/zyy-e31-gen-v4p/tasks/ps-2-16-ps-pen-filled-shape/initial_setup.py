import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _solid_png(width, height, rgb):
    row = b"\x00" + bytes(rgb) * width
    raw = row * height
    out = b"\x89PNG\r\n\x1a\n"
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    out += _chunk(b"IDAT", zlib.compress(raw))
    out += _chunk(b"IEND", b"")
    return out


NOTE = (
    "ps-2-16 说明\n"
    "1. 底图：~/e31-newapps/ps-2-16-seed.png，48x48，纯色底 RGB(220,220,220)。\n"
    "2. 用钢笔工具在画布中央逐点绘制一个闭合形状（形状要盖住画布正中心，画布四边各留至少 6 像素不要画到），\n"
    "   并用实色 RGB(190,30,60) 填充该形状。形状之外保持底图原色不动。\n"
    "3. 保存后导出 PNG 到 ~/e31-newapps/out/ps-2-16-ps-pen-filled-shape.png，尺寸保持 48x48。\n"
    "4. 不要覆盖底图文件。\n"
)


class Setup(BaseSetup):
    def run(self, context):
        base = os.path.expanduser("~/e31-newapps")
        out_dir = os.path.join(base, "out")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "ps-2-16-ps-pen-filled-shape.png")
        if os.path.lexists(out_path):
            os.remove(out_path)
        seed_path = os.path.join(base, "ps-2-16-seed.png")
        with open(seed_path, "wb") as f:
            f.write(_solid_png(48, 48, (220, 220, 220)))
        note_path = os.path.join(base, "ps-2-16-note.txt")
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(NOTE)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed_path, "note": note_path}}
