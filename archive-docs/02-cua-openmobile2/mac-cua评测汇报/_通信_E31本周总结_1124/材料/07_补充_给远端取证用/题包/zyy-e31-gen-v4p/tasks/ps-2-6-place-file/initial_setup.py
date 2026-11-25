import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _write_png(path, width, height, rgb):
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
        seed_dir = os.path.expanduser("~/e31-newapps/seed")
        os.makedirs(seed_dir, exist_ok=True)
        doc_path = os.path.join(seed_dir, "ps-2-6-doc.png")
        asset_path = os.path.join(seed_dir, "ps-2-6-asset.png")
        for path in [doc_path, asset_path]:
            if os.path.lexists(path):
                os.remove(path)
        _write_png(doc_path, 64, 48, (200, 200, 200))
        _write_png(asset_path, 24, 24, (30, 90, 200))
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", doc_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"doc": doc_path, "asset": asset_path}}
