import os, sys, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_path = os.path.expanduser('~/e31-newapps/e31-seed.png')
        out_path = os.path.expanduser('~/e31-newapps/out/ps-2-8-stroke-apply.png')
        
        for path in [seed_path, out_path]:
            if os.path.lexists(path):
                os.remove(path)
        
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
        width, height = 64, 64
        square_size = 40
        margin = (width - square_size) // 2
        
        rows = []
        for y in range(height):
            row = b''
            for x in range(width):
                if margin <= x < margin + square_size and margin <= y < margin + square_size:
                    row += b'\x00\x00\x00'
                else:
                    row += b'\xff\xff\xff'
            rows.append(row)
        
        png_data = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
        png_data += struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
        
        raw_data = b''.join(b'\x00' + row for row in rows)
        compressed = zlib.compress(raw_data, 9)
        idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
        png_data += struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
        
        iend_crc = zlib.crc32(b'IEND') & 0xffffffff
        png_data += struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
        
        with open(seed_path, 'wb') as f:
            f.write(png_data)
        
        return {"status": "completed", "state": {}}
