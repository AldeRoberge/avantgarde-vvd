"""Side-by-side comparison: AvantGarde SlashV vs Adventor SlashV."""
from __future__ import annotations

import os
import sys
import traceback

from PIL import Image, ImageDraw, ImageFont

import make_font
from logutil import log_path, setup_logging

log = setup_logging("demo_compare")

ROOT = make_font.ROOT
OUT_DIR = make_font.OUT_DIR
IMAGES = os.path.join(ROOT, "images")

DEMO = "Ville de Val-d'Or"
SCALE = 2

AG_BOOK = os.path.join(OUT_DIR, "AvantGardeSlashV-Book.ttf")
AG_DEMI = os.path.join(OUT_DIR, "AvantGardeSlashV-Demi.ttf")
AG_OBLQ = os.path.join(OUT_DIR, "AvantGardeSlashV-DemiOblique.ttf")

AD_REG = os.path.join(OUT_DIR, "AdventorSlashV-Regular.ttf")
AD_BOLD = os.path.join(OUT_DIR, "AdventorSlashV-Bold.ttf")
AD_ITAL = os.path.join(OUT_DIR, "AdventorSlashV-Italic.ttf")

INK = "#111111"
GREY = "#9aa0a6"
ACCENT = "#0aa06e"
RULE = "#e2e5e9"
MUTED = "#c9ced4"


def s(n: int) -> int:
    return n * SCALE


def require(path: str, how: str) -> None:
    if not os.path.isfile(path):
        log.error("Missing %s. Run: %s", path, how)
        raise FileNotFoundError(path)
    log_path(log, "Font", path)


def f(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, s(size))


def main() -> int:
    log.info("Building AvantGarde vs Adventor comparison sheet.")

    needed = [
        (AG_BOOK, "python scripts/make_font.py avantgarde"),
        (AG_DEMI, "python scripts/make_font.py avantgarde"),
        (AG_OBLQ, "python scripts/make_font.py avantgarde"),
        (AD_REG, "python scripts/make_font.py adventor"),
        (AD_BOLD, "python scripts/make_font.py adventor"),
        (AD_ITAL, "python scripts/make_font.py adventor"),
    ]
    try:
        for path, how in needed:
            require(path, how)
        ag_src = make_font.resolve_source("AVGARDN.TTF", make_font.FAMILIES["avantgarde"])
        ad_src = make_font.resolve_source(
            "texgyreadventor-regular.otf", make_font.FAMILIES["adventor"]
        )
    except FileNotFoundError:
        return 1

    W, H = s(1600), s(1280)
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    M = s(70)
    col_gap = s(40)
    col_w = (W - 2 * M - col_gap) // 2
    left_x = M
    right_x = M + col_w + col_gap

    def rule(y: int) -> None:
        d.line([(M, y), (W - M, y)], fill=RULE, width=max(1, s(2)))

    # Header
    d.text((M, s(48)), "S L A S H V   C O M P A R E", fill=ACCENT, font=f(AG_DEMI, 22))
    d.text((M, s(88)), DEMO, fill=INK, font=f(AG_DEMI, 96))
    d.text(
        (M, s(210)),
        "Same V treatment on two source families",
        fill=GREY,
        font=f(AG_BOOK, 28),
    )
    rule(s(270))

    # Column headers
    y = s(300)
    d.text((left_x, y), "AvantGarde SlashV", fill=ACCENT, font=f(AG_DEMI, 28))
    d.text((right_x, y), "Adventor SlashV", fill=ACCENT, font=f(AD_BOLD, 28))
    y += s(48)
    d.text((left_x, y), "from AvantGarde Bk BT", fill=GREY, font=f(AG_BOOK, 20))
    d.text((right_x, y), "from TeX Gyre Adventor", fill=GREY, font=f(AD_REG, 20))

    # Display line in each column
    y += s(70)
    d.text((left_x, y), DEMO, fill=INK, font=f(AG_DEMI, 56))
    d.text((right_x, y), DEMO, fill=INK, font=f(AD_BOLD, 56))

    # Weight rows
    y += s(100)
    rows = [
        ("Book / Regular", AG_BOOK, AD_REG),
        ("Demi / Bold", AG_DEMI, AD_BOLD),
        ("Oblique / Italic", AG_OBLQ, AD_ITAL),
    ]
    for label, ag_path, ad_path in rows:
        d.text((left_x, y), label.split(" / ")[0], fill=GREY, font=f(AG_BOOK, 18))
        d.text((right_x, y), label.split(" / ")[1], fill=GREY, font=f(AD_REG, 18))
        d.text((left_x, y + s(28)), DEMO, fill=INK, font=f(ag_path, 42))
        d.text((right_x, y + s(28)), DEMO, fill=INK, font=f(ad_path, 42))
        y += s(100)

    rule(y)
    y += s(40)

    # Big V pair for each family
    d.text((left_x, y), "The V", fill=ACCENT, font=f(AG_BOOK, 22))
    d.text((right_x, y), "The V", fill=ACCENT, font=f(AD_REG, 22))
    y += s(40)

    d.text((left_x, y), "V", fill=MUTED, font=f(ag_src, 160))
    d.text((left_x + s(150), y), "V", fill=INK, font=f(AG_BOOK, 160))
    d.text((right_x, y), "V", fill=MUTED, font=f(ad_src, 160))
    d.text((right_x + s(150), y), "V", fill=INK, font=f(AD_REG, 160))

    y += s(175)
    d.text((left_x, y), "original", fill=GREY, font=f(AG_BOOK, 18))
    d.text((left_x + s(150), y), "SlashV", fill=GREY, font=f(AG_BOOK, 18))
    d.text((right_x, y), "original", fill=GREY, font=f(AD_REG, 18))
    d.text((right_x + s(150), y), "SlashV", fill=GREY, font=f(AD_REG, 18))

    os.makedirs(IMAGES, exist_ok=True)
    out = os.path.join(IMAGES, "demo_compare.png")
    img.save(out, dpi=(144, 144), optimize=True)
    log.info("Saved comparison sheet to %s", out)
    log.info("Comparison sheet ready.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log.error("Something went wrong:\n%s", traceback.format_exc())
        sys.exit(1)
