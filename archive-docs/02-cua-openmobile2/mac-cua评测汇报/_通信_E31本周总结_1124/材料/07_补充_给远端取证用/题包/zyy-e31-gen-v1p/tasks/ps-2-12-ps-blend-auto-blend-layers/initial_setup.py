import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _png_bytes(width, height, pixel_fn):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            r, g, b = pixel_fn(x, y)
            raw.extend((r & 255, g & 255, b & 255))
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw)))
            + chunk(b"IEND", b""))


class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser("~/Desktop/e31-newapps/out")
        seed_dir = os.path.expanduser("~/Desktop/e31-newapps/seed")
        os.makedirs(out_dir, exist_ok=True)
        os.makedirs(seed_dir, exist_ok=True)
        target = os.path.join(out_dir, "ps-2-12-ps-blend-auto-blend-layers.png")
        if os.path.lexists(target):
            os.remove(target)
        scene_w, seed_w, seed_h = 200, 120, 80
        offsets = [0, 40, 80]
        seeds = []
        for index, off in enumerate(offsets):
            def pixel(x, y, off=off):
                gx = x + off
                r = (gx * 255) // scene_w
                g = (y * 255) // seed_h
                b = 255 - r
                return (r, g, b)
            path = os.path.join(seed_dir, "ps-2-12-photo-%d.png" % (index + 1))
            with open(path, "wb") as handle:
                handle.write(_png_bytes(seed_w, seed_h, pixel))
            seeds.append(path)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026"] + seeds, capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seeds": seeds}}
