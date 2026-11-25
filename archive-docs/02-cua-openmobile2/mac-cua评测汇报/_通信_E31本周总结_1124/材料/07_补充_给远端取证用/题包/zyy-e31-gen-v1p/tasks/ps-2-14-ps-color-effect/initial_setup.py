import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _png(width, height, rgb):
    raw = b''.join(b'\x00' + bytes(rgb) * width for _ in range(height))
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


class Setup(BaseSetup):
    def run(self, context):
        out = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-14-ps-color-effect.png')
        if os.path.lexists(out):
            os.remove(out)
        base = os.path.expanduser('~/Desktop/e31-newapps/ps-2-14-ps-color-effect')
        os.makedirs(base, exist_ok=True)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        seed = os.path.join(base, 'seed.png')
        with open(seed, 'wb') as f:
            f.write(_png(48, 32, (120, 120, 120)))
        with open(os.path.join(base, 'reference.png'), 'wb') as f:
            f.write(_png(48, 32, (150, 118, 82)))
        note = (
            '说明：用 Adobe Photoshop 2026 打开本文件夹里的 seed.png，\n'
            '给整幅图套用一个暖褐色（怀旧/棕褐调）的颜色效果，\n'
            '使整体色彩与 reference.png 一致：全图呈现约 RGB(150, 118, 82) 的暖褐色，允许轻微误差。\n'
            '保持尺寸 48x32 不变，然后导出 PNG 到 ~/Desktop/e31-newapps/out/ps-2-14-ps-color-effect.png。\n'
            '不要覆盖 seed.png。\n'
        )
        with open(os.path.join(base, 'README.txt'), 'w', encoding='utf-8') as f:
            f.write(note)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
