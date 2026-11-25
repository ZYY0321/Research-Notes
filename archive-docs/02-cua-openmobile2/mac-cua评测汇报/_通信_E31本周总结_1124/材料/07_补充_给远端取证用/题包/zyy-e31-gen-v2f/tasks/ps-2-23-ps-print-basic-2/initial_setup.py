import os, sys, subprocess, time, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_path = os.path.expanduser("~/Desktop/e31-newapps/seed-ps-2-23-ps-print-basic-2.bmp")
        os.makedirs(os.path.dirname(seed_path), exist_ok=True)
        width, height = 100, 100
        row_size = ((width * 3 + 3) // 4) * 4
        pixel_data_size = row_size * height
        file_size = 54 + pixel_data_size
        bmp_header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, 54)
        dib_header = struct.pack('<IIIHHIIIIII', 40, width, height, 1, 24, 0, pixel_data_size, 2835, 2835, 0, 0)
        with open(seed_path, 'wb') as f:
            f.write(bmp_header + dib_header)
            for _ in range(height):
                f.write(bytes([255, 255, 255] * width))
                padding = row_size - width * 3
                if padding > 0:
                    f.write(bytes(padding))
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(2)
        return {"status": "completed", "state": {}}
