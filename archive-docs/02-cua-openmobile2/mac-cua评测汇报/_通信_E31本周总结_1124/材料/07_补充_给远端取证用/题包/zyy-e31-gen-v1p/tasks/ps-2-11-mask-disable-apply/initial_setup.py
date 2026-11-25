import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

GREEN = (0, 160, 0)
BLUE = (0, 64, 224)


def _png(width, height, px):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(
        b"\x00" + b"".join(bytes(px(x, y)) for x in range(width))
        for y in range(height)
    )
    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    out += chunk(b"IDAT", zlib.compress(raw))
    out += chunk(b"IEND", b"")
    return out


class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser("~/Desktop/e31-newapps/out")
        os.makedirs(out_dir, exist_ok=True)
        for path in [
            "~/Desktop/e31-newapps/out/ps-2-11-mask-disable-apply.png",
            "~/Desktop/e31-newapps/out/ps-2-11-mask-disable-apply.psd",
        ]:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        seed = os.path.expanduser("~/Desktop/e31-newapps/ps-2-11-mask-disable-apply-seed.png")
        data = _png(48, 48, lambda x, y: GREEN if x < 24 else BLUE)
        with open(seed, "wb") as f:
            f.write(data)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
