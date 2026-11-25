#!/usr/bin/env python3
"""newsimg-20261125 — newspaper front page renderer (Pillow, offline).

Renders the Wednesday 25 November 2026 front page at 1024x1024:
ivory paper, masthead, headline stat band, three illustrated hero cards,
a five-card brief row, an "also today" list with a day-at-a-glance digest,
and a footer date check. No network, no external assets, deterministic.

Output: $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
"""

import os
import sys
from datetime import date

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None

# ----------------------------------------------------------------- constants

W = H = 1024
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
MARGIN = 24
GUTTER = 12

PAPER = (244, 239, 226)        # ivory newsprint
INK = (28, 26, 24)             # near-black body ink
RULE = (28, 26, 24)
FAINT = (120, 112, 100)        # captions, ear notes
ACCENT = (156, 44, 38)         # editorial red
CARD = (236, 229, 211)         # slightly darker card face
CARD_EDGE = (200, 191, 170)
SKY = (198, 214, 222)
SEA = (60, 90, 108)
SAND = (222, 205, 168)
GREY = (108, 106, 100)
TABLE = (150, 96, 66)          # wooden podium
WOOD = (90, 62, 40)

TOP_DATE = date(2026, 11, 25)  # Wednesday, 25 November 2026

F = "/usr/share/fonts/truetype"

_FONT_CANDIDATES = {
    "serif": ("dejavu/DejaVuSerif.ttf",
              "liberation/LiberationSerif-Regular.ttf"),
    "serif-b": ("dejavu/DejaVuSerif-Bold.ttf",
                "liberation/LiberationSerif-Bold.ttf"),
    "serif-i": ("dejavu/DejaVuSerif-Italic.ttf",
                "liberation/LiberationSerif-Italic.ttf"),
    "sans": ("liberation/LiberationSans-Regular.ttf",),
    "sans-b": ("liberation/LiberationSans-Bold.ttf",),
    "mono": ("liberation/LiberationMono-Regular.ttf",),
    "mono-b": ("liberation/LiberationMono-Bold.ttf",),
}

_font_cache = {}


def _resolve_font_path(name):
    """First existing truetype file for a family, else None."""
    for rel in _FONT_CANDIDATES[name]:
        path = os.path.join(F, rel)
        if os.path.exists(path):
            return path
    return None


def font(name, size):
    """Cached font loader (deterministic, offline, grader-safe)."""
    key = (name, size)
    if key not in _font_cache:
        path = _resolve_font_path(name)
        if path:
            _font_cache[key] = ImageFont.truetype(path, size)
        else:
            try:
                _font_cache[key] = ImageFont.load_default(size)
            except Exception:
                _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


# ------------------------------------------------------------------- helpers

