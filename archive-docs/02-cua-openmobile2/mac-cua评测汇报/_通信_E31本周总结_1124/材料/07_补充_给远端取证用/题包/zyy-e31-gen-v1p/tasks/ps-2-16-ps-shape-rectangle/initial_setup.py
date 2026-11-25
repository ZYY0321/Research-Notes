import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser('~/Desktop/e31-newapps/seed/ps-2-16-ps-shape-rectangle-seed.png')
NOTES = os.path.expanduser('~/Desktop/e31-newapps/seed/ps-2-16-ps-shape-rectangle-notes.txt')
OUT = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-16-ps-shape-rectangle.png')


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def _solid_png(width, height, rgb):
    row = b'\x00' + bytes(rgb) * width
    raw = row * height
    return (b'\x89PNG\r\n\x1a\n'
            + _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + _chunk(b'IDAT', zlib.compress(raw))
            + _chunk(b'IEND', b''))


class Setup(BaseSetup):
    def run(self, context):
        for path in [OUT]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(os.path.dirname(SEED), exist_ok=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(SEED, 'wb') as f:
            f.write(_solid_png(64, 48, (230, 230, 230)))
        with open(NOTES, 'w', encoding='utf-8') as f:
            f.write('底图：64x48 像素，纯色 RGB(230,230,230)，路径 ~/Desktop/e31-newapps/seed/ps-2-16-ps-shape-rectangle-seed.png。\n'
                    '任务：用矩形形状工具画一个实色填充的矩形。\n'
                    '填充颜色：RGB(200,30,40)。\n'
                    '位置：矩形覆盖从像素 (16,12) 到 (47,35) 的区域（含边界），不要描边。\n'
                    '矩形之外的像素保持底图原色。\n'
                    '完成后导出 PNG 到 ~/Desktop/e31-newapps/out/ps-2-16-ps-shape-rectangle.png，尺寸保持 64x48。\n')
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
