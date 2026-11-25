import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = "~/e31-newapps/ps-2-14-ps-color-profile-embed-seed.png"
NOTE = "~/e31-newapps/ps-2-14-ps-color-profile-embed-instructions.txt"
OUT = "~/e31-newapps/out/ps-2-14-ps-color-profile-embed.png"


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _png(width, height, rgb):
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(raw)) + _chunk(b"IEND", b""))


class Setup(BaseSetup):
    def run(self, context):
        out = os.path.expanduser(OUT)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if os.path.lexists(out):
            os.remove(out)
        seed = os.path.expanduser(SEED)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        with open(seed, "wb") as f:
            f.write(_png(48, 32, (120, 60, 200)))
        note = os.path.expanduser(NOTE)
        with open(note, "w", encoding="utf-8") as f:
            f.write("种子图像: " + SEED + "\n")
            f.write("请在 Adobe Photoshop 2026 中打开上面的种子图像，用 Save As 保存为 PNG，\n")
            f.write("保存时勾选 Color 选项（Embed Color Profile，嵌入颜色配置文件）。\n")
            f.write("保存到: " + OUT + "\n")
            f.write("不要改动图像内容，也不要覆盖种子图。\n")
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
