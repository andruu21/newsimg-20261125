#!/usr/bin/env python3
"""Render the 25 November 2026 front page of "The Daily Ledger".

Everything the page contains lives in one PAGE spec at the bottom of the
file: masthead strings, the six stat boxes, three lead stories, five
briefs, the numbered "also today" list and the timed digest. Drawing
code is generic -- it only knows how to lay out those structures at
1024x1024 on ivory paper, entirely offline with Pillow.

Output: $MAKEFUN_OUTPUT_DIR/entry.png (falls back to /output/entry.png).
"""

import os
import sys
from datetime import date

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # renderer still copies the bundled PNG if Pillow is gone
    Image = ImageDraw = ImageFont = None

# ---------------------------------------------------------------- page frame

SIZE = 1024
EDGE = 24          # left/right page margin
SPACING = 12       # gap between columns
OUTDIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

INK = (28, 26, 24)        # body text and rules
RED = (156, 44, 38)       # kickers, numbers, accents
MUTED = (120, 112, 100)   # folios, ear text
PAPER = (244, 239, 226)   # page background
PANEL = (236, 229, 211)   # card fill
PANEL_RIM = (200, 191, 170)
ASH = (108, 106, 100)     # illustration grey
SURF = (60, 90, 108)      # sea band
DUNE = (222, 205, 168)    # desert band
HAZE = (198, 214, 222)    # sky band
BRASS = (150, 96, 66)

PUB_DAY = date(2026, 11, 25)

FONTS_DIR = "/usr/share/fonts/truetype"

# family -> candidate files, tried in order; first hit wins
FAMILIES = {
    "serif": ("dejavu/DejaVuSerif.ttf", "liberation/LiberationSerif-Regular.ttf"),
    "serif-bold": ("dejavu/DejaVuSerif-Bold.ttf", "liberation/LiberationSerif-Bold.ttf"),
    "serif-ital": ("dejavu/DejaVuSerif-Italic.ttf", "liberation/LiberationSerif-Italic.ttf"),
    "sans": ("liberation/LiberationSans-Regular.ttf",),
    "sans-bold": ("liberation/LiberationSans-Bold.ttf",),
    "mono": ("liberation/LiberationMono-Regular.ttf",),
    "mono-bold": ("liberation/LiberationMono-Bold.ttf",),
}

_fonts = {}


def typeface(family, px):
    """Memoised truetype loader; degrades to the bitmap default font."""
    slot = (family, px)
    if slot not in _fonts:
        path = next((os.path.join(FONTS_DIR, rel)
                     for rel in FAMILIES[family]
                     if os.path.exists(os.path.join(FONTS_DIR, rel))), None)
        if path:
            _fonts[slot] = ImageFont.truetype(path, px)
        else:
            try:
                _fonts[slot] = ImageFont.load_default(px)
            except Exception:
                _fonts[slot] = ImageFont.load_default()
    return _fonts[slot]


# ------------------------------------------------------------------ text kit

def fit_lines(pen, words, face, box_w):
    """Greedy wrap of `words` into lines that fit box_w pixels."""
    out, run = [], ""
    for w in words.split():
        cand = (run + " " + w).strip()
        if pen.textlength(cand, font=face) <= box_w:
            run = cand
        else:
            if run:
                out.append(run)
            run = w
    if run:
        out.append(run)
    return out


def paint_lines(pen, pos, lines, face, colour, lead=1.22, cap=None):
    """Stamp lines top-down; answer the y just past the last baseline."""
    x, y = pos
    if cap:
        lines = lines[:cap]
    for ln in lines:
        pen.text((x, y), ln, font=face, fill=colour)
        y += int(face.size * lead)
    return y


def paragraph(pen, pos, text, family, px, box_w, colour=INK, lead=1.22,
              cap=None):
    """Wrap then draw; returns the y below the block."""
    return paint_lines(pen, pos, fit_lines(pen, text, typeface(family, px),
                                            box_w), typeface(family, px),
                       colour, lead, cap)


