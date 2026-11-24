import math
import os
import struct
import zlib


def _chunk(tag, data):
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def _write_png(path, width, height, buf, channels):
    if len(buf) != width * height * channels:
        raise ValueError("png buffer length")
    raw = bytearray()
    stride = width * channels
    for y in range(height):
        raw.append(0)
        raw.extend(buf[y * stride:(y + 1) * stride])
    color = 6 if channels == 4 else 2
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color, 0, 0, 0)
    data = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)


def _write_psd(path, width, height, rgb):
    if len(rgb) != width * height * 3:
        raise ValueError("psd buffer length")
    channels = [bytes(rgb[offset::3]) for offset in range(3)]
    header = b"8BPS" + struct.pack(">H", 1) + b"\x00" * 6
    header += struct.pack(">HIIHH", 3, height, width, 8, 3)
    body = struct.pack(">III", 0, 0, 0) + struct.pack(">H", 0) + b"".join(channels)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(header + body)


_ZZ = [
    0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5,
    12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63,
]
_QY = [
    16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99,
]
_QC = [
    17, 18, 24, 47, 99, 99, 99, 99, 18, 21, 26, 66, 99, 99, 99, 99,
    24, 26, 56, 99, 99, 99, 99, 99, 47, 66, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99,
]
_COS = [[math.cos((2 * x + 1) * u * math.pi / 16.0) for u in range(8)] for x in range(8)]


def _huffman(symbols, length):
    symbols = list(symbols)
    if len(symbols) > (1 << length):
        raise ValueError("huffman overflow")
    counts = [0] * 16
    counts[length - 1] = len(symbols)
    codes = {}
    code = 0
    index = 0
    for bits in range(1, 17):
        for _ in range(counts[bits - 1]):
            codes[symbols[index]] = (code, bits)
            code += 1
            index += 1
        code <<= 1
    return counts, symbols, codes


def _amp_bits(value):
    if value == 0:
        return 0, 0
    size = abs(value).bit_length()
    extra = value if value > 0 else value + (1 << size) - 1
    return size, extra


class _Bits:
    def __init__(self):
        self.buf = bytearray()
        self.acc = 0
        self.n = 0

    def write(self, code, length):
        if length <= 0:
            return
        self.acc = (self.acc << length) | (code & ((1 << length) - 1))
        self.n += length
        while self.n >= 8:
            self.n -= 8
            byte = (self.acc >> self.n) & 0xFF
            self.buf.append(byte)
            if byte == 0xFF:
                self.buf.append(0x00)
        self.acc &= (1 << self.n) - 1 if self.n else 0

    def flush(self):
        if self.n:
            self.write((1 << (8 - self.n)) - 1, 8 - self.n)


def _dct(block):
    out = [0.0] * 64
    for v in range(8):
        cv = 0.7071067811865476 if v == 0 else 1.0
        for u in range(8):
            cu = 0.7071067811865476 if u == 0 else 1.0
            total = 0.0
            for y in range(8):
                for x in range(8):
                    total += block[y * 8 + x] * _COS[x][u] * _COS[y][v]
            out[v * 8 + u] = 0.25 * cu * cv * total
    return out


def _qdiv(coeff, quant):
    if coeff >= 0:
        return int(coeff / quant + 0.5)
    return -int((-coeff) / quant + 0.5)


