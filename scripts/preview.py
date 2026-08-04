import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Windows", "Fonts")
OUT_DIR = os.path.join(ROOT, "fonts")
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


W, H = s(1600), s(1180)
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
label = ImageFont.truetype(os.path.join(SRC_DIR, "AVGARDN.TTF"), s(30))

y = s(40)
for style, src, mod in PAIRS:
    f_o = ImageFont.truetype(os.path.join(SRC_DIR, src), s(88))
    f_m = ImageFont.truetype(os.path.join(OUT_DIR, mod), s(88))

    d.text((s(50), y), f"{style} - original", fill="#999999", font=label)
    d.text((s(50), y + s(40)), DEMO, fill="#999999", font=f_o)
    d.text((s(50), y + s(165)), f"{style} - customized", fill="#0a7", font=label)
    d.text((s(50), y + s(205)), DEMO, fill="black", font=f_m)
    y += s(385)

os.makedirs(IMAGES, exist_ok=True)
out = os.path.join(IMAGES, "preview.png")
img.save(out, dpi=(144, 144), optimize=True)
print(f"{out}  ({W}x{H})")

# --- Big V comparison (Book) ---
img2 = Image.new("RGB", (s(760), s(520)), "white")
d2 = ImageDraw.Draw(img2)
big_o = ImageFont.truetype(os.path.join(SRC_DIR, "AVGARDN.TTF"), s(340))
big_m = ImageFont.truetype(os.path.join(OUT_DIR, "AvantGardeSlashV-Book.ttf"), s(340))
d2.text((s(50), s(60)), "V", fill="#c8c8c8", font=big_o)
d2.text((s(430), s(60)), "V", fill="black", font=big_m)
out2 = os.path.join(IMAGES, "preview_V.png")
img2.save(out2, dpi=(144, 144), optimize=True)
print(f"{out2}  ({s(760)}x{s(520)})")
