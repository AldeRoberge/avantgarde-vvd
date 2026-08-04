"""Render Adventor SlashV specimen (Ville de Val-d'Or)."""
from __future__ import annotations

import os
import sys
import traceback

from PIL import Image, ImageDraw, ImageFont

import make_font
from logutil import log_path, setup_logging

log = setup_logging("demo_adventor")

ROOT = make_font.ROOT
OUT_DIR = make_font.OUT_DIR
IMAGES = os.path.join(ROOT, "images")
FAM = make_font.FAMILIES["adventor"]

DEMO = "Ville de Val-d'Or"
SCALE = 2

REG = os.path.join(OUT_DIR, "AdventorSlashV-Regular.ttf")
BOLD = os.path.join(OUT_DIR, "AdventorSlashV-Bold.ttf")
ITAL = os.path.join(OUT_DIR, "AdventorSlashV-Italic.ttf")
BI = os.path.join(OUT_DIR, "AdventorSlashV-BoldItalic.ttf")

INK = "#111111"
GREY = "#9aa0a6"
ACCENT = "#0aa06e"
RULE = "#e2e5e9"


def s(n):
    return n * SCALE


def main() -> int:
    log.info("avantgarde-vvd / demo_adventor.py")
    try:
        orig = make_font.resolve_source("texgyreadventor-regular.otf", FAM)
    except FileNotFoundError:
        log.exception("Adventor source missing")
        return 1

    for path, label in [(REG, "Regular"), (BOLD, "Bold"), (ITAL, "Italic"), (BI, "BoldItalic"), (orig, "original")]:
        log_path(log, label, path)
        if not os.path.isfile(path):
            log.error("missing %s — run: python scripts/make_font.py adventor", path)
            return 1

    W, H = 1500 * SCALE, 1500 * SCALE
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    M = 80 * SCALE

    def f(path, size):
        return ImageFont.truetype(path, s(size))

    def rule(y):
        d.line([(M, y), (W - M, y)], fill=RULE, width=max(1, s(2)))

    log.info("drawing Adventor specimen...")
    d.text((M, s(58)), "A D V E N T O R   S L A S H V", fill=ACCENT, font=f(BOLD, 22))
    d.text((M, s(96)), DEMO, fill=INK, font=f(BOLD, 118))
    d.text((M, s(244)), "TeX Gyre Adventor - V with a vertical left stroke", fill=GREY, font=f(REG, 28))
    rule(s(310))

    y = s(350)
    for label, path in [("Regular", REG), ("Bold", BOLD), ("Italic", ITAL), ("Bold Italic", BI)]:
        log.debug("row %s", label)
        d.text((M, y + s(22)), label, fill=ACCENT, font=f(REG, 22))
        d.text((M + s(280), y), DEMO, fill=INK, font=f(path, 70))
        y += s(108)

    rule(y + s(20))
    y += s(55)
    d.text((M, y), "The V", fill=ACCENT, font=f(REG, 24))
    bx = M + s(240)
    d.text((bx, y - s(42)), "V", fill="#c9ced4", font=f(orig, 190))
    d.text((bx + s(180), y - s(42)), "V", fill=INK, font=f(REG, 190))
    d.text((bx, y + s(150)), "original", fill=GREY, font=f(REG, 20))
    d.text((bx + s(180), y + s(150)), "customized", fill=GREY, font=f(REG, 20))

    os.makedirs(IMAGES, exist_ok=True)
    out = os.path.join(IMAGES, "demo_adventor.png")
    img.save(out, dpi=(144, 144), optimize=True)
    log_path(log, "wrote", out, level=20)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log.error("unhandled:\n%s", traceback.format_exc())
        sys.exit(1)
