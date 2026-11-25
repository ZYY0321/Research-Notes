import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser('~/Desktop/e31-newapps/seed/ps-2-14-ps-channel-manipulation-seed.png')
INSTR = os.path.expanduser('~/Desktop/e31-newapps/seed/ps-2-14-ps-channel-manipulation-instructions.txt')
OUT = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-14-ps-channel-manipulation.png')

INSTR_TEXT = (
    '通道操作说明\n'
    '1. 用 Adobe Photoshop 2026 打开图像：~/Desktop/e31-newapps/seed/ps-2-14-ps-channel-manipulation-seed.png\n'
    '2. 在「通道」面板里只选中「绿」通道，把整个绿色通道填充为白色（数值 255）。红、蓝通道保持原样。\n'
    '   （种子图整幅是 RGB(120, 80, 200)，操作完成后合成颜色应是 RGB(120, 255, 200)。）\n'
    '3. 回到合成视图，把结果保存为 PNG：~/Desktop/e31-newapps/out/ps-2-14-ps-channel-manipulation.png\n'
    '4. 不要改动或覆盖种子图本身。\n'
)

def _chunk(tag, data):
    body = tag + data
    return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xffffffff)

def _png(width, height, rgb):
    raw = b''.join(b'\x00' + bytes(rgb) * width for _ in range(height))
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', ihdr)
            + _chunk(b'IDAT', zlib.compress(raw)) + _chunk(b'IEND', b''))

class Setup(BaseSetup):
    def run(self, context):
        for path in [OUT]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(os.path.dirname(SEED), exist_ok=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(SEED, 'wb') as handle:
            handle.write(_png(48, 32, (120, 80, 200)))
        with open(INSTR, 'w', encoding='utf-8') as handle:
            handle.write(INSTR_TEXT)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
