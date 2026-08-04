import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Windows", "Fonts")
OUT_DIR = os.path.join(ROOT, "fonts")
IMAGES = os.path.join(ROOT, "images")

DEMO = "Ville de Val-d'Or"
SCALE = 2  # render at 2x for a crisp high-res PNG

BOOK = os.path.join(OUT_DIR, "AvantGardeSlashV-Book.ttf")
DEMI = os.path.join(OUT_DIR, "AvantGardeSlashV-Demi.ttf")
OBLQ = os.path.join(OUT_DIR, "AvantGardeSlashV-DemiOblique.ttf")
ORIG_BOOK = os.path.join(SRC_DIR, "AVGARDN.TTF")

INK = "#111111"
GREY = "#9aa0a6"
ACCENT = "#0aa06e"
RULE = "#e2e5e9"

W, H = 1500 * SCALE, 1360 * SCALE
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

M = 80 * SCALE


def s(n):
    return n * SCALE


def f(path, size):
    return ImageFont.truetype(path, s(size))


def rule(y):
    d.line([(M, y), (W - M, y)], fill=RULE, width=max(1, s(2)))


# --- Header ---
d.text((M, s(58)), "A V A N T G A R D E   S L A S H V", fill=ACCENT, font=f(DEMI, 22))
d.text((M, s(96)), DEMO, fill=INK, font=f(DEMI, 118))
d.text((M, s(244)), "Custom AvantGarde - the V has a vertical left stroke", fill=GREY, font=f(BOOK, 30))
rule(s(310))

# --- Weights ---
y = s(350)
for label, path, size in [("Book", BOOK, 74), ("Demi", DEMI, 74), ("Demi Oblique", OBLQ, 74)]:
    d.text((M, y + s(22)), label, fill=ACCENT, font=f(BOOK, 24))
    d.text((M + s(240), y), DEMO, fill=INK, font=f(path, size))
    y += s(108)

rule(y + s(20))

# --- Size ramp ---
y += s(60)
for size in (46, 34, 26, 20):
    d.text((M, y + s(46 - size) // 2), f"{size}px", fill=GREY, font=f(BOOK, 18))
    d.text((M + s(100), y), DEMO, fill=INK, font=f(BOOK, size))
    y += s(size + 26)

rule(y + s(20))

# --- Before / after V ---
y += s(55)
d.text((M, y), "The V", fill=ACCENT, font=f(BOOK, 24))

big_o = f(ORIG_BOOK, 190)
big_n = f(BOOK, 190)
bx = M + s(240)
d.text((bx, y - s(42)), "V", fill="#c9ced4", font=big_o)
d.text((bx + s(160), y - s(42)), "V", fill=INK, font=big_n)

d.text((bx, y + s(150)), "original", fill=GREY, font=f(BOOK, 20))
d.text((bx + s(160), y + s(150)), "customized", fill=GREY, font=f(BOOK, 20))

note = ("Left stroke is vertical; the right stroke leans 8 degrees\n"
        "further right than the original. Both strokes share the\n"
        "font's stem width so their top edges match in weight.")
d.multiline_text((bx + s(420), y - s(10)), note, fill=GREY, font=f(BOOK, 26), spacing=s(12))

os.makedirs(IMAGES, exist_ok=True)
out = os.path.join(IMAGES, "demo.png")
img.save(out, dpi=(144, 144), optimize=True)
print(f"{out}  ({W}x{H})")
