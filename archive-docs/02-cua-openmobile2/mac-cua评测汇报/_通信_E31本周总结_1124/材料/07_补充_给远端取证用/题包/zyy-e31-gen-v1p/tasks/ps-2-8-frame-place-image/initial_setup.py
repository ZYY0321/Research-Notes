import os, sys, subprocess, time, zlib, struct, binascii
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED_DIR = os.path.expanduser("~/Desktop/e31-newapps/seed")
OUT_DIR = os.path.expanduser("~/Desktop/e31-newapps/out")
PHOTO = os.path.join(SEED_DIR, "ps-2-8-photo.png")
FRAME_PSD = os.path.join(SEED_DIR, "ps-2-8-frame.psd")


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)


def _png_bytes(width, height, rgb):
    row = b"\x00" + bytes(rgb) * width
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(row * height)) + _chunk(b"IEND", b""))


class Setup(BaseSetup):
    def run(self, context):
        os.makedirs(SEED_DIR, exist_ok=True)
        os.makedirs(OUT_DIR, exist_ok=True)
        for path in ["~/Desktop/e31-newapps/out/ps-2-8-frame-place-image.png", "~/Desktop/e31-newapps/out/ps-2-8-frame-place-image.psd"]:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        if not os.path.exists(PHOTO):
            with open(PHOTO, "wb") as f:
                f.write(_png_bytes(48, 32, (210, 120, 40)))
        if os.path.exists(FRAME_PSD):
            proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", FRAME_PSD], capture_output=True, text=True)
        else:
            proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026"], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
