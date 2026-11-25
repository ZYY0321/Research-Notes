import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser('~/e31-newapps/seed/ps-2-14-ps-selective-color-adjust-seed.png')
NOTES = os.path.expanduser('~/e31-newapps/seed/ps-2-14-ps-selective-color-adjust-notes.txt')
OUT = os.path.expanduser('~/e31-newapps/out/ps-2-14-ps-selective-color-adjust.png')

RED = (200, 40, 40)
BLUE = (40, 60, 200)


def make_seed_png(width, height, left_color, right_color):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    rows = b''
    for y in range(height):
        rows += b'\x00'
        for x in range(width):
            color = left_color if x < width // 2 else right_color
            rows += bytes(color)
    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(rows))
    out += chunk(b'IEND', b'')
    return out

NOTES_TEXT = (
    '选择性颜色调整说明\n'
    '种子图：~/e31-newapps/seed/ps-2-14-ps-selective-color-adjust-seed.png（48x32，左半为红色、右半为蓝色）。\n'
    '要求：只把图中红色 RGB(200,40,40) 的区域全部调整为目标颜色 RGB(30,160,70)。\n'
    '蓝色 RGB(40,60,200) 的区域必须保持原样，一个像素都不要改。\n'
    '完成后保存为 48x32 的 PNG 到 ~/e31-newapps/out/ps-2-14-ps-selective-color-adjust.png。\n'
    '不要覆盖种子图。\n'
)


class Setup(BaseSetup):
    def run(self, context):
        for path in [OUT]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(os.path.dirname(SEED), exist_ok=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(SEED, 'wb') as handle:
            handle.write(make_seed_png(48, 32, RED, BLUE))
        with open(NOTES, 'w', encoding='utf-8') as handle:
            handle.write(NOTES_TEXT)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