def bar_h(pen, y, x_a, x_b, w=1, colour=INK):
    pen.rectangle([x_a, y, x_b, y + w - 1], fill=colour)


def bar_v(pen, x, y_a, y_b, w=1, colour=INK):
    pen.rectangle([x, y_a, x + w - 1, y_b], fill=colour)


def right_text(pen, y, text, face, colour):
    """Right-align a string against the page's right margin."""
    pen.text((SIZE - EDGE - pen.textlength(text, font=face), y), text,
             font=face, fill=colour)


def centre_text(pen, y, text, face, colour):
    pen.text(((SIZE - pen.textlength(text, font=face)) / 2, y), text,
             font=face, fill=colour)


def eyebrow(pen, x, y, text, colour=RED):
    """Small uppercase red label that opens a card or column."""
    pen.text((x, y), text.upper(), font=typeface("sans-bold", 11), fill=colour)


def big_head(pen, x, y, text, px, box_w, colour=INK, lead=1.08):
    return paragraph(pen, (x, y), text, "serif-bold", px, box_w, colour, lead)


# ------------------------------------------------------------------ sections

def head_masthead(pen):
    """Hairline, ear notes, title, strapline and the dateline strip."""
    bar_h(pen, 26, EDGE, SIZE - EDGE, 2)
    ear = typeface("serif-ital", 13)
    pen.text((EDGE, 34), "Vol. CXXVII, No. 214", font=ear, fill=MUTED)
    right_text(pen, 34, "Late Final Edition", ear, MUTED)

    centre_text(pen, 54, "THE DAILY LEDGER", typeface("serif-bold", 64), INK)
    centre_text(pen, 128,
                "INDEPENDENT SINCE 1899  \u00b7  WORLD, POLITICS, SCIENCE, MARKETS",
                typeface("sans", 12), MUTED)

    bar_h(pen, 152, EDGE, SIZE - EDGE, 2)
    dl = typeface("sans-bold", 14)
    dateline = PUB_DAY.strftime("%A, %d %B %Y").replace(" 0", " ", 1)
    pen.text((EDGE, 160), dateline.upper(), font=dl, fill=INK)
    right_text(pen, 160, "\u00a32.40  \u00b7  \u20ac2.80  \u00b7  $3.50", dl, INK)
    bar_h(pen, 184, EDGE, SIZE - EDGE, 1)


def head_stats(pen, y, cells):
    """One bordered strip of labelled numbers, divided by thin rules."""
    f_num, f_lab, f_sub = (typeface(*t) for t in
                           (("mono-bold", 17), ("sans-bold", 10), ("sans", 9)))
    x_a, x_b = EDGE, SIZE - EDGE
    span = (x_b - x_a) / len(cells)
    pen.rectangle([x_a, y, x_b, y + 58], outline=INK, width=1)
    for i, (label, value, note) in enumerate(cells):
        cx = x_a + span * i + 12
        pen.text((cx, y + 8), label, font=f_lab, fill=RED)
        pen.text((cx, y + 22), value, font=f_num, fill=INK)
        pen.text((cx, y + 43), note, font=f_sub, fill=MUTED)
        if i:
            bar_v(pen, int(x_a + span * i), y + 6, y + 52)
    return y + 58


def lead_frame(pen, x, y, w, h, eyebrow_txt, head_txt, body_txt, folio):
    """Card scaffolding shared by all three leads: panel + picture slot.

    Answers (picture_y, picture_h) so each story can paint its own scene.
    """
    pen.rectangle([x, y, x + w, y + h], fill=PANEL, outline=PANEL_RIM)
    pic_y, pic_h = y + 12, 96
    eyebrow(pen, x + 14, pic_y + pic_h + 20, eyebrow_txt)
    head_y = big_head(pen, x + 14, pic_y + pic_h + 38, head_txt, 20, w - 28)
    body_end = paragraph(pen, (x + 14, head_y + 6), body_txt, "serif", 12,
                         w - 28, INK, lead=1.26, cap=3)
    pen.text((x + 14, max(body_end + 4, y + h - 22)), folio,
             font=typeface("serif-ital", 11), fill=MUTED)
    return pic_y, pic_h


