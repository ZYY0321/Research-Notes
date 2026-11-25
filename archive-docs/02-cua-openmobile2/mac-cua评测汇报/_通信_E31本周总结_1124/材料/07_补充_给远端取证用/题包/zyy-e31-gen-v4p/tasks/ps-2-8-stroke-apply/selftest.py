import json, tempfile, struct, zlib
import evaluation
import fixturelib as F

def create_stroke_image(width, height, stroke_color, stamp):
    square_size = 40
    margin = (width - square_size) // 2
    stroke_width = 10
    
    rows = []
    for y in range(height):
        row = b''
        for x in range(width):
            in_square = margin <= x < margin + square_size and margin <= y < margin + square_size
            dist_to_square = 0
            if not in_square:
                dx = max(0, margin - x, x - (margin + square_size - 1))
                dy = max(0, margin - y, y - (margin + square_size - 1))
                dist_to_square = max(dx, dy)
            
            if in_square:
                row += b'\x00\x00\x00'
            elif dist_to_square > 0 and dist_to_square <= stroke_width:
                row += bytes(stroke_color)
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
    
    if stamp:
        text_data = b'Adobe Photoshop'
        text_chunk_data = b'Software\x00' + text_data
        text_crc = zlib.crc32(b'tEXt' + text_chunk_data) & 0xffffffff
        png_data += struct.pack('>I', len(text_chunk_data)) + b'tEXt' + text_chunk_data + struct.pack('>I', text_crc)
    
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    png_data += struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    
    return png_data

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        
        F.write(out, create_stroke_image(width, height, [255, 0, 0], False))
        cases.append(F.case("shortcut", params, 0))
        
        F.write(out, create_stroke_image(width, height, [255, 0, 0], True))
        cases.append(F.case("reference", params, 1))
        
        F.write(out, create_stroke_image(width, height, [0, 0, 255], True))
        cases.append(F.case("near_miss", params, 0))
        
        F.write(out, create_stroke_image(width + 4, height, [255, 0, 0], True))
        cases.append(F.case("param_swap", params, 0))
    
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
