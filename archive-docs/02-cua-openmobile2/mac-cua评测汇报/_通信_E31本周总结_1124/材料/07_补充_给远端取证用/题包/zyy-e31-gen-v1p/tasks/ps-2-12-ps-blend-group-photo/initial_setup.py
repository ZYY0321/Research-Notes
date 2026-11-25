import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _write_png(path, width, height, pixel_fn):
    rows = []
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            r, g, b = pixel_fn(x, y)
            row += bytes((r & 255, g & 255, b & 255))
        rows.append(bytes(row))
    raw = b"".join(rows)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    body = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(raw)) + _chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(body)


class Setup(BaseSetup):
    def run(self, context):
        seed_dir = os.path.expanduser("~/Desktop/e31-newapps/seed")
        out_dir = os.path.expanduser("~/Desktop/e31-newapps/out")
        os.makedirs(seed_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)
        target = os.path.join(out_dir, "ps-2-12-ps-blend-group-photo.png")
        if os.path.lexists(target):
            os.remove(target)
        width, height = 64, 48
        for index in range(3):
            shift = index * 7

            def pixel(x, y, shift=shift, index=index):
                base = (120 + x * 2 - shift, 110 + y * 2, 90 + index * 25)
                cx = 16 + index * 14
                cy = 22 + (index % 2) * 6
                if (x - cx) * (x - cx) + (y - cy) * (y - cy) < 36:
                    return (235, 200 - index * 20, 170)
                return base

            path = os.path.join(seed_dir, "ps-2-12-group-%d.png" % (index + 1))
            _write_png(path, width, height, pixel)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026"], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"seeds": 3}}
