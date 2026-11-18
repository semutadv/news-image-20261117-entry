#!/usr/bin/env python3
"""The World in One Day - entry for make.fun contest news-image-20261117.

A program (Python 3, standard library only, no network) that draws one
1024x1024 front-page image summing up the world news of Tuesday
17 November 2026 and writes it to /output/entry.png (or to
$MAKEFUN_OUTPUT_DIR/entry.png when that variable is set).

Everything is drawn with code: a small rasteriser (rects, lines, circles,
polygons), simple flat illustrations for each story, and text rendered
from the glyph bitmaps in fontdata.py. The drawing uses only integer
arithmetic and a fixed zlib level, so two runs write identical bytes.

The day's stories (researched from the day's reporting; see SOURCES.md):
Ukraine drops a span of the Kerch Bridge; Iran fires drones at a U.S.
radar in Bahrain; Trump, Xi and Putin head for a Shenzhen summit;
tankers are mined in the Strait of Hormuz; Wall Street slides; Japan
scrambles jets against Russian aircraft - plus four one-line briefs.
"""

import os
import struct
import zlib

from fontdata import FONTS

W = 1024
H = 1024

PAPER = (246, 241, 230)
INK = (22, 24, 28)
RED = (176, 30, 38)
BLUE = (27, 66, 124)
AMBER = (190, 116, 18)
GREY = (110, 106, 96)
RULE = (60, 58, 52)
TINT = (236, 229, 211)
SKY = (203, 224, 240)
SEA = (70, 112, 148)
STEEL = (96, 106, 118)
SMOKE = (150, 148, 142)
ORANGE = (238, 128, 30)
YELLOW = (250, 196, 60)
WHITE = (252, 250, 244)

img = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        img[i] = c[0]
        img[i + 1] = c[1]
        img[i + 2] = c[2]


def rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        img[i:i + len(row)] = row


def hline(x, y, w, c, t=1):
    rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    rect(x, y, t, h, c)


def line(x0, y0, x1, y1, c, t=1):
    """Thick line: stamp filled discs along a Bresenham walk."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    r = max(0, (t - 1) // 2)
    while True:
        circle(x0, y0, r, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c):
    if r <= 0:
        px(cx, cy, c)
        return
    for yy in range(cy - r, cy + r + 1):
        d = yy - cy
        span = int((r * r - d * d) ** 0.5)
        rect(cx - span, yy, 2 * span + 1, 1, c)


def ring(cx, cy, r, c, t=2):
    steps = max(24, r * 4)
    for i in range(steps):
        a = 6.283185307 * i / steps
        x = int(cx + r * _cos(a))
        y = int(cy + r * _sin(a))
        circle(x, y, t // 2, c)


def arc(cx, cy, r, a0, a1, c, t=2):
    steps = max(12, r * 2)
    n = max(2, int(steps * abs(a1 - a0) / 6.283185307))
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        x = int(cx + r * _cos(a))
        y = int(cy + r * _sin(a))
        circle(x, y, t // 2, c)


def _sin(a):
    # deterministic small-angle-free sin/cos via math is fine too, but keep
    # to integer-friendly float math from the standard library.
    import math
    return math.sin(a)


def _cos(a):
    import math
    return math.cos(a)


def poly(points, c):
    """Filled polygon, even-odd scanline."""
    ys = [p[1] for p in points]
    y0 = max(0, min(ys))
    y1 = min(H - 1, max(ys))
    n = len(points)
    for yy in range(y0, y1 + 1):
        nodes = []
        for i in range(n):
            xa, ya = points[i]
            xb, yb = points[(i + 1) % n]
            if (ya <= yy < yb) or (yb <= yy < ya):
                nodes.append(xa + (yy - ya) * (xb - xa) / (yb - ya))
        nodes.sort()
        for i in range(0, len(nodes) - 1, 2):
            xa = int(nodes[i])
            xb = int(nodes[i + 1])
            if xb >= xa:
                rect(xa, yy, xb - xa + 1, 1, c)


# ---------------------------------------------------------------- text

def text_width(fkey, s, tracking=0):
    glyphs = FONTS[fkey]["glyphs"]
    w = 0
    for ch in s:
        w += glyphs[ch][0]
    if s:
        w += tracking * (len(s) - 1)
    return w


def draw_text(fkey, x, y_asc, s, c, tracking=0):
    """Draw s with the font's ascender line at y_asc; returns end x."""
    font = FONTS[fkey]
    glyphs = font["glyphs"]
    for ch in s:
        adv, w, h, bx, top, rows = glyphs[ch]
        if rows:
            gx = x + bx
            gy = y_asc + top
            for r, bits in enumerate(rows):
                yy = gy + r
                if yy < 0 or yy >= H:
                    continue
                b = bits
                xx = gx + w - 1
                while b:
                    if b & 1:
                        px(xx, yy, c)
                    b >>= 1
                    xx -= 1
        x += adv + tracking
    return x