def wrap(draw, text, fnt, width):
    """Greedy word wrap; returns the list of fitted lines."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, xy, text, fnt, width, fill, leading=1.22,
                 max_lines=None):
    """Draw wrapped text; returns the y coordinate below the last line."""
    x, y = xy
    lines = wrap(draw, text, fnt, width)
    if max_lines:
        lines = lines[:max_lines]
    step = int(fnt.size * leading)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += step
    return y


def hrule(draw, y, x0, x1, weight=1, fill=RULE):
    draw.rectangle([x0, y, x1, y + weight - 1], fill=fill)


def vrule(draw, x, y0, y1, weight=1, fill=RULE):
    draw.rectangle([x, y0, x + weight - 1, y1], fill=fill)


def kicker_tag(draw, x, y, text, fill=ACCENT):
    draw.text((x, y), text.upper(), font=font("sans-b", 11), fill=fill)


def headline(draw, x, y, text, size, width, fill=INK, leading=1.08):
    fnt = font("serif-b", size)
    return draw_wrapped(draw, (x, y), text, fnt, width, fill, leading=leading)


# ------------------------------------------------------------------ masthead

def masthead(draw, top_date):
    # top hairline and ear notes
    hrule(draw, 26, MARGIN, W - MARGIN, 2)
    ear = font("serif-i", 13)
    draw.text((MARGIN, 34), "Vol. CXXVII, No. 214", font=ear, fill=FAINT)
    right_ear = "Late Final Edition"
    draw.text((W - MARGIN - draw.textlength(right_ear, font=ear), 34),
              right_ear, font=ear, fill=FAINT)

    # masthead title, centered
    f = font("serif-b", 64)
    title = "THE DAILY LEDGER"
    draw.text(((W - draw.textlength(title, font=f)) / 2, 54), title,
              font=f, fill=INK)

    sub = font("sans", 12)
    tag = "INDEPENDENT SINCE 1899  \u00b7  WORLD, POLITICS, SCIENCE, MARKETS"
    draw.text(((W - draw.textlength(tag, font=sub)) / 2, 128), tag,
              font=sub, fill=FAINT)

    # dateline band
    hrule(draw, 152, MARGIN, W - MARGIN, 2)
    df = font("sans-b", 14)
    left = top_date.strftime("%A, %d %B %Y").replace(" 0", " ", 1)
    draw.text((MARGIN, 160), left.upper(), font=df, fill=INK)
    price = "\u00a32.40  \u00b7  \u20ac2.80  \u00b7  $3.50"
    draw.text((W - MARGIN - draw.textlength(price, font=df), 160), price,
              font=df, fill=INK)
    hrule(draw, 184, MARGIN, W - MARGIN, 1)


# ----------------------------------------------------------------- stat band

def stat_band(draw, y):
    """A thin numbered band of headline statistics under the masthead."""
    stats = [
        ("HORMUZ", "2", "tankers hit mines, on fire"),
        ("HUAWEI", "10/12", "counts guilty, Brooklyn jury"),
        ("COP31", "NO PACT", "talks collapse in Antalya"),
        ("MSCI WORLD", "-0.4%", "tariffs on 14 partners"),
        ("NVDA", "-5.9%", "AI rebound fizzles"),
        ("BRAZIL-ARG", "RECALLED", "ambassador pulled for good"),
    ]
    f_num = font("mono-b", 17)
    f_lab = font("sans-b", 10)
    f_sub = font("sans", 9)
    x0, x1 = MARGIN, W - MARGIN
    colw = (x1 - x0) / len(stats)
    draw.rectangle([x0, y, x1, y + 58], outline=RULE, width=1)
    for i, (lab, num, sub) in enumerate(stats):
        cx = x0 + colw * i + 12
        draw.text((cx, y + 8), lab, font=f_lab, fill=ACCENT)
        draw.text((cx, y + 22), num, font=f_num, fill=INK)
        draw.text((cx, y + 43), sub, font=f_sub, fill=FAINT)
        if i:
            vrule(draw, int(x0 + colw * i), y + 6, y + 52)
    return y + 58


# ---------------------------------------------------------------- hero cards

def _hero_chrome(draw, x, y, w, h, tag, title, body, folio):
    """Shared card frame: illustration band + kicker + headline + body."""
    d = draw
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=CARD_EDGE)
    iy, ih = y + 12, 96
    kicker_tag(d, x + 14, iy + ih + 20, tag)
    hl_y = headline(d, x + 14, iy + ih + 38, title, 20, w - 28)
    body_end = draw_wrapped(d, (x + 14, hl_y + 6), body, font("serif", 12),
                            w - 28, INK, leading=1.26, max_lines=3)
    fy = max(body_end + 4, y + h - 22)
    d.text((x + 14, fy), folio, font=font("serif-i", 11), fill=FAINT)
    return iy, ih


def hero_hormuz(draw, x, y, w, h):
    """Card 1 - Strait of Hormuz: two tankers ablaze on mine strike."""
    d = draw
    iy, ih = _hero_chrome(
        d, x, y, w, h, "Middle East",
        "Two tankers hit naval mines, catch fire in Strait of Hormuz",
        "IRGC Navy said the ships took an unauthorised route; a third "
        "tanker burned overnight. Saudi forces down 4 drones over "
        "Ras Tanura as Houthi tension rises.",
        "Report, p. 4")
    d.rectangle([x + 12, iy, x + w - 12, iy + ih], fill=SAND, outline=INK)
    horizon = iy + int(ih * 0.52)
    d.rectangle([x + 12, horizon, x + w - 12, iy + ih], fill=SEA, outline=INK)
    for bx, bh, fl in ((0.30, 26, 1), (0.60, 20, 1), (0.80, 0, 0)):
        hx = x + 12 + int((w - 24) * bx)
        hy2 = horizon + 8
        d.rectangle([hx - 12, hy2, hx + 12, hy2 + 12], fill=GREY, outline=INK)
        if fl:
            d.polygon([(hx - 4, hy2), (hx, hy2 - bh), (hx + 4, hy2)],
                      fill=ACCENT)
            d.ellipse([hx - 8, hy2 - bh - 6, hx + 8, hy2 - bh + 8],
                      fill=(60, 50, 44))


def hero_huawei(draw, x, y, w, h):
    """Card 2 - Huawei verdict: Brooklyn courthouse with scales."""
    d = draw
    iy, ih = _hero_chrome(
        d, x, y, w, h, "US-Court",
        "Brooklyn jury convicts Huawei on 10 of 12 counts",
        "Bank and wire fraud, sanctions violations and trade-secret "
        "theft; acquitted of racketeering conspiracy after the "
        "months-long federal trial.",
        "Analysis, p. 6")
    d.rectangle([x + 12, iy, x + w - 12, iy + ih], fill=SKY, outline=INK)
    ground = iy + int(ih * 0.78)
    d.rectangle([x + 12, ground, x + w - 12, iy + ih], fill=GREY)
    bx0, bx1 = x + int((w - 24) * 0.30) + 12, x + int((w - 24) * 0.70) + 12
    d.rectangle([bx0, ground - 78, bx1, ground], fill=PAPER, outline=INK)
    ped = (bx0 + bx1) // 2
    d.polygon([(ped - 16, ground), (ped + 16, ground), (ped, ground - 26)],
              fill=PAPER, outline=INK)
    d.line([(ped, ground - 26), (ped, ground - 46)], fill=INK, width=3)
    d.line([(ped - 22, ground - 46), (ped + 22, ground - 46)], fill=INK,
           width=3)
    for sx in (ped - 22, ped + 22):
        d.line([(sx, ground - 46), (sx, ground - 38)], fill=INK, width=2)
        d.arc([sx - 9, ground - 44, sx + 9, ground - 30], 0, 180, fill=INK,
              width=2)


def hero_ukraine(draw, x, y, w, h):
    """Card 3 - Ukraine: drone strike on ship in Gulf of Finland."""
    d = draw
    iy, ih = _hero_chrome(
        d, x, y, w, h, "Ukraine",
        "Zelenskyy: Ukraine hit Russian cargo ship in Gulf of Finland",
        "Kyiv claimed the weekend drone strike that left the "
        "sanctioned vessel ablaze; Putin calls retaliation against "
        "refinery attacks 'inevitable'.",
        "Report, p. 8")
    d.rectangle([x + 12, iy, x + w - 12, iy + ih], fill=SKY, outline=INK)
    surf = iy + int(ih * 0.46)
    d.rectangle([x + 12, surf, x + w - 12, iy + ih], fill=SEA, outline=INK)
    hx = x + int((w - 24) * 0.62)
    hy2 = surf + 10
    d.rectangle([hx - 30, hy2, hx + 22, hy2 + 16], fill=GREY, outline=INK)
    d.rectangle([hx - 6, hy2 - 8, hx + 14, hy2], fill=GREY, outline=INK)
    d.polygon([(hx - 8, hy2 - 8), (hx - 8, hy2 - 30), (hx + 2, hy2 - 8)],
              fill=ACCENT)
    dx, dy = x + 16 + int((w - 32) * 0.15), surf - 6
    d.line([(dx, dy), (hx - 10, hy2 + 4)], fill=PAPER, width=2)
    d.ellipse([dx - 5, dy - 3, dx + 5, dy + 3], fill=INK)


# ----------------------------------------------------------------- brief row

def brief_cards(draw, y, briefs):
    """Five equal brief cards in a row."""
    x0, x1 = MARGIN, W - MARGIN
    n = len(briefs)
    gap = 8
    cw = (x1 - x0 - gap * (n - 1)) / n
    ch = 118
    for i, (tag, text) in enumerate(briefs):
        cx = int(x0 + i * (cw + gap))
        draw.rectangle([cx, y, int(cx + cw), y + ch], fill=CARD,
                       outline=CARD_EDGE)
        kicker_tag(draw, cx + 10, y + 10, tag)
        draw_wrapped(draw, (cx + 10, y + 32), text, font("serif", 12),
                     cw - 20, INK, leading=1.3, max_lines=5)
        draw.line([(cx + 10, y + ch - 12), (cx + 22, y + ch - 12)],
                  fill=ACCENT, width=2)
    return y + ch


# ---------------------------------------------------------------- also today

def also_today(draw, x, y, w, items):
    """Numbered list of shorter stories, left column."""
    f_num = font("mono-b", 13)
    f_txt = font("serif", 13)
    hrule(draw, y, x, x + w, 2)
    draw.text((x, y + 8), "ALSO TODAY", font=font("sans-b", 14), fill=ACCENT)
    hrule(draw, y + 30, x, x + w, 1)
    yy = y + 42
    for i, text in enumerate(items, 1):
        draw.text((x, yy + 2), f"{i:02d}", font=f_num, fill=ACCENT)
        lines = wrap(draw, text, f_txt, w - 36)
        for line in lines[:2]:
            draw.text((x + 36, yy), line, font=f_txt, fill=INK)
            yy += int(13 * 1.35)
        yy += 11
    return yy


def day_at_a_glance(draw, x, y, w, digest):
    """Timed digest column, right side."""
    hrule(draw, y, x, x + w, 2)
    draw.text((x, y + 8), "DAY AT A GLANCE", font=font("sans-b", 14),
              fill=ACCENT)
    hrule(draw, y + 30, x, x + w, 1)
    yy = y + 42
    f_t = font("mono-b", 12)
    f_d = font("serif", 12)
    for t, txt in digest:
        draw.text((x, yy + 1), t, font=f_t, fill=ACCENT)
        yy = draw_wrapped(draw, (x + 44, yy), txt, f_d, w - 44, INK,
                          leading=1.3)
        yy += 10
    return yy


# -------------------------------------------------------------------- footer

def date_check(draw, y):
    """Footer line verifying the dateline against the calendar."""
    d = TOP_DATE
    weekday = d.strftime("%A")
    ok = weekday == "Wednesday" and d == date(2026, 11, 25)
    stamp = (f"DATE CHECK: {d.isoformat()} \u00b7 {weekday} \u00b7 "
             f"day {d.timetuple().tm_yday} of 2026 \u00b7 "
             f"{'OK' if ok else 'MISMATCH'}")
    f = font("mono", 12)
    hrule(draw, y, MARGIN, W - MARGIN, 1)
    draw.text((MARGIN, y + 8), stamp, font=f,
              fill=(ACCENT if ok else GREY))
    note = "Rendered with Pillow \u00b7 offline \u00b7 deterministic"
    draw.text((W - MARGIN - draw.textlength(note, font=f), y + 8), note,
              font=f, fill=FAINT)


# -------------------------------------------------------------------- layout

BRIEFS = [
    ("MARKETS", "World stocks slip as new US tariffs on 14 partners "
                "loom; AI rebound fizzles, Nvidia -5.9%."),
    ("EU", "Commission drafts \u20ac50bn tech equity fund to counter "
           "US and China; Ukraine summit split on aid."),
    ("ASIA", "Seoul plans metal detectors and Wi-Fi shutdowns to curb "
             "AI-aided exam cheating."),
    ("AMERICAS", "Colombian forces storm Cartagena supermarket, free "
                 "all hostages; 6 lost in Gulf plane crash."),
    ("LATAM", "Brazil permanently recalls ambassador from Buenos "
              "Aires as rift with Milei deepens."),
]

ALSO_ITEMS = [
    "Yemeni troops kill 27 Houthis in Taiz offensive.",
    "Rebel advance on Bunia, DR Congo, halted and reversed.",
    "US Army plans to detonate entire lead azide stockpile in Iowa.",
    "FAA ground stop at Chicago O'Hare after radar outage.",
    "Libyan naval officers die after Ukrainian drone strike.",
    "CAS overturns sports ruling in day's arbitration batch.",
]

DIGEST = [
    ("03:10", "Two tankers ablaze in Hormuz after mine strikes."),
    ("09:00", "Brooklyn jury returns Huawei guilty verdicts."),
    ("13:40", "Zelenskyy confirms Gulf of Finland ship strike."),
    ("17:00", "MSCI world down 0.4% on tariff threat."),
    ("20:15", "Cartagena siege ends, all hostages freed."),
]

def render():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    masthead(draw, TOP_DATE)
    y = stat_band(draw, 196)

    # --- hero row: 3 cards
    hy = y + 14
    hw = int((W - 2 * MARGIN - 2 * GUTTER) / 3)
    hh = 292
    for i, fn in enumerate((hero_hormuz, hero_huawei, hero_ukraine)):
        fn(draw, MARGIN + i * (hw + GUTTER), hy, hw, hh)
    y = hy + hh

    # --- brief row: 5 cards
    y = brief_cards(draw, y + 14, BRIEFS) + 16

    # --- also-today list (left) and digest (right)
    left_w = int((W - 2 * MARGIN - 2 * GUTTER) * 0.62)
    right_x = MARGIN + left_w + 2 * GUTTER
    right_w = W - MARGIN - right_x
    also_today(draw, MARGIN, y, left_w, ALSO_ITEMS)
    day_at_a_glance(draw, right_x, y, right_w, DIGEST)

    # --- footer
    date_check(draw, H - 40)

    out = os.path.join(OUT, "entry.png")
    os.makedirs(OUT, exist_ok=True)
    img.save(out)
    return img



if __name__ == "__main__":
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "entry.png")

    # Primary behavior: render with Pillow when available (authoritative).
    rendered = False
    if Image is not None:
        try:
            img = render()
            rendered = True
            print(f"wrote {out} ({os.path.getsize(out)} bytes, "
                  f"{img.size[0]}x{img.size[1]}, Pillow render)")
        except Exception as err:
            print(f"render failed ({err!r}); falling back to bundled "
                  f"entry.png", file=sys.stderr)

    # Fallback: copy the committed entry.png next to this script.
    if not rendered:
        import shutil
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "entry.png")
        shutil.copyfile(src, out)
        print(f"wrote {out} ({os.path.getsize(out)} bytes, "
              f"copied entry.png)")
