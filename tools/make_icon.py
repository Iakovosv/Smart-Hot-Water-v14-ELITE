"""Generate brand assets for the GSW Smart Hot Water integration.

Produces, at the repo root ``brand/`` and inside
``custom_components/gsw_hotwater/brand/``:

    icon.png / icon@2x.png               square mark (light theme)
    dark_icon.png / dark_icon@2x.png     square mark (dark theme)
    logo.png / logo@2x.png               horizontal wordmark (light theme)
    dark_logo.png / dark_logo@2x.png     horizontal wordmark (dark theme)

The mark is a rounded-square water gradient tile with a white water drop and
an orange flame (hot water). Everything is drawn supersampled (4x) and then
downscaled with Lanczos for smooth edges.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SS = 4  # supersample factor
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

NAVY = (11, 42, 91)
BLUE = (30, 127, 194)
CYAN = (56, 182, 232)
DROP = (243, 251, 255)
DROP_SHADE = (198, 231, 252)
FLAME = (255, 159, 28)
FLAME_CORE = (255, 209, 102)

DARK_DROP = (143, 216, 255)
DARK_DROP_EDGE = (214, 240, 255)
TEXT_LIGHT = (18, 46, 92)
TEXT_LIGHT_2 = (52, 86, 132)
TEXT_DARK = (234, 246, 255)
TEXT_DARK_2 = (150, 202, 238)


def lerp(a, b, t):
    return int(round(a + (b - a) * t))


def lerp3(c1, c2, t):
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def diagonal_gradient(w: int, h: int, c1, c2) -> Image.Image:
    """Small diagonal gradient upscaled (cheap and smooth)."""
    small = Image.new("RGB", (64, 64))
    px = small.load()
    for y in range(64):
        for x in range(64):
            px[x, y] = lerp3(c1, c2, (x + y) / 126.0)
    return small.resize((w, h), Image.BILINEAR)


def rounded_mask(size: int, radius_ratio: float) -> Image.Image:
    """Alpha mask of a rounded square, at exactly ``size`` pixels."""
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=int(size * radius_ratio), fill=255
    )
    return mask


def draw_teardrop(dr: ImageDraw.ImageDraw, cx: float, cy: float, r: float,
                  tip: float, fill) -> None:
    """Union of a circle and the tangent cone from the tip = a teardrop."""
    d = max(cy - tip, r * 1.0001)
    half = max((d * d - r * r), 1.0) ** 0.5
    ty = cy - r * r / d
    dr.polygon([(cx, tip), (cx + r * half / d, ty), (cx - r * half / d, ty)], fill=fill)
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def draw_mark(img: Image.Image, size_px: int, cx: float, cy: float,
              mark_ratio: float, dark: bool) -> None:
    """Draw the drop+flame mark inside ``img`` at the given centre."""
    dr = ImageDraw.Draw(img)
    r = size_px * mark_ratio
    drop_cy = cy + r * 0.34
    tip = drop_cy - 2.10 * r
    if dark:
        draw_teardrop(dr, cx, drop_cy, r * 1.10, drop_cy - 2.10 * r * 1.10, DARK_DROP_EDGE)
        draw_teardrop(dr, cx, drop_cy, r, tip, DARK_DROP)
    else:
        draw_teardrop(dr, cx, drop_cy + r * 0.06, r * 1.06, tip, DROP_SHADE)
        draw_teardrop(dr, cx, drop_cy, r, tip, DROP)
    # flame
    fr = r * 0.46
    fcy = drop_cy + r * 0.34
    ftip = fcy - 2.05 * fr
    draw_teardrop(dr, cx, fcy, fr, ftip, FLAME)
    draw_teardrop(dr, cx, fcy + fr * 0.16, fr * 0.55, ftip + fr * 1.15, FLAME_CORE)


def render_icon(size: int, dark: bool) -> Image.Image:
    s = size * SS
    if dark:
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw_mark(img, s, s / 2, s / 2, 0.235, dark=True)
    else:
        bg = diagonal_gradient(s, s, NAVY, CYAN)
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        img.paste(bg, (0, 0), rounded_mask(s, 0.225))
        draw_mark(img, s, s / 2, s / 2, 0.235, dark=False)
    return img.resize((size, size), Image.LANCZOS)


def _fit_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def render_logo(w: int, h: int, dark: bool) -> Image.Image:
    s = SS
    W, H = w * s, h * s
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    mark_size = int(H * 0.66)
    mx, my = int(H * 0.14), (H - mark_size) // 2
    bg = diagonal_gradient(mark_size, mark_size, NAVY, CYAN)
    tile = Image.new("RGBA", (mark_size, mark_size), (0, 0, 0, 0))
    tile.paste(bg, (0, 0), rounded_mask(mark_size, 0.225))
    draw_mark(tile, mark_size, mark_size / 2, mark_size / 2, 0.235, dark=False)
    img.alpha_composite(tile, (mx, my))

    x0 = mx + mark_size + int(H * 0.13)
    t1 = TEXT_DARK if dark else TEXT_LIGHT
    t2 = TEXT_DARK_2 if dark else TEXT_LIGHT_2

    f1 = _fit_font(FONT_BOLD, int(H * 0.215))
    f2 = _fit_font(FONT_REG, int(H * 0.125))
    f3 = _fit_font(FONT_BOLD, int(H * 0.095))

    d = ImageDraw.Draw(img)
    b1 = d.textbbox((0, 0), "GSW", font=f1)
    b2 = d.textbbox((0, 0), "Smart Hot Water", font=f2)
    b3 = d.textbbox((0, 0), "ELITE", font=f3)
    gap = int(H * 0.045)
    block_h = (b1[3] - b1[1]) + gap + (b2[3] - b2[1])
    y = (H - block_h) // 2 - b1[1]
    d.text((x0, y), "GSW", font=f1, fill=t1)

    # ELITE badge after "GSW" on the first line
    bw, bh = b3[2] - b3[0], b3[3] - b3[1]
    bx = x0 + (b1[2] - b1[0]) + int(H * 0.035)
    by = y + b1[1] + (b1[3] - b1[1]) - bh - int(H * 0.004)
    pad_x, pad_y = int(H * 0.030), int(H * 0.016)
    d.rounded_rectangle(
        [bx - pad_x, by - pad_y, bx + bw + pad_x, by + bh + pad_y],
        radius=int(H * 0.040), fill=BLUE if not dark else (36, 120, 180),
    )
    d.text((bx, by), "ELITE", font=f3, fill=(255, 255, 255))

    y2 = y + (b1[3] - b1[1]) + gap - b2[1]
    d.text((x0, y2), "Smart Hot Water", font=f2, fill=t2)

    return img.resize((w, h), Image.LANCZOS)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    targets = [root / "brand", root / "custom_components" / "gsw_hotwater" / "brand"]

    assets = {
        "icon.png": render_icon(256, dark=False),
        "icon@2x.png": render_icon(512, dark=False),
        "dark_icon.png": render_icon(256, dark=True),
        "dark_icon@2x.png": render_icon(512, dark=True),
        "logo.png": render_logo(512, 256, dark=False),
        "logo@2x.png": render_logo(1024, 512, dark=False),
        "dark_logo.png": render_logo(512, 256, dark=True),
        "dark_logo@2x.png": render_logo(1024, 512, dark=True),
    }
    for d in targets:
        d.mkdir(parents=True, exist_ok=True)
        for name, im in assets.items():
            im.save(d / name)
        print("wrote", len(assets), "files to", d)


if __name__ == "__main__":
    main()
