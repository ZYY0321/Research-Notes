import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _png_bytes(width, height, rgb):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''.join(b'\x00' + bytes(rgb) * width for _ in range(height))
    header = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', header)
            + chunk(b'IDAT', zlib.compress(raw))
            + chunk(b'IEND', b''))


class Setup(BaseSetup):
    def run(self, context):
        seed_dir = os.path.expanduser('~/e31-newapps/seed')
        out_dir = os.path.expanduser('~/e31-newapps/out')
        os.makedirs(seed_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)
        target = os.path.expanduser('~/e31-newapps/out/ps-2-19-ps-new-guide-menu.png')
        if os.path.lexists(target):
            os.remove(target)
        seed_png = os.path.join(seed_dir, 'ps-2-19-ps-new-guide-menu-seed.png')
        with open(seed_png, 'wb') as fh:
            fh.write(_png_bytes(48, 32, (200, 200, 200)))
        instructions = os.path.join(seed_dir, 'ps-2-19-ps-new-guide-menu-instructions.txt')
        with open(instructions, 'w', encoding='utf-8') as fh:
            fh.write('图像文件: ~/e31-newapps/seed/ps-2-19-ps-new-guide-menu-seed.png\n')
            fh.write('用 View > Guides > New Guide 新建一条参考线，设置如下：\n')
            fh.write('方向 (Orientation): 垂直 (Vertical)\n')
            fh.write('颜色 (Color): 青色 (Cyan)\n')
            fh.write('位置 (Position): 24 像素 (24 px)\n')
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