def draw_text_centered(fkey, cx, y_asc, s, c, tracking=0):
    return draw_text(fkey, cx - text_width(fkey, s, tracking) // 2,
                     y_asc, s, c, tracking)


def draw_text_right(fkey, xr, y_asc, s, c, tracking=0):
    return draw_text(fkey, xr - text_width(fkey, s, tracking),
                     y_asc, s, c, tracking)


def wrap(fkey, s, maxw, tracking=0):
    words = s.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(fkey, trial, tracking) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def body_text(fkey, x, y_asc, s, maxw, lh, c, tracking=0):
    """Wrapped paragraph; returns the y just below the last line."""
    for ln in wrap(fkey, s, maxw, tracking):
        draw_text(fkey, x, y_asc, ln, c, tracking)
        y_asc += lh
    return y_asc


# ---------------------------------------------------------------- scenes

def draw_bridge(x, y, w, h):
    """Kerch Bridge: a span dropped into the sea, burst at the break."""
    rect(x, y, w, h, SKY)
    sea_y = y + int(h * 0.62)
    rect(x, sea_y, w, y + h - sea_y, SEA)
    for i in range(5):  # wave ticks
        wx = x + 14 + i * (w // 5)
        hline(wx, sea_y + 14 + (i % 3) * 12, 26, (120, 160, 190), 2)
    deck_y = y + int(h * 0.44)
    tower_x = x + int(w * 0.30)
    tower2_x = x + int(w * 0.78)
    # towers
    rect(tower_x, deck_y - 64, 10, 64 + (sea_y - deck_y), STEEL)
    rect(tower2_x, deck_y - 64, 10, 64 + (sea_y - deck_y), STEEL)
    # cables
    for tx in (tower_x + 5, tower2_x + 5):
        for fx in (0.06, 0.16, 0.55, 0.68, 0.94):
            line(tx, deck_y - 62, x + int(w * fx), deck_y, (70, 80, 94), 1)
    # deck: left part intact, right stub, middle span fallen
    rect(x, deck_y, int(w * 0.52), 9, STEEL)
    rect(tower2_x - 4, deck_y, x + w - tower2_x + 4, 9, STEEL)
    bx = x + int(w * 0.52)
    line(bx, deck_y + 4, x + int(w * 0.74), sea_y + 16, STEEL, 9)
    # explosion burst at the break
    cx, cy = bx + 4, deck_y - 6
    for dx, dy, ln in ((-16, -12, 12), (0, -20, 14), (16, -12, 12),
                       (-20, 2, 11), (20, 2, 11), (-8, -18, 10), (8, -18, 10)):
        line(cx, cy, cx + dx, cy + dy, ORANGE, 3)
    circle(cx, cy, 8, YELLOW)
    circle(cx, cy, 4, ORANGE)
    # smoke
    for sx, sy, sr in ((bx + 26, deck_y - 34, 12), (bx + 44, deck_y - 46, 9),
                       (bx + 12, deck_y - 48, 8)):
        circle(sx, sy, sr, SMOKE)
    # splash where the span lands
    for dx in (-8, 0, 8):
        line(x + int(w * 0.74) + dx, sea_y + 14, x + int(w * 0.74) + dx * 2,
             sea_y - 2, WHITE, 2)


def draw_drone(x, y, w, h):
    rect(x, y, w, h, TINT)
    cx, cy = x + w // 2, y + h // 2
    # radar dish on the right, signal arcs above it
    dish_x, dish_y = x + int(w * 0.80), y + int(h * 0.62)
    poly([(dish_x - 30, dish_y - 24), (dish_x + 2, dish_y - 30),
          (dish_x + 6, dish_y - 2), (dish_x - 24, dish_y + 6)], STEEL)
    line(dish_x - 24, dish_y - 22, dish_x - 2, dish_y - 4, INK, 2)
    line(dish_x - 11, dish_y + 4, dish_x - 11, y + h - 4, STEEL, 5)
    line(dish_x - 24, y + h - 4, dish_x + 2, y + h - 4, STEEL, 4)
    for r in (15, 24, 33):
        arc(dish_x - 12, dish_y - 12, r, -2.6, -1.1, BLUE, 3)
    # quadcopter drone, left of centre
    dx, dy = x + int(w * 0.30), y + int(h * 0.36)
    rect(dx - 17, dy - 8, 34, 16, INK)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        line(dx, dy, dx + sx * 30, dy + sy * 20, INK, 4)
        rect(dx + sx * 30 - 13, dy + sy * 20 - 2, 26, 4, INK)
    circle(dx, dy + 12, 4, RED)
    # motion dashes
    for i in range(3):
        hline(x + 8 + i * 4, dy - 26 + i * 10, 22, GREY, 2)


def draw_flags(x, y, w, h):
    rect(x, y, w, h, TINT)
    fw, fh = 74, 48
    xs = [x + 16, x + w // 2 - fw // 2, x + w - 16 - fw]
    base = y + h - 14
    for fx in xs:
        vline(fx - 3, y + 8, base - y - 8, STEEL, 3)
    # United States: stripes + blue canton
    fx = xs[0]
    for i in range(7):
        rect(fx, y + 10 + i * 7, fw, 4 if i % 2 == 0 else 3,
             RED if i % 2 == 0 else WHITE)
    rect(fx, y + 10, 32, 24, BLUE)
    for r in range(3):
        for cix in range(4):
            px(fx + 4 + cix * 8, y + 15 + r * 7, WHITE)
            px(fx + 5 + cix * 8, y + 15 + r * 7, WHITE)
    # China: red field, gold stars
    fx = xs[1]
    rect(fx, y + 10, fw, fh, RED)
    circle(fx + 13, y + 22, 5, YELLOW)
    for sx, sy in ((24, 14), (27, 21), (27, 29), (23, 34)):
        circle(fx + sx, y + sy, 2, YELLOW)
    # Russia: white / blue / red
    fx = xs[2]
    rect(fx, y + 10, fw, 16, WHITE)
    rect(fx, y + 26, fw, 16, BLUE)
    rect(fx, y + 42, fw, 16, RED)
    hline(x + 10, base, w - 20, RULE, 2)


def draw_tanker(x, y, w, h):
    rect(x, y, w, h, SKY)
    sea_y = y + int(h * 0.58)
    rect(x, sea_y, w, y + h - sea_y, SEA)
    hx, hy = x + 12, sea_y - 16
    hull_w = int(w * 0.62)
    poly([(hx, hy), (hx + hull_w, hy), (hx + hull_w - 18, hy + 20),
          (hx + 12, hy + 20)], (40, 44, 52))
    rect(hx + 8, hy - 10, hull_w - 60, 10, RED)
    for i in range(3):
        rect(hx + 14 + i * 34, hy - 22, 28, 12, (STEEL if i % 2 else AMBER))
    rect(hx + hull_w - 34, hy - 30, 20, 30, (40, 44, 52))
    # naval mine, right of the ship
    mx, my = x + int(w * 0.86), sea_y + 6
    circle(mx, my, 11, INK)
    for a in range(8):
        ang = 6.283185307 * a / 8
        line(mx, my, int(mx + 17 * _cos(ang)), int(my + 17 * _sin(ang)), INK, 3)
    circle(mx - 3, my - 3, 3, (90, 92, 96))
    for i in range(4):
        wx = x + 10 + i * (w // 4)
        hline(wx, sea_y + 22 + (i % 2) * 8, 24, (120, 160, 190), 2)


def draw_chart(x, y, w, h):
    rect(x, y, w, h, TINT)
    gx, gy = x + 10, y + 8
    gw, gh = w - 20, h - 16
    for i in range(1, 4):
        hline(gx, gy + gh * i // 4, gw, (205, 198, 178), 1)
    pts = [(gx + 2, gy + 8), (gx + gw // 4, gy + 14),
           (gx + gw // 2, gy + 10), (gx + (gw * 3) // 4, gy + gh // 2),
           (gx + gw - 4, gy + gh - 6)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 4)
    ex, ey = pts[-1]
    poly([(ex - 4, ey - 12), (ex + 10, ey - 4), (ex - 10, ey + 2)], RED)
    hline(gx, gy + gh, gw, RULE, 2)


def draw_jet(x, y, w, h):
    rect(x, y, w, h, TINT)
    circle(x + int(w * 0.88), y + int(h * 0.18), 11, RED)
    # fighter silhouette, nose to the right
    jx, jy = x + int(w * 0.08), y + int(h * 0.50)
    poly([(jx, jy + 6), (jx + 34, jy - 2), (jx + 62, jy - 12),
          (jx + 74, jy - 2), (jx + 104, jy + 2), (jx + 74, jy + 8),
          (jx + 46, jy + 10), (jx + 30, jy + 20), (jx + 22, jy + 10),
          (jx + 6, jy + 14)], INK)
    poly([(jx + 30, jy - 2), (jx + 44, jy - 16), (jx + 54, jy - 3)], INK)
    for i in range(3):
        hline(x + 4 + i * 3, jy - 12 + i * 12, 16 - i * 3, GREY, 2)


# ---------------------------------------------------------------- page

M = 30           # page margin
CW = W - 2 * M   # content width


def kicker(x, y_asc, s, c=RED):
    draw_text("sans15b", x, y_asc, s, c, tracking=1)


def panel_headline(x, y_asc, s, maxw=CW):
    lines = wrap("sans20", s, maxw)
    for ln in lines:
        draw_text("sans20", x, y_asc, ln, INK)
        y_asc += 25
    return y_asc


def build():
    rect(0, 0, W, H, PAPER)

    # ---- masthead
    hline(M, 16, CW, INK, 4)
    hline(M, 23, CW, INK, 1)
    draw_text_centered("serif58", W // 2, 34, "THE WORLD IN ONE DAY", INK)
    hline(M, 116, CW, INK, 1)
    hline(M, 121, CW, INK, 3)

    # ---- date strip
    rect(M, 132, CW, 42, RED)
    draw_text("sans24", M + 16, 141, "TUESDAY, 17 NOVEMBER 2026", WHITE)
    draw_text_right("sans15b", W - M - 16, 146, "LATE EDITION", WHITE,
                    tracking=2)

    # ---- hero: Kerch Bridge
    hy = 190
    kicker(M, hy, "UKRAINE WAR - CRIMEA")
    draw_text_right("sans15b", W - M, hy, "LEAD STORY", GREY, tracking=1)
    y = hy + 24
    for ln in ("UKRAINE BLOWS A SPAN OUT OF", "RUSSIA'S CRIMEA BRIDGE"):
        draw_text("sans40", M, y, ln, INK)
        y += 50
    hline(M, y + 6, CW, RULE, 2)
    iy = y + 20
    draw_bridge(M, iy, 486, 170)
    body_text("sans19", M + 512, iy + 4,
              "Zelenskyy hails an 'unprecedented operation,' weeks in the "
              "making, as a section of the Kerch Bridge drops into the sea. "
              "Moscow vows to rebuild it 'better than before' - and answers "
              "overnight by striking Kyiv's bridges, shutting the capital's "
              "Northern and Southern crossings.",
              CW - 512, 26, INK)

    # ---- row of three panels
    ry = 548
    hline(M, ry - 14, CW, RULE, 2)
    pw = 312
    xs = [M, M + pw + 14, M + 2 * (pw + 14)]
    vline(xs[1] - 7, ry, 240, (190, 182, 162), 1)
    vline(xs[2] - 7, ry, 240, (190, 182, 162), 1)

    draw_drone(xs[0], ry, pw, 66)
    kicker(xs[0], ry + 80, "MIDDLE EAST - BAHRAIN")
    yy = panel_headline(xs[0], ry + 102,
                        "IRAN FIRES DRONES AT U.S. RADAR IN BAHRAIN", pw)
    body_text("sans16", xs[0], yy + 4,
              "Bahrain says it intercepted the attack on Sheikh Isa base; "
              "no one hurt. U.S. intel alleges a Tehran 'dirty-bomb' plot "
              "against Trump aides.", pw, 21, INK)

    draw_flags(xs[1], ry, pw, 66)
    kicker(xs[1], ry + 80, "DIPLOMACY - SHENZHEN")
    yy = panel_headline(xs[1], ry + 102,
                        "TRUMP, XI, PUTIN TO MEET ON NUCLEAR RISKS", pw)
    body_text("sans16", xs[1], yy + 4,
              "Thursday's APEC summit in Shenzhen, China, pairs with "
              "Ukraine talks in Berlin the same day. Trump also floats "
              "meeting Kim Jong Un.", pw, 21, INK)

    draw_tanker(xs[2], ry, pw, 66)
    kicker(xs[2], ry + 80, "ENERGY - STRAIT OF HORMUZ")
    yy = panel_headline(xs[2], ry + 102,
                        "TANKERS MINED IN STRAIT OF HORMUZ", pw)
    body_text("sans16", xs[2], yy + 4,
              "Merchant ships hit naval mines in the oil chokepoint; "
              "drone alert at an Iraqi gas field. Brent tops $93.",
              pw, 21, INK)

    # ---- row of two panels
    ty = 800
    hline(M, ty - 12, CW, RULE, 2)
    tw = 476
    draw_chart(M, ty, 118, 92)
    kicker(M + 132, ty + 2, "MARKETS - NEW YORK")
    yy = panel_headline(M + 132, ty + 24,
                        "WALL STREET SLIDES: S&P BELOW ITS 200-DAY LINE",
                        tw - 132)
    body_text("sans16", M + 132, yy + 2,
              "Dow -846 pts, S&P -1.0%; VIX nears 27 before Nvidia "
              "earnings.", tw - 132, 21, INK)

    x2 = M + tw + 12
    draw_jet(x2, ty, 118, 92)
    kicker(x2 + 132, ty + 2, "ASIA-PACIFIC - JAPAN")
    yy = panel_headline(x2 + 132, ty + 24,
                        "JAPAN SCRAMBLES JETS OVER RUSSIAN AIRSPACE BREACH",
                        tw - 132)
    body_text("sans16", x2 + 132, yy + 2,
              "Tokyo protests the dawn violation; Seoul also scrambles "
              "jets.", tw - 132, 21, INK)

    # ---- briefs
    by = 924
    hline(M, by - 10, CW, INK, 3)
    draw_text("sans13b", M, by + 2, "ALSO TODAY", RED, tracking=1)
    draw_text_right("sans13b", W - M, by + 2,
                    "SOURCES: REUTERS - BBC - AP - CNN - WASHINGTON POST",
                    GREY)
    briefs = [
        ("EUROPE", "Five nations unveil a joint Rwanda return hub for "
                   "rejected asylum seekers."),
        ("WEST BANK", "Settlers kill a 72-year-old woman in Jericho; U.K. "
                      "sanctions eight settlement firms."),
        ("GENEVA", "128 nations weigh a treaty to ban lethal autonomous "
                   "weapons - 'killer robots'."),
        ("MONGOLIA", "President Khurelsukh says he will resign over a "
                     "$25M railway bribery claim."),
    ]
    yy = by + 22
    for lead, rest in briefs:
        x = draw_text("sans15b", M, yy, lead + " - ", RED)
        draw_text("sans15", x, yy, rest, INK)
        yy += 17


# ---------------------------------------------------------------- output

def png_bytes():
    raw = bytearray()
    rowlen = W * 3
    for yy in range(H):
        raw.append(0)
        raw += img[yy * rowlen:(yy + 1) * rowlen]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main():
    build()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(png_bytes())


if __name__ == "__main__":
    main()