def _write_jpeg(path, width, height, rgb):
    if len(rgb) != width * height * 3:
        raise ValueError("jpeg buffer length")
    mw = (width + 7) // 8 * 8
    mh = (height + 7) // 8 * 8
    planes = [bytearray(mw * mh) for _ in range(3)]
    for y in range(mh):
        sy = min(y, height - 1)
        for x in range(mw):
            sx = min(x, width - 1)
            i = (sy * width + sx) * 3
            r, g, b = rgb[i], rgb[i + 1], rgb[i + 2]
            yy = (77 * r + 150 * g + 29 * b) >> 8
            cb = ((-43 * r - 85 * g + 128 * b) >> 8) + 128
            cr = ((128 * r - 107 * g - 21 * b) >> 8) + 128
            j = y * mw + x
            planes[0][j] = max(0, min(255, yy))
            planes[1][j] = max(0, min(255, cb))
            planes[2][j] = max(0, min(255, cr))
    ac_symbols = [0x00, 0xF0]
    for run in range(16):
        for size in range(1, 12):
            ac_symbols.append((run << 4) | size)
    dc_counts, dc_vals, dc_codes = _huffman(list(range(12)), 4)
    ac_counts, ac_vals, ac_codes = _huffman(ac_symbols, 8)

    def blocks(plane, quant):
        encoded = []
        prev = 0
        for by in range(0, mh, 8):
            for bx in range(0, mw, 8):
                spatial = []
                for y in range(8):
                    row = (by + y) * mw + bx
                    spatial.extend(plane[row + x] - 128 for x in range(8))
                freq = _dct(spatial)
                zz = []
                for pos in range(64):
                    natural = _ZZ[pos]
                    coeff = _qdiv(freq[natural], quant[natural])
                    if coeff > 2047:
                        coeff = 2047
                    elif coeff < -2047:
                        coeff = -2047
                    zz.append(coeff)
                delta = zz[0] - prev
                prev = zz[0]
                encoded.append((delta, zz))
        return encoded

    y_blocks = blocks(planes[0], _QY)
    cb_blocks = blocks(planes[1], _QC)
    cr_blocks = blocks(planes[2], _QC)
    bits = _Bits()

    def put_dc(value):
        size, extra = _amp_bits(value)
        code, length = dc_codes[size]
        bits.write(code, length)
        bits.write(extra, size)

    def put_ac(zz):
        run = 0
        last_nonzero = 0
        for index in range(1, 64):
            if zz[index]:
                last_nonzero = index
        for index in range(1, 64):
            value = zz[index]
            if value == 0:
                run += 1
                continue
            while run >= 16:
                code, length = ac_codes[0xF0]
                bits.write(code, length)
                run -= 16
            size, extra = _amp_bits(value)
            code, length = ac_codes[(run << 4) | size]
            bits.write(code, length)
            bits.write(extra, size)
            run = 0
        if last_nonzero < 63:
            code, length = ac_codes[0x00]
            bits.write(code, length)

    mcu = 0
    for by in range(mh // 8):
        for bx in range(mw // 8):
            delta, zz = y_blocks[mcu]
            put_dc(delta)
            put_ac(zz)
            delta, zz = cb_blocks[mcu]
            put_dc(delta)
            put_ac(zz)
            delta, zz = cr_blocks[mcu]
            put_dc(delta)
            put_ac(zz)
            mcu += 1
    bits.flush()

    def dht(table_id, counts, values):
        return bytes([table_id]) + bytes(counts) + bytes(values)

    def dqt(table_id, quant):
        return bytes([table_id]) + bytes(quant[_ZZ[i]] for i in range(64))

    def segment(marker, payload):
        return b"\xff" + bytes([marker]) + struct.pack(">H", len(payload) + 2) + payload

    app0 = b"JFIF\x00\x01\x01\x00" + struct.pack(">HH", 1, 1) + b"\x00\x00"
    sof = struct.pack(">BHHB", 8, height, width, 3) + bytes([1, 0x11, 0, 2, 0x11, 1, 3, 0x11, 1])
    sos = bytes([3, 1, 0x00, 2, 0x11, 3, 0x11, 0, 63, 0])
    dht_payload = (
        dht(0x00, dc_counts, dc_vals)
        + dht(0x10, ac_counts, ac_vals)
        + dht(0x01, dc_counts, dc_vals)
        + dht(0x11, ac_counts, ac_vals)
    )
    blob = b"".join([
        b"\xff\xd8",
        segment(0xE0, app0),
        segment(0xDB, dqt(0x00, _QY) + dqt(0x01, _QC)),
        segment(0xC0, sof),
        segment(0xC4, dht_payload),
        segment(0xDA, sos),
        bytes(bits.buf),
        b"\xff\xd9",
    ])
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(blob)


class _Img:
    def __init__(self, width, height, channels, color):
        self.w = width
        self.h = height
        self.ch = channels
        self.buf = bytearray(color) * (width * height)

    def load(self):
        return self

    def __setitem__(self, key, value):
        x, y = key
        if not (0 <= x < self.w and 0 <= y < self.h):
            raise IndexError((x, y))
        value = tuple(value)
        if self.ch == 4 and len(value) == 3:
            value = value + (255,)
        if len(value) < self.ch:
            raise ValueError("pixel")
        start = (y * self.w + x) * self.ch
        for offset in range(self.ch):
            self.buf[start + offset] = int(value[offset]) & 255

    def putpixel(self, xy, value):
        self[xy] = value

    def save(self, path, fmt=None, **kwargs):
        if fmt is None:
            fmt = kwargs.get("format")
        label = (fmt or "").upper()
        ext = os.path.splitext(path)[1].lower()
        if label in ("JPG", "JPEG") or (not label and ext in (".jpg", ".jpeg")):
            if self.ch != 3:
                raise ValueError("jpeg is rgb only")
            _write_jpeg(path, self.w, self.h, bytes(self.buf))
            return
        if label == "PSD" or (not label and ext == ".psd"):
            rgb = self.buf if self.ch == 3 else bytes(
                self.buf[i] for i in range(len(self.buf)) if (i % 4) != 3
            )
            _write_psd(path, self.w, self.h, rgb)
            return
        _write_png(path, self.w, self.h, bytes(self.buf), self.ch)


class _Draw:
    def __init__(self, image):
        self.image = image

    def rectangle(self, box, fill=None, outline=None):
        if fill is None:
            return
        x0, y0, x1, y1 = (int(v) for v in box)
        if x0 > x1:
            x0, x1 = x1, x0
        if y0 > y1:
            y0, y1 = y1, y0
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < self.image.w and 0 <= y < self.image.h:
                    self.image[x, y] = fill


class Image:
    @staticmethod
    def new(mode, size, color=None):
        channels = 4 if mode == "RGBA" else 3
        if color is None:
            color = (0, 0, 0, 0) if channels == 4 else (0, 0, 0)
        else:
            color = tuple(color)
            if channels == 4 and len(color) == 3:
                color = color + (255,)
        pixel = bytes(int(channel) & 255 for channel in color[:channels])
        return _Img(size[0], size[1], channels, pixel)


class ImageDraw:
    @staticmethod
    def Draw(image):
        return _Draw(image)

import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_dir = os.path.expanduser('~/e31-newapps/seeds/ps-2-21-ps-batch-process-files')
        os.makedirs(seed_dir, exist_ok=True)
        for i in range(4):
            img = Image.new('RGB', (32, 32), color=(50 + i * 20, 100, 150))
            img.save(os.path.join(seed_dir, f'image_{i+1}.jpg'))
        instructions = os.path.expanduser('~/e31-newapps/seeds/ps-2-21-ps-batch-process-files-instructions.txt')
        with open(instructions, 'w', encoding='utf-8') as f:
            f.write('对所有图像执行以下处理：\n1. 调整图像大小为 64×64 像素\n2. 转换为 PNG 格式\n3. 保存到输出文件夹')
        out_dir = os.path.expanduser('~/e31-newapps/out/ps-2-21-ps-batch-process-files')
        os.makedirs(out_dir, exist_ok=True)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(1)
        return {'status': 'completed', 'state': {}}