def lead_hormuz(pen, x, y, w, h):
    """Tankers burning in the strait: desert shore over dark water."""
    pic_y, pic_h = lead_frame(
        pen, x, y, w, h, "Middle East",
        "Two tankers hit naval mines, catch fire in Strait of Hormuz",
        "IRGC Navy said the ships took an unauthorised route; a third "
        "tanker burned overnight. Saudi forces down 4 drones over "
        "Ras Tanura as Houthi tension rises.",
        "Report, p. 4")
    pen.rectangle([x + 12, pic_y, x + w - 12, pic_y + pic_h],
                  fill=DUNE, outline=INK)
    water = pic_y + int(pic_h * 0.52)
    pen.rectangle([x + 12, water, x + w - 12, pic_y + pic_h],
                  fill=SURF, outline=INK)
    for frac, flame_h, burning in ((0.30, 26, True), (0.60, 20, True),
                                   (0.80, 0, False)):
        bow = x + 12 + int((w - 24) * frac)
        deck = water + 8
        pen.rectangle([bow - 12, deck, bow + 12, deck + 12],
                      fill=ASH, outline=INK)
        if burning:
            pen.polygon([(bow - 4, deck), (bow, deck - flame_h),
                         (bow + 4, deck)], fill=RED)
            pen.ellipse([bow - 8, deck - flame_h - 6, bow + 8,
                         deck - flame_h + 8], fill=(60, 50, 44))


def lead_huawei(pen, x, y, w, h):
    """Courthouse scene: scales of justice on a plinth."""
    pic_y, pic_h = lead_frame(
        pen, x, y, w, h, "US-Court",
        "Brooklyn jury convicts Huawei on 10 of 12 counts",
        "Bank and wire fraud, sanctions violations and trade-secret "
        "theft; acquitted of racketeering conspiracy after the "
        "months-long federal trial.",
        "Analysis, p. 6")
    pen.rectangle([x + 12, pic_y, x + w - 12, pic_y + pic_h],
                  fill=HAZE, outline=INK)
    pavement = pic_y + int(pic_h * 0.78)
    pen.rectangle([x + 12, pavement, x + w - 12, pic_y + pic_h], fill=ASH)
    wall_a = x + int((w - 24) * 0.30) + 12
    wall_b = x + int((w - 24) * 0.70) + 12
    pen.rectangle([wall_a, pavement - 78, wall_b, pavement],
                  fill=PAPER, outline=INK)
    mid = (wall_a + wall_b) // 2
    pen.polygon([(mid - 16, pavement), (mid + 16, pavement),
                 (mid, pavement - 26)], fill=PAPER, outline=INK)
    pen.line([(mid, pavement - 26), (mid, pavement - 46)], fill=INK, width=3)
    pen.line([(mid - 22, pavement - 46), (mid + 22, pavement - 46)],
             fill=INK, width=3)
    for arm in (mid - 22, mid + 22):
        pen.line([(arm, pavement - 46), (arm, pavement - 38)], fill=INK,
                 width=2)
        pen.arc([arm - 9, pavement - 44, arm + 9, pavement - 30], 0, 180,
                fill=INK, width=2)


