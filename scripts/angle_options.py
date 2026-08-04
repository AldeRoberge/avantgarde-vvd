"""Render the V at several right-stroke angles so the slant can be chosen."""
from __future__ import annotations

import os
import shutil
import sys
import traceback

from PIL import Image, ImageDraw, ImageFont

import make_font
from logutil import log_path, setup_logging

log = setup_logging("angle_options")

ROOT = make_font.ROOT
IMAGES = os.path.join(ROOT, "images")
SCRATCH = os.path.join(ROOT, "scripts", "_angles")
FAM = make_font.FAMILIES["avantgarde"]

DEMO = "Ville de Val-d'Or"
OPTIONS = [0, 4, 8, 12, 16]
SRC, STYLE = "AVGARDD.TTF", "Demi"

GREY = "#9aa0a6"
ACCENT = "#0aa06e"


def main() -> int:
    log.info("avantgarde-vvd / angle_options.py")
    log.info("ROOT=%s", ROOT)
    log.info("OPTIONS=%s  EXTRA_ANGLE default=%s", OPTIONS, make_font.EXTRA_ANGLE)
    log.info("building from %s (%s)", SRC, STYLE)
    log_path(log, "SCRATCH", SCRATCH)
    log_path(log, "IMAGES", IMAGES)

    try:
        make_font.resolve_source(SRC, FAM)
        make_font.resolve_source("AVGARDN.TTF", FAM)
    except FileNotFoundError:
        log.exception("required source font missing")
        return 1

    if os.path.isdir(SCRATCH):
        log.debug("removing previous scratch dir %s", SCRATCH)
        shutil.rmtree(SCRATCH, ignore_errors=True)
    os.makedirs(SCRATCH, exist_ok=True)

    built = []
    for extra in OPTIONS:
        path = os.path.join(SCRATCH, f"v{extra}.ttf")
        log.info("----- build angle +%s -> %s -----", extra, path)
        try:
            _, old_deg, new_deg = make_font.build(
                SRC, STYLE, path, extra, family=FAM
            )
            log.info("  original %.2f° -> new %.2f°", old_deg, new_deg)
            built.append((extra, path, old_deg, new_deg))
        except Exception:
            log.exception("failed building angle +%s", extra)
            return 1

    W = 1500
    ROW = 210
    H = 150 + ROW * len(built)
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    lab = ImageFont.truetype(make_font.resolve_source("AVGARDN.TTF", FAM), 26)
    labb = ImageFont.truetype(make_font.resolve_source("AVGARDD.TTF", FAM), 28)

    d.text((70, 50), "Right-stroke angle options (Demi)", fill="#111111", font=labb)
    d.text((70, 92), f"current setting is +{make_font.EXTRA_ANGLE:g}", fill=ACCENT, font=lab)

    y = 150
    for extra, path, old_deg, new_deg in built:
        f_big = ImageFont.truetype(path, 170)
        f_txt = ImageFont.truetype(path, 72)
        tag = f"+{extra}"
        color = ACCENT if extra == make_font.EXTRA_ANGLE else GREY
        d.text((70, y + 60), tag, fill=color, font=labb)
        d.text(
            (70, y + 100),
            f"{new_deg:.1f} deg",
            fill=GREY,
            font=ImageFont.truetype(make_font.resolve_source("AVGARDN.TTF", FAM), 20),
        )
        d.text((190, y + 10), "V", fill="#111111", font=f_big)
        d.text((360, y + 55), DEMO, fill="#111111", font=f_txt)
        d.line([(70, y + ROW - 20), (W - 70, y + ROW - 20)], fill="#eceff1", width=2)
        y += ROW

    os.makedirs(IMAGES, exist_ok=True)
    out = os.path.join(IMAGES, "angle_options.png")
    img.save(out)
    log_path(log, "wrote", out, level=20)

    shutil.rmtree(SCRATCH, ignore_errors=True)
    log.info("angle_options.png ready")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log.error("unhandled error:\n%s", traceback.format_exc())
        sys.exit(1)
