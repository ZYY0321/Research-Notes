import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def _png(width, height, rgb):
    raw = b''.join(b'\x00' + bytes(rgb) * width for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n'
            + _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + _chunk(b'IDAT', zlib.compress(raw))
            + _chunk(b'IEND', b''))


class Setup(BaseSetup):
    def run(self, context):
        out_path = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-21-ps-action-play-on-image.png')
        if os.path.lexists(out_path):
            os.remove(out_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        in_dir = os.path.expanduser('~/Desktop/e31-newapps/in')
        os.makedirs(in_dir, exist_ok=True)
        seed_path = os.path.join(in_dir, 'ps-2-21-seed.png')
        with open(seed_path, 'wb') as f:
            f.write(_png(48, 32, (30, 120, 200)))
        note = ('动作集：e31\n'
                '动作名：e31-invert\n'
                '动作内容：对当前图像执行一步 图像 > 调整 > 反相（Image > Adjustments > Invert）。\n'
                '播放完成后另存为 PNG：~/Desktop/e31-newapps/out/ps-2-21-ps-action-play-on-image.png\n'
                '保存尺寸与原图一致：48×32。不要覆盖种子图。\n')
        with open(os.path.join(in_dir, 'ps-2-21-instructions.txt'), 'w', encoding='utf-8') as f:
            f.write(note)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
