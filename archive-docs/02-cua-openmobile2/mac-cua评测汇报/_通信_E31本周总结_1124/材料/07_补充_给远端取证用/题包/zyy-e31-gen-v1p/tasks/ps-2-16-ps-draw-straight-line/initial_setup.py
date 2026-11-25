import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup
import struct
import zlib

def create_png(width, height, color):
    png_sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
    ihdr = struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    raw = b''
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            raw += bytes(color)
    compressed = zlib.compress(raw, 9)
    idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    return png_sig + ihdr + idat + iend

class Setup(BaseSetup):
    def run(self, context):
        seeds_dir = os.path.expanduser("~/Desktop/e31-newapps/seeds")
        out_dir = os.path.expanduser("~/Desktop/e31-newapps/out")
        os.makedirs(seeds_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)
        seed_path = os.path.join(seeds_dir, "ps-2-16-seed.png")
        with open(seed_path, 'wb') as f:
            f.write(create_png(64, 64, (240, 240, 240)))
        instructions_path = os.path.join(seeds_dir, "ps-2-16-instructions.txt")
        instructions = """请用 Photoshop 的绘图工具（如画笔工具、直线工具等）在当前打开的图像上画一条红色 RGB(255, 0, 0) 的直线。\n完成后，将图像导出为 PNG 格式，保存到：~/Desktop/e31-newapps/out/ps-2-16-ps-draw-straight-line.png\n\n注意：\n- 种子图尺寸为 64x64 像素，背景色为浅灰色 RGB(240, 240, 240)\n- 直线可以是任意位置和方向，但必须可见\n- 导出时请选择 PNG 格式\n- 请保持图像尺寸为 64x64 像素\n"""
        with open(instructions_path, 'w', encoding='utf-8') as f:
            f.write(instructions)
        out_path = os.path.expanduser("~/Desktop/e31-newapps/out/ps-2-16-ps-draw-straight-line.png")
        if os.path.exists(out_path):
            os.remove(out_path)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(2)
        return {"status": "completed", "state": {}}