def lead_ukraine(pen, x, y, w, h):
    """Bay scene: drone vector closing on a struck cargo ship."""
    pic_y, pic_h = lead_frame(
        pen, x, y, w, h, "Ukraine",
        "Zelenskyy: Ukraine hit Russian cargo ship in Gulf of Finland",
        "Kyiv claimed the weekend drone strike that left the "
        "sanctioned vessel ablaze; Putin calls retaliation against "
        "refinery attacks 'inevitable'.",
        "Report, p. 8")
    pen.rectangle([x + 12, pic_y, x + w - 12, pic_y + pic_h],
                  fill=HAZE, outline=INK)
    swell = pic_y + int(pic_h * 0.46)
    pen.rectangle([x + 12, swell, x + w - 12, pic_y + pic_h],
                  fill=SURF, outline=INK)
    hull = x + int((w - 24) * 0.62)
    base = swell + 10
    pen.rectangle([hull - 30, base, hull + 22, base + 16], fill=ASH,
                  outline=INK)
    pen.rectangle([hull - 6, base - 8, hull + 14, base], fill=ASH,
                  outline=INK)
    pen.polygon([(hull - 8, base - 8), (hull - 8, base - 30),
                 (hull + 2, base - 8)], fill=RED)
    drone_x = x + 16 + int((w - 32) * 0.15)
    drone_y = swell - 6
    pen.line([(drone_x, drone_y), (hull - 10, base + 4)], fill=PAPER, width=2)
    pen.ellipse([drone_x - 5, drone_y - 3, drone_x + 5, drone_y + 3],
                fill=INK)


def brief_row(pen, y, briefs):
    """Five same-sized brief cards spread across the page width."""
    n = len(briefs)
    gap = 8
    cw = (SIZE - 2 * EDGE - gap * (n - 1)) / n
    ch = 118
    for i, (tag, blurb) in enumerate(briefs):
        cx = int(EDGE + i * (cw + gap))
        pen.rectangle([cx, y, int(cx + cw), y + ch], fill=PANEL,
                      outline=PANEL_RIM)
        eyebrow(pen, cx + 10, y + 10, tag)
        paragraph(pen, (cx + 10, y + 32), blurb, "serif", 12, cw - 20, INK,
                  lead=1.3, cap=5)
        pen.line([(cx + 10, y + ch - 12), (cx + 22, y + ch - 12)],
                 fill=RED, width=2)
    return y + ch


def also_column(pen, x, y, w, entries):
    """Numbered short-story list under an 'ALSO TODAY' banner."""
    f_no, f_txt = typeface("mono-bold", 13), typeface("serif", 13)
    bar_h(pen, y, x, x + w, 2)
    pen.text((x, y + 8), "ALSO TODAY", font=typeface("sans-bold", 14),
             fill=RED)
    bar_h(pen, y + 30, x, x + w, 1)
    yy = y + 42
    for n, story in enumerate(entries, 1):
        pen.text((x, yy + 2), f"{n:02d}", font=f_no, fill=RED)
        for ln in fit_lines(pen, story, f_txt, w - 36)[:2]:
            pen.text((x + 36, yy), ln, font=f_txt, fill=INK)
            yy += int(13 * 1.35)
        yy += 11
    return yy


def glance_column(pen, x, y, w, schedule):
    """Right-hand timed digest under a 'DAY AT A GLANCE' banner."""
    bar_h(pen, y, x, x + w, 2)
    pen.text((x, y + 8), "DAY AT A GLANCE", font=typeface("sans-bold", 14),
             fill=RED)
    bar_h(pen, y + 30, x, x + w, 1)
    yy = y + 42
    f_t, f_d = typeface("mono-bold", 12), typeface("serif", 12)
    for stamp, blurb in schedule:
        pen.text((x, yy + 1), stamp, font=f_t, fill=RED)
        yy = paint_lines(pen, (x + 44, yy),
                         fit_lines(pen, blurb, f_d, w - 44), f_d, INK,
                         lead=1.3)
        yy += 10
    return yy


def foot_check(pen, y):
    """Footer stamp that re-derives the weekday from the calendar."""
    good = PUB_DAY == date(2026, 11, 25) and PUB_DAY.strftime("%A") == "Wednesday"
    stamp = (f"DATE CHECK: {PUB_DAY.isoformat()} \u00b7 "
             f"{PUB_DAY.strftime('%A')} \u00b7 "
             f"day {PUB_DAY.timetuple().tm_yday} of 2026 \u00b7 "
             f"{'OK' if good else 'MISMATCH'}")
    f = typeface("mono", 12)
    bar_h(pen, y, EDGE, SIZE - EDGE, 1)
    pen.text((EDGE, y + 8), stamp, font=f, fill=RED if good else ASH)
    right_text(pen, y + 8,
               "Rendered with Pillow \u00b7 offline \u00b7 deterministic",
               f, MUTED)


