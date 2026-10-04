"""Generate brand/icon.png and brand/icon@2x.png without external deps.

Draws a rounded-square gradient tile with a water drop and a small flame,
supersampled 4x for smooth edges, then writes a PNG using zlib.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

SS = 4  # supersample factor


def lerp(a, b, t):
    return a + (b - a) * t


def rounded_rect_alpha(x, y, w, h, r):
    cx = min(max(x, r), w - r)
    cy = min(max(y, r), h - r)
    dx = x - cx
    dy = y - cy
    d = (dx * dx + dy * dy) ** 0.5
    return 1.0 if d <= r else 0.0


def in_drop(x, y):
    cx, cy = 0.5, 0.56
    dx, dy = x - cx, y - cy
    if dx * dx + dy * dy <= 0.16 * 0.16:
        return True
    if 0.30 <= y <= 0.56:
        half = (y - 0.30) / (0.56 - 0.30) * 0.16
        if abs(x - 0.5) <= half:
            return True
    return False


def in_flame(x, y):
    cx, cy = 0.5, 0.60
    dx, dy = x - cx, y - cy
    if dx * dx + dy * dy <= 0.075 * 0.075:
        return True
    if 0.44 <= y <= 0.60:
        half = (0.60 - y) / (0.60 - 0.44) * 0.075
        if abs(x - 0.5) <= half:
            return True
    return False


def render(size: int):
    W = size * SS
    acc = [[[0, 0, 0, 0] for _ in range(size)] for _ in range(size)]

    for j in range(W):
        for i in range(W):
            nx = i / W
            ny = j / W
            a = rounded_rect_alpha(nx, ny, 1.0, 1.0, 0.22)
            if a <= 0:
                continue
            t = (nx + ny) / 2
            r = int(lerp(13, 20, t))
            g = int(lerp(42, 120, t))
            b = int(lerp(90, 160, t))
            if in_drop(nx, ny):
                r, g, b = 224, 244, 255
                if in_flame(nx, ny):
                    r, g, b = 255, 176, 32
            oi, oj = i // SS, j // SS
            c = acc[oj][oi]
            c[0] += r
            c[1] += g
            c[2] += b
            c[3] += int(a * 255)

    n = SS * SS
    return [[(c[0] // n, c[1] // n, c[2] // n, c[3] // n) for c in row] for row in acc]


def write_png(path: Path, px) -> None:
    size = len(px)
    raw = bytearray()
    for j in range(size):
        raw.append(0)
        for i in range(size):
            raw += bytes(px[j][i])

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    path.write_bytes(png)


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "brand"
    out.mkdir(exist_ok=True)
    write_png(out / "icon.png", render(256))
    write_png(out / "icon@2x.png", render(512))
    print("wrote", out / "icon.png", "and", out / "icon@2x.png")


if __name__ == "__main__":
    main()
