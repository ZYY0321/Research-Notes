import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser("~/e31-newapps/out")
        os.makedirs(out_dir, exist_ok=True)
        for path in ["~/e31-newapps/out/ps-2-11-clipping-mask.png", "~/e31-newapps/out/ps-2-11-clipping-mask.psd"]:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        width, height = 48, 32
        raw = b"".join(b"\x00" + bytes((200, 200, 200)) * width for _ in range(height))
        png = b"".join([
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            chunk(b"IDAT", zlib.compress(raw)),
            chunk(b"IEND", b""),
        ])
        seed = os.path.expanduser("~/e31-newapps/ps-2-11-clipping-mask-seed.png")
        with open(seed, "wb") as handle:
            handle.write(png)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
