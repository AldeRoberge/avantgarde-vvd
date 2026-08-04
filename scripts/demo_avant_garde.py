"""Render the full AvantGarde SlashV specimen sheet."""
from __future__ import annotations

import os
import sys
import traceback

from PIL import Image, ImageDraw, ImageFont

import make_font
from logutil import log_path, setup_logging

log = setup_logging("demo")

ROOT = make_font.ROOT
OUT_DIR = make_font.OUT_DIR
IMAGES = os.path.join(ROOT, "images")

DEMO = "Ville de Val-d'Or"
SCALE = 2

BOOK = os.path.join(OUT_DIR, "AvantGardeSlashV-Book.ttf")
DEMI = os.path.join(OUT_DIR, "AvantGardeSlashV-Demi.ttf")
OBLQ = os.path.join(OUT_DIR, "AvantGardeSlashV-DemiOblique.ttf")

INK = "#111111"
GREY = "#9aa0a6"
ACCENT = "#0aa06e"
RULE = "#e2e5e9"


def s(n):
    return n * SCALE


def require_font(path: str, label: str) -> str:
    log_path(log, label, path)
    if not os.path.isfile(path):
        log.error("%s missing: %s", label, path)
        log.error("Run: python scripts/make_font.py")
        raise FileNotFoundError(path)
    return path


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    px = s(size)
    log.debug("ImageFont.truetype(%r, size=%d -> %dpx)", path, size, px)
    try:
        return ImageFont.truetype(path, px)
    except Exception:
        log.exception("failed to load font %s at size %s", path, px)
        raise


def main() -> int:
    log.info("avantgarde-vvd / demo_avant_garde.py")
    log.info("ROOT=%s  SCALE=%s  DEMO=%r", ROOT, SCALE, DEMO)
    log_path(log, "OUT_DIR", OUT_DIR)
    log_path(log, "IMAGES", IMAGES)

    try:
        orig_book = make_font.resolve_source("AVGARDN.TTF")
    except FileNotFoundError:
        log.exception("cannot resolve original Book font")
        return 1

    for path, label in [
        (BOOK, "Book output"),
        (DEMI, "Demi output"),
        (OBLQ, "Demi Oblique output"),
        (orig_book, "original Book"),
    ]:
        try:
            require_font(path, label)
        except FileNotFoundError:
            return 1

    W, H = 1500 * SCALE, 1360 * SCALE
    log.info("canvas %dx%d", W, H)
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    M = 80 * SCALE

    def f(path, size):
        return load_font(path, size)

    def rule(y):
        log.debug("rule at y=%s", y)
        d.line([(M, y), (W - M, y)], fill=RULE, width=max(1, s(2)))

    try:
        log.info("drawing header...")
        d.text((M, s(58)), "A V A N T G A R D E   S L A S H V", fill=ACCENT, font=f(DEMI, 22))
        d.text((M, s(96)), DEMO, fill=INK, font=f(DEMI, 118))
        d.text(
            (M, s(244)),
            "Custom AvantGarde - the V has a vertical left stroke",
            fill=GREY,
            font=f(BOOK, 30),
        )
        rule(s(310))

        log.info("drawing weights...")
        y = s(350)
        for label, path, size in [("Book", BOOK, 74), ("Demi", DEMI, 74), ("Demi Oblique", OBLQ, 74)]:
            log.debug("weight row %r from %s", label, path)
            d.text((M, y + s(22)), label, fill=ACCENT, font=f(BOOK, 24))
            d.text((M + s(240), y), DEMO, fill=INK, font=f(path, size))
            y += s(108)

        rule(y + s(20))

        log.info("drawing size ramp...")
        y += s(60)
        for size in (46, 34, 26, 20):
            d.text((M, y + s(46 - size) // 2), f"{size}px", fill=GREY, font=f(BOOK, 18))
            d.text((M + s(100), y), DEMO, fill=INK, font=f(BOOK, size))
            y += s(size + 26)

        rule(y + s(20))

        log.info("drawing before/after V...")
        y += s(55)
        d.text((M, y), "The V", fill=ACCENT, font=f(BOOK, 24))

        big_o = f(orig_book, 190)
        big_n = f(BOOK, 190)
        bx = M + s(240)
        d.text((bx, y - s(42)), "V", fill="#c9ced4", font=big_o)
        d.text((bx + s(160), y - s(42)), "V", fill=INK, font=big_n)

        d.text((bx, y + s(150)), "original", fill=GREY, font=f(BOOK, 20))
        d.text((bx + s(160), y + s(150)), "customized", fill=GREY, font=f(BOOK, 20))

        note = (
            "Left stroke is vertical; the right stroke leans 8 degrees\n"
            "further right than the original. Both strokes share the\n"
            "font's stem width so their top edges match in weight."
        )
        d.multiline_text((bx + s(420), y - s(10)), note, fill=GREY, font=f(BOOK, 26), spacing=s(12))
    except Exception:
        log.exception("error while drawing specimen")
        return 1

    os.makedirs(IMAGES, exist_ok=True)
    out = os.path.join(IMAGES, "demo_avant_garde.png")
    try:
        img.save(out, dpi=(144, 144), optimize=True)
    except Exception:
        log.exception("failed to save %s", out)
        return 1

    log_path(log, "wrote", out, level=20)
    log.info("demo_avant_garde.png ready (%dx%d)", W, H)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log.error("unhandled error:\n%s", traceback.format_exc())
        sys.exit(1)
