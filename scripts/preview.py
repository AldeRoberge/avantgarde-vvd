"""Render original-vs-customized previews for every weight."""
from __future__ import annotations

import os
import sys
import traceback

from PIL import Image, ImageDraw, ImageFont

import make_font
from logutil import log_path, setup_logging

log = setup_logging("preview")

ROOT = make_font.ROOT
OUT_DIR = make_font.OUT_DIR
IMAGES = os.path.join(ROOT, "images")

DEMO = "Ville de Val-d'Or"
SCALE = 2

PAIRS = [
    ("Book", "AVGARDN.TTF", "AvantGardeSlashV-Book.ttf"),
    ("Demi", "AVGARDD.TTF", "AvantGardeSlashV-Demi.ttf"),
    ("Demi Oblique", "AVGARDDO.TTF", "AvantGardeSlashV-DemiOblique.ttf"),
]


def s(n):
    return n * SCALE


def main() -> int:
    log.info("avantgarde-vvd / preview.py")
    log.info("ROOT=%s  SCALE=%s", ROOT, SCALE)
    log_path(log, "OUT_DIR", OUT_DIR)
    log_path(log, "IMAGES", IMAGES)

    W, H = s(1600), s(1180)
    log.info("canvas %dx%d", W, H)
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    try:
        label_path = make_font.resolve_source("AVGARDN.TTF")
        label = ImageFont.truetype(label_path, s(30))
        log.debug("label font loaded from %s", label_path)
    except Exception:
        log.exception("failed to load label font AVGARDN.TTF")
        return 1

    y = s(40)
    for style, src, mod in PAIRS:
        log.info("----- weight %s -----", style)
        mod_path = os.path.join(OUT_DIR, mod)
        log_path(log, "modified", mod_path)
        if not os.path.isfile(mod_path):
            log.error("missing modified font %s — run make_font.py first", mod_path)
            return 1

        try:
            src_path = make_font.resolve_source(src)
            f_o = ImageFont.truetype(src_path, s(88))
            f_m = ImageFont.truetype(mod_path, s(88))
            log.debug("loaded original %s and modified %s at %dpx", src_path, mod_path, s(88))
        except Exception:
            log.exception("failed loading fonts for weight %s", style)
            return 1

        d.text((s(50), y), f"{style} - original", fill="#999999", font=label)
        d.text((s(50), y + s(40)), DEMO, fill="#999999", font=f_o)
        d.text((s(50), y + s(165)), f"{style} - customized", fill="#0a7", font=label)
        d.text((s(50), y + s(205)), DEMO, fill="black", font=f_m)
        y += s(385)
        log.debug("next row y=%s", y)

    os.makedirs(IMAGES, exist_ok=True)
    out = os.path.join(IMAGES, "preview.png")
    try:
        img.save(out, dpi=(144, 144), optimize=True)
    except Exception:
        log.exception("failed to save %s", out)
        return 1
    log_path(log, "wrote", out, level=20)

    log.info("drawing big V comparison (Book)...")
    img2 = Image.new("RGB", (s(760), s(520)), "white")
    d2 = ImageDraw.Draw(img2)
    try:
        big_o = ImageFont.truetype(make_font.resolve_source("AVGARDN.TTF"), s(340))
        big_m = ImageFont.truetype(os.path.join(OUT_DIR, "AvantGardeSlashV-Book.ttf"), s(340))
    except Exception:
        log.exception("failed loading fonts for preview_V")
        return 1

    d2.text((s(50), s(60)), "V", fill="#c8c8c8", font=big_o)
    d2.text((s(430), s(60)), "V", fill="black", font=big_m)
    out2 = os.path.join(IMAGES, "preview_V.png")
    try:
        img2.save(out2, dpi=(144, 144), optimize=True)
    except Exception:
        log.exception("failed to save %s", out2)
        return 1

    log_path(log, "wrote", out2, level=20)
    log.info("preview images ready")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log.error("unhandled error:\n%s", traceback.format_exc())
        sys.exit(1)
