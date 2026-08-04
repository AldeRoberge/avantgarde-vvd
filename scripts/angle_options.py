"""Render the V at several right-stroke angles so the slant can be chosen."""
import os
import shutil

from PIL import Image, ImageDraw, ImageFont

import make_font

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = os.path.join(ROOT, "images")
SCRATCH = os.path.join(ROOT, "scripts", "_angles")
SRC_DIR = make_font.SRC_DIR

DEMO = "Ville de Val-d'Or"
OPTIONS = [0, 4, 8, 12, 16]
SRC, STYLE = "AVGARDD.TTF", "Demi"      # Demi shows the slant most clearly

GREY = "#9aa0a6"
ACCENT = "#0aa06e"

shutil.rmtree(SCRATCH, ignore_errors=True)
os.makedirs(SCRATCH, exist_ok=True)

built = []
for extra in OPTIONS:
    path = os.path.join(SCRATCH, f"v{extra}.ttf")
    _, old_deg, new_deg = make_font.build(SRC, STYLE, path, extra)
    built.append((extra, path, old_deg, new_deg))

W = 1500
ROW = 210
H = 150 + ROW * len(built)
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
lab = ImageFont.truetype(os.path.join(SRC_DIR, "AVGARDN.TTF"), 26)
labb = ImageFont.truetype(os.path.join(SRC_DIR, "AVGARDD.TTF"), 28)

d.text((70, 50), "Right-stroke angle options (Demi)", fill="#111111", font=labb)
d.text((70, 92), "current setting is +8", fill=ACCENT, font=lab)

y = 150
for extra, path, old_deg, new_deg in built:
    f_big = ImageFont.truetype(path, 170)
    f_txt = ImageFont.truetype(path, 72)

    tag = f"+{extra}"
    d.text((70, y + 60), tag, fill=ACCENT if extra == make_font.EXTRA_ANGLE else GREY, font=labb)
    d.text((70, y + 100), f"{new_deg:.1f} deg", fill=GREY, font=ImageFont.truetype(os.path.join(SRC_DIR, "AVGARDN.TTF"), 20))

    d.text((190, y + 10), "V", fill="#111111", font=f_big)
    d.text((360, y + 55), DEMO, fill="#111111", font=f_txt)

    d.line([(70, y + ROW - 20), (W - 70, y + ROW - 20)], fill="#eceff1", width=2)
    y += ROW

os.makedirs(IMAGES, exist_ok=True)
out = os.path.join(IMAGES, "angle_options.png")
img.save(out)
print(out)

shutil.rmtree(SCRATCH, ignore_errors=True)