# --------------------------------------------------------- page copy (data)

STORIES = {
    "stats": [
        ("HORMUZ", "2", "tankers hit mines, on fire"),
        ("HUAWEI", "10/12", "counts guilty, Brooklyn jury"),
        ("COP31", "NO PACT", "talks collapse in Antalya"),
        ("MSCI WORLD", "-0.4%", "tariffs on 14 partners"),
        ("NVDA", "-5.9%", "AI rebound fizzles"),
        ("BRAZIL-ARG", "RECALLED", "ambassador pulled for good"),
    ],
    "leads": (lead_hormuz, lead_huawei, lead_ukraine),
    "briefs": [
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
    ],
    "also": [
        "Yemeni troops kill 27 Houthis in Taiz offensive.",
        "Rebel advance on Bunia, DR Congo, halted and reversed.",
        "US Army plans to detonate entire lead azide stockpile in Iowa.",
        "FAA ground stop at Chicago O'Hare after radar outage.",
        "Libyan naval officers die after Ukrainian drone strike.",
        "CAS overturns sports ruling in day's arbitration batch.",
    ],
    "digest": [
        ("03:10", "Two tankers ablaze in Hormuz after mine strikes."),
        ("09:00", "Brooklyn jury returns Huawei guilty verdicts."),
        ("13:40", "Zelenskyy confirms Gulf of Finland ship strike."),
        ("17:00", "MSCI world down 0.4% on tariff threat."),
        ("20:15", "Cartagena siege ends, all hostages freed."),
    ],
}


def compose(pen):
    """Paint the whole sheet, top band to footer."""
    head_masthead(pen)
    y = head_stats(pen, 196, STORIES["stats"])

    # lead trio, equal thirds
    top = y + 14
    lead_w = int((SIZE - 2 * EDGE - 2 * SPACING) / 3)
    lead_h = 292
    for i, painter in enumerate(STORIES["leads"]):
        painter(pen, EDGE + i * (lead_w + SPACING), top, lead_w, lead_h)
    y = top + lead_h

    # brief strip
    y = brief_row(pen, y + 14, STORIES["briefs"]) + 16

    # also-today (wide left) beside the digest (narrow right)
    left_w = int((SIZE - 2 * EDGE - 2 * SPACING) * 0.62)
    right_x = EDGE + left_w + 2 * SPACING
    also_column(pen, EDGE, y, left_w, STORIES["also"])
    glance_column(pen, right_x, y, SIZE - EDGE - right_x, STORIES["digest"])

    foot_check(pen, SIZE - 40)


def render():
    """Produce entry.png and answer the image."""
    sheet = Image.new("RGB", (SIZE, SIZE), PAPER)
    compose(ImageDraw.Draw(sheet))
    os.makedirs(OUTDIR, exist_ok=True)
    target = os.path.join(OUTDIR, "entry.png")
    sheet.save(target)
    return sheet


if __name__ == "__main__":
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")

    if Image is not None:
        try:
            page = render()
            print(f"wrote {dest} ({os.path.getsize(dest)} bytes, "
                  f"{page.size[0]}x{page.size[1]}, Pillow render)")
            sys.exit(0)
        except Exception as err:
            print(f"render failed ({err!r}); falling back to bundled "
                  f"entry.png", file=sys.stderr)

    # No Pillow (or render blew up): ship the committed image instead.
    import shutil
    bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "entry.png")
    shutil.copyfile(bundled, dest)
    print(f"wrote {dest} ({os.path.getsize(dest)} bytes, copied entry.png)")
