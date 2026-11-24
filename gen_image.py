#!/usr/bin/env python3
"""Deterministic 1024x1024 editorial news infographic for 23 November 2026."""

import math
import os

from PIL import Image, ImageDraw, ImageFont

# Render at 2x and downsample so circles, arcs and type look editorial.
SCALE = 2
SIZE = 1024 * SCALE
OUT_SIZE = 1024

BG = (14, 28, 44)  # #0e1c2c
PANEL = (22, 41, 63)
PANEL_EDGE = (46, 74, 104)
INK = (236, 240, 245)
MUTED = (168, 184, 200)
GOLD = (212, 186, 110)
RULE = (90, 112, 128)

BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Layout in 2x pixels.
MARGIN = 32 * SCALE
GAP = 20 * SCALE
GRID_TOP = 130 * SCALE
PANEL_W = 470 * SCALE
PANEL_H = 274 * SCALE
RADIUS = 14 * SCALE
PAD = 20 * SCALE
ICON = 58 * SCALE


def font(path, size):
    return ImageFont.truetype(path, size * SCALE)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def I(n):
    return int(round(n))


def box(*vals):
    return tuple(I(v) for v in vals)


def text_w(fnt, text):
    return fnt.getlength(text)


def wrap_words(text, fnt, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_w(fnt, trial) <= max_width:
            current = trial
            continue
        if current:
            lines.append(current)
        if text_w(fnt, word) <= max_width:
            current = word
            continue
        chunk = ""
        for ch in word:
            next_chunk = chunk + ch
            if chunk and text_w(fnt, next_chunk) > max_width:
                lines.append(chunk)
                chunk = ch
            else:
                chunk = next_chunk
        current = chunk
    if current:
        lines.append(current)
    return lines


def fit_wrap(text, path, max_size, min_size, max_width, max_lines):
    chosen = None
    for size in range(max_size, min_size - 1, -1):
        fnt = font(path, size)
        lines = wrap_words(text, fnt, max_width)
        if len(lines) <= max_lines:
            chosen = (fnt, size, lines)
            break
    if chosen is None:
        fnt = font(path, min_size)
        chosen = (fnt, min_size, wrap_words(text, fnt, max_width)[:max_lines])
    return chosen


def line_height(fnt, extra=0.28):
    ascent, descent = fnt.getmetrics()
    return int(ascent + descent + extra * (ascent + descent))


def draw_tracked(draw, text, cx, y, fnt, fill, tracking):
    width = sum(text_w(fnt, ch) for ch in text) + tracking * (len(text) - 1)
    x = cx - width / 2
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += text_w(fnt, ch) + tracking
    return width


def draw_lines(draw, lines, x, y, fnt, fill, spacing):
    cursor = y
    for line in lines:
        draw.text((x, cursor), line, font=fnt, fill=fill)
        cursor += spacing
    return cursor


def icon_globe(draw, cx, cy, s, color):
    cx, cy, s = I(cx), I(cy), I(s)
    r = I(s * 0.42)
    w = max(2, s // 18)
    draw.ellipse(box(cx - r, cy - r, cx + r, cy + r), outline=color, width=w)
    draw.ellipse(box(cx - r, cy - r // 3, cx + r, cy + r // 3), outline=color, width=max(2, w - 1))
    draw.ellipse(box(cx - r, cy - (r * 2) // 3, cx + r, cy + (r * 2) // 3), outline=color, width=max(1, w - 1))
    draw.line(box(cx, cy - r, cx, cy + r), fill=color, width=w)
    draw.arc(box(cx - r // 2, cy - r, cx + r // 2, cy + r), start=0, end=360, fill=color, width=max(2, w - 1))


def icon_ship(draw, cx, cy, s, color):
    cx, cy, s = I(cx), I(cy), I(s)
    hull = [
        (I(cx - s * 0.46), I(cy + s * 0.02)),
        (I(cx + s * 0.46), I(cy + s * 0.02)),
        (I(cx + s * 0.30), I(cy + s * 0.32)),
        (I(cx - s * 0.30), I(cy + s * 0.32)),
    ]
    draw.polygon(hull, fill=color)
    draw.rectangle(box(cx - s * 0.08, cy - s * 0.22, cx + s * 0.18, cy + s * 0.02), fill=color)
    draw.rectangle(box(cx + s * 0.02, cy - s * 0.36, cx + s * 0.12, cy - s * 0.22), fill=color)
    draw.line(box(cx + s * 0.07, cy - s * 0.36, cx + s * 0.07, cy - s * 0.46), fill=color, width=max(2, s // 20))
    wave_y = cy + s * 0.42
    for dx in (-0.38, -0.06, 0.26):
        x0 = cx + s * dx
        draw.arc(
            box(x0, wave_y - s * 0.08, x0 + s * 0.22, wave_y + s * 0.08),
            start=200,
            end=340,
            fill=color,
            width=max(2, s // 22),
        )
    tip = [
        (I(cx - s * 0.28), I(cy - s * 0.18)),
        (I(cx - s * 0.14), I(cy - s * 0.18)),
        (I(cx - s * 0.21), I(cy + s * 0.02)),
    ]
    draw.polygon(tip, fill=color)


def icon_chip(draw, cx, cy, s, color):
    cx, cy, s = I(cx), I(cy), I(s)
    r = I(s * 0.28)
    w = max(2, s // 18)
    draw.rounded_rectangle(box(cx - r, cy - r, cx + r, cy + r), radius=max(4, s // 16), outline=color, width=w)
    draw.rectangle(box(cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45), outline=color, width=max(2, w - 1))
    pin = max(3, s // 14)
    length = I(s * 0.10)
    for i in range(3):
        t = -r + r * (i + 1) / 2
        draw.rectangle(box(cx - r - length, cy + t - pin // 2, cx - r, cy + t + pin // 2), fill=color)
        draw.rectangle(box(cx + r, cy + t - pin // 2, cx + r + length, cy + t + pin // 2), fill=color)
        draw.rectangle(box(cx + t - pin // 2, cy - r - length, cx + t + pin // 2, cy - r), fill=color)
        draw.rectangle(box(cx + t - pin // 2, cy + r, cx + t + pin // 2, cy + r + length), fill=color)
    tri = [
        (I(cx), I(cy - r * 0.28)),
        (I(cx + r * 0.28), I(cy + r * 0.22)),
        (I(cx - r * 0.28), I(cy + r * 0.22)),
    ]
    draw.polygon(tri, fill=color)


def icon_flame(draw, cx, cy, s, color, core):
    cx, cy, s = I(cx), I(cy), I(s)
    r = s * 0.46
    outer = [
        (I(cx), I(cy - r)),
        (I(cx + r * 0.42), I(cy - r * 0.35)),
        (I(cx + r * 0.70), I(cy + r * 0.10)),
        (I(cx + r * 0.38), I(cy + r * 0.78)),
        (I(cx - r * 0.18), I(cy + r * 0.82)),
        (I(cx - r * 0.68), I(cy + r * 0.18)),
        (I(cx - r * 0.38), I(cy - r * 0.28)),
    ]
    draw.polygon(outer, fill=color)
    inner = [
        (I(cx + r * 0.02), I(cy - r * 0.12)),
        (I(cx + r * 0.22), I(cy + r * 0.18)),
        (I(cx + r * 0.08), I(cy + r * 0.55)),
        (I(cx - r * 0.16), I(cy + r * 0.55)),
        (I(cx - r * 0.20), I(cy + r * 0.18)),
    ]
    draw.polygon(inner, fill=core)


def icon_chart(draw, cx, cy, s, color):
    cx, cy, s = I(cx), I(cy), I(s)
    bars = (0.38, 0.62, 0.28, 0.48, 0.78)
    base = cy + s * 0.34
    left = cx - s * 0.38
    bw = s * 0.10
    gap = s * 0.06
    tops = []
    for i, h in enumerate(bars):
        x0 = left + i * (bw + gap)
        y0 = base - s * 0.70 * h
        draw.rounded_rectangle(box(x0, y0, x0 + bw, base), radius=max(2, s // 24), fill=color)
        tops.append((I(x0 + bw / 2), I(y0 - s * 0.04)))
    draw.line(tops, fill=mix(color, INK, 0.35), width=max(2, s // 18))
    last = tops[-1]
    draw.ellipse(box(last[0] - 4, last[1] - 4, last[0] + 4, last[1] + 4), fill=INK)


def icon_burst_ship(draw, cx, cy, s, color):
    cx, cy, s = I(cx), I(cy), I(s)
    n = 8
    r_out = s * 0.22
    r_in = s * 0.09
    bx, by = cx + s * 0.10, cy - s * 0.18
    pts = []
    for i in range(n * 2):
        ang = -math.pi / 2 + i * math.pi / n
        r = r_out if i % 2 == 0 else r_in
        pts.append((I(bx + r * math.cos(ang)), I(by + r * math.sin(ang))))
    draw.polygon(pts, fill=color)
    hull = [
        (I(cx - s * 0.42), I(cy + s * 0.06)),
        (I(cx + s * 0.36), I(cy + s * 0.06)),
        (I(cx + s * 0.22), I(cy + s * 0.32)),
        (I(cx - s * 0.28), I(cy + s * 0.32)),
    ]
    draw.polygon(hull, fill=color)
    draw.rectangle(box(cx - s * 0.12, cy - s * 0.10, cx + s * 0.10, cy + s * 0.06), fill=color)
    draw.line(box(cx - s * 0.46, cy + s * 0.42, cx + s * 0.42, cy + s * 0.42), fill=color, width=max(2, s // 20))


ICONS = {
    "CLIMATE": lambda d, x, y, s, c: icon_globe(d, x, y, s, c),
    "GULF": lambda d, x, y, s, c: icon_ship(d, x, y, s, c),
    "TECH": lambda d, x, y, s, c: icon_chip(d, x, y, s, c),
    "DISASTER": lambda d, x, y, s, c: icon_flame(d, x, y, s, c, (255, 214, 140)),
    "MARKETS": lambda d, x, y, s, c: icon_chart(d, x, y, s, c),
    "CONFLICT": lambda d, x, y, s, c: icon_burst_ship(d, x, y, s, c),
}

STORIES = [
    {
        "label": "CLIMATE",
        "color": (72, 186, 112),
        "headline": "COP31 Talks Collapse Over Fossil Fuels",
        "body": "Summit in Türkiye ends with no deal as the EU and others reject the draft text.",
    },
    {
        "label": "GULF",
        "color": (220, 72, 72),
        "headline": "Trump Threatens to Sink Iranian Vessels",
        "body": "US strikes a tanker exporting Iranian oil; attacks on Hormuz shipping hit a wartime high.",
    },
    {
        "label": "TECH",
        "color": (64, 204, 220),
        "headline": "Nvidia Brings Back Jensen Huang as CEO",
        "body": "The board reverses its abrupt dismissal after Trump intervenes; shares jump about 30%.",
    },
    {
        "label": "DISASTER",
        "color": (240, 152, 52),
        "headline": "Indonesia Factory Fire Kills 24",
        "body": "Candy factory blaze in Banten; rescuers keep searching for about 30 missing workers.",
    },
    {
        "label": "MARKETS",
        "color": (220, 186, 72),
        "headline": "Asia Steps In After AI Stock Sell-Off",
        "body": "Regulators in China, South Korea and Taiwan backstop markets; oil nears a three-month low.",
    },
    {
        "label": "CONFLICT",
        "color": (164, 108, 214),
        "headline": "Russian Warship Sunk off Libya",
        "body": "Suspected drone attack near Benghazi; Libya demands an explanation from Ukraine.",
    },
]


def draw_masthead(draw):
    cx = SIZE / 2
    kicker = "THE WORLD IN ONE PICTURE"
    kicker_font = font(SANS_PATH, 12)
    date_font = font(BOLD_PATH, 36)
    tracking = 5.4 * SCALE
    kicker_y = 28 * SCALE
    draw_tracked(draw, kicker, cx, kicker_y, kicker_font, GOLD, tracking)
    kicker_width = sum(text_w(kicker_font, ch) for ch in kicker) + tracking * (len(kicker) - 1)
    line_y = kicker_y + kicker_font.getmetrics()[0] * 0.62
    left_x1 = MARGIN + 8 * SCALE
    left_x2 = cx - kicker_width / 2 - 16 * SCALE
    right_x1 = cx + kicker_width / 2 + 16 * SCALE
    right_x2 = SIZE - MARGIN - 8 * SCALE
    draw.line((left_x1, line_y, left_x2, line_y), fill=RULE, width=SCALE)
    draw.line((right_x1, line_y, right_x2, line_y), fill=RULE, width=SCALE)

    date = "Monday 23 November 2026"
    date_y = 54 * SCALE
    dw = text_w(date_font, date)
    draw.text((cx - dw / 2, date_y), date, font=date_font, fill=INK)

    rule_y = 112 * SCALE
    draw.line((MARGIN, rule_y, SIZE - MARGIN, rule_y), fill=mix(GOLD, RULE, 0.45), width=SCALE)


def draw_label(draw, x, y, text, color):
    fnt = font(BOLD_PATH, 11)
    label = text
    pad_x = 9 * SCALE
    pad_y = 4 * SCALE
    w = text_w(fnt, label)
    h = line_height(fnt, extra=0.05)
    box = (x, y, x + w + pad_x * 2, y + h + pad_y)
    draw.rounded_rectangle(box, radius=5 * SCALE, fill=mix(PANEL, color, 0.22))
    draw.text((x + pad_x, y + pad_y // 2), label, font=fnt, fill=color)
    return box[3]


def draw_icon(draw, panel_x, panel_y, story):
    ix = panel_x + PANEL_W - PAD - ICON
    iy = panel_y + PANEL_H - PAD - ICON
    badge = mix(PANEL, story["color"], 0.18)
    draw.ellipse((ix, iy, ix + ICON, iy + ICON), fill=badge)
    ring = mix(story["color"], PANEL, 0.35)
    draw.ellipse((ix, iy, ix + ICON, iy + ICON), outline=ring, width=SCALE)
    ICONS[story["label"]](draw, ix + ICON / 2, iy + ICON / 2, ICON * 0.86, story["color"])


def draw_panel(draw, col, row, story):
    x = MARGIN + col * (PANEL_W + GAP)
    y = GRID_TOP + row * (PANEL_H + GAP)
    draw.rounded_rectangle((x, y, x + PANEL_W, y + PANEL_H), radius=RADIUS, fill=PANEL)
    draw.rounded_rectangle(
        (x, y, x + PANEL_W, y + PANEL_H), radius=RADIUS, outline=PANEL_EDGE, width=SCALE
    )
    accent = (x + 14 * SCALE, y + 8 * SCALE, x + 86 * SCALE, y + 12 * SCALE)
    draw.rounded_rectangle(accent, radius=2 * SCALE, fill=story["color"])

    inner_x = x + PAD
    inner_w = PANEL_W - PAD * 2
    label_bottom = draw_label(draw, inner_x, y + 18 * SCALE, story["label"], story["color"])

    head_top = label_bottom + 10 * SCALE
    head_font, _, head_lines = fit_wrap(
        story["headline"], BOLD_PATH, 20, 14, inner_w, 3
    )
    head_spacing = line_height(head_font, extra=0.12)
    body_top = draw_lines(draw, head_lines, inner_x, head_top, head_font, INK, head_spacing)
    body_top += 10 * SCALE

    # Keep the two summary lines clear of the corner icon.
    body_width = inner_w - ICON * 0.15
    body_font, _, body_lines = fit_wrap(
        story["body"], SANS_PATH, 13, 10, body_width, 2
    )
    body_spacing = line_height(body_font, extra=0.18)
    draw_lines(draw, body_lines, inner_x, body_top, body_font, MUTED, body_spacing)
    draw_icon(draw, x, y, story)


def main():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)
    draw_masthead(draw)
    for i, story in enumerate(STORIES):
        draw_panel(draw, i % 2, i // 2, story)
    out = img.resize((OUT_SIZE, OUT_SIZE), Image.Resampling.LANCZOS)
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    out.save(dest, format="PNG")


if __name__ == "__main__":
    main()
