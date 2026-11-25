import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _png(width, height, pixel):
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)
    raw = b""
    for y in range(height):
        raw += b"\x00"
        for x in range(width):
            raw += bytes(pixel(x, y))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class Setup(BaseSetup):
    def run(self, context):
        base = os.path.expanduser("~/Desktop/e31-newapps")
        seed_dir = os.path.join(base, "seed")
        os.makedirs(seed_dir, exist_ok=True)
        os.makedirs(os.path.join(base, "out"), exist_ok=True)
        seed = os.path.join(seed_dir, "ps-2-19-ps-measure-and-scale-seed.png")

        def pixel(x, y):
            if 12 <= x < 44 and 10 <= y < 30:
                return (30, 80, 200)
            return (245, 245, 245)

        with open(seed, "wb") as f:
            f.write(_png(64, 40, pixel))
        note = os.path.join(seed_dir, "ps-2-19-ps-measure-and-scale-\u8bf4\u660e.txt")
        with open(note, "w", encoding="utf-8") as f:
            f.write("\u8bf7\u5728 Photoshop \u4e2d\u6253\u5f00\u56fe\u50cf\u6587\u4ef6\uff1a" + seed + "\n")
            f.write("\u9700\u8981\u6d4b\u91cf\u7684\u5bf9\u8c61\uff1a\u56fe\u50cf\u4e2d\u592e\u7684\u84dd\u8272\u77e9\u5f62\u3002\n")
            f.write("\u8bf7\u4f7f\u7528 Photoshop \u7684\u6d4b\u91cf\u529f\u80fd\u91cf\u51fa\u8be5\u77e9\u5f62\u7684\u50cf\u7d20\u5bbd\u5ea6\u548c\u9ad8\u5ea6\u3002\n")
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
