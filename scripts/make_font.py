"""
Create a customized AvantGarde font whose 'V' has a vertical left stroke.

The left stroke becomes a vertical stem and the right stroke can be given extra
slant. Both strokes meet at the bottom, forming a single connected V.

Base fonts are the AvantGarde TTFs installed in the user's font folder.
The output family is renamed so it can live alongside the original AvantGarde.
"""
import math
import os
from array import array

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Windows", "Fonts")
OUT_DIR = os.path.join(ROOT, "fonts")

# Degrees of extra slant added to the right stroke's original angle
# (the original is roughly 20 degrees off vertical). Larger = leans further right.
EXTRA_ANGLE = 8.0

VARIANTS = [
    ("AVGARDN.TTF", "Book", "AvantGardeSlashV-Book"),
    ("AVGARDD.TTF", "Demi", "AvantGardeSlashV-Demi"),
    ("AVGARDDO.TTF", "Demi Oblique", "AvantGardeSlashV-DemiOblique"),
]

NEW_FAMILY = "AvantGarde SlashV"


def analyze_V(points):
    """Identify the 7 structural points of the V outline.

    The three AvantGarde files store this contour starting at different points,
    so the points must be found by geometry rather than by index.
    """
    ytop = max(y for _, y in points)
    ybot = min(y for _, y in points)

    top = sorted([p for p in points if p[1] == ytop])
    bottom = sorted([p for p in points if p[1] == ybot])
    middle = [p for p in points if p[1] not in (ytop, ybot)]

    assert len(top) == 4 and len(bottom) == 2 and len(middle) == 1, points

    return {
        "TLo": top[0],   # left stroke, top outer corner
        "TLi": top[1],   # left stroke, top inner corner
        "TRi": top[2],   # right stroke, top inner corner
        "TRo": top[3],   # right stroke, top outer corner
        "botL": bottom[0],
        "tip": bottom[1],  # bottom tip, outer (right) side
        "notch": middle[0],
        "ytop": ytop,
        "ybot": ybot,
    }


def measure_stem_width(glyf, gname):
    """Horizontal thickness of a glyph's stem, measured across its middle.

    Used on 'I' to read the font's true vertical stem weight. Measuring on a
    scanline (rather than using the bounding box) keeps this correct for the
    oblique face, where the stem is a slanted parallelogram.
    """
    g = glyf[gname]
    coords, endPts, _ = g.getCoordinates(glyf)
    pts = [tuple(p) for p in coords]
    ys = [y for _, y in pts]
    y = (max(ys) + min(ys)) / 2.0

    xs = []
    start = 0
    for end in endPts:
        contour = pts[start:end + 1]
        n = len(contour)
        for i in range(n):
            x1, y1 = contour[i]
            x2, y2 = contour[(i + 1) % n]
            if y1 == y2:
                continue
            if min(y1, y2) <= y <= max(y1, y2):
                t = (y - y1) / (y2 - y1)
                xs.append(x1 + t * (x2 - x1))
        start = end + 1

    return max(xs) - min(xs)


def rebuild_V(font: TTFont, extra_angle: float):
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    cmap = font.getBestCmap()
    gname = cmap[ord("V")]
    g = glyf[gname]

    coords, _, _ = g.getCoordinates(glyf)
    P = analyze_V([tuple(p) for p in coords])

    ytop, ybot = P["ytop"], P["ybot"]
    _, ny = P["notch"]
    height = ytop - ybot

    # Stem thickness: use the font's real vertical stem, taken from 'I'.
    # The old left stroke is diagonal, so its horizontal top width is wider than
    # its actual perpendicular thickness; reusing that width made the upright
    # stem look too bold.
    W = round(measure_stem_width(glyf, cmap[ord("I")]))

    # Place the vertical stem at the same sidebearing as the 'H' stem, so the
    # letter is spaced like other flat-sided capitals.
    _, h_lsb = hmtx[cmap[ord("H")]]
    a = h_lsb
    stem_inner = a + W

    # Lean the right stroke further, keeping the same *horizontal* top width as
    # the vertical stem. Compensating with 1/cos to hold perpendicular weight made
    # the Demi / Demi Oblique tops read ~322 vs the rest of the face at ~285.
    theta = math.atan2(P["TRo"][0] - P["tip"][0], height)
    theta2 = theta + math.radians(extra_angle)
    tan2 = math.tan(theta2)
    horiz2 = W

    # The stroke hangs off the notch, where it joins the stem.
    x_top_inner = stem_inner + (ytop - ny) * tan2
    x_top_outer = x_top_inner + horiz2
    # Tip sits under the stem's right edge so the baseline of the V is exactly
    # stem-width wide (not stem + leftover tip overshoot).
    x_tip = stem_inner

    new_coords = [
        (a, ytop),                        # stem top outer
        (stem_inner, ytop),               # stem top inner
        (stem_inner, ny),                 # notch: strokes join here
        (round(x_top_inner), ytop),       # right stroke top inner
        (round(x_top_outer), ytop),       # right stroke top outer
        (round(x_tip), ybot),             # bottom tip (= stem's right foot)
        (a, ybot),                        # stem bottom outer
    ]

    g.coordinates = GlyphCoordinates(new_coords)
    g.flags = array("B", [1] * len(new_coords))   # all on-curve: straight lines
    g.endPtsOfContours = [len(new_coords) - 1]
    g.numberOfContours = 1

    # Drop the original hinting instructions: they reference the old point set
    # and would distort the new outline when the renderer hints it.
    prog = ttProgram.Program()
    prog.fromBytecode(b"")
    g.program = prog

    g.recalcBounds(glyf)

    # Keep the original right sidebearing so the apex relates to the next
    # letter the way it did before.
    old_aw, _ = hmtx[gname]
    rsb = old_aw - P["TRo"][0]
    hmtx[gname] = (g.xMax + rsb, g.xMin)

    return gname, math.degrees(theta), math.degrees(theta2)


def rename_font(font: TTFont, style: str):
    name = font["name"]
    full = f"{NEW_FAMILY} {style}".strip()
    ps = full.replace(" ", "")

    def setn(nameID, value):
        name.setName(value, nameID, 3, 1, 0x409)   # Windows Unicode English
        name.setName(value, nameID, 1, 0, 0)       # Mac Roman English

    setn(1, NEW_FAMILY)
    setn(2, style)
    setn(3, f"{NEW_FAMILY} {style} 1.0")
    setn(4, full)
    setn(6, ps)
    setn(16, NEW_FAMILY)
    setn(17, style)


def build(src, style, out_path, extra_angle=EXTRA_ANGLE):
    font = TTFont(os.path.join(SRC_DIR, src))
    gname, old_deg, new_deg = rebuild_V(font, extra_angle)

    # These cache per-size metrics that no longer match the new advance width.
    for tag in ("hdmx", "LTSH", "VDMX"):
        if tag in font:
            del font[tag]

    rename_font(font, style)
    font.save(out_path)
    return gname, old_deg, new_deg


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for src, style, outbase in VARIANTS:
        out = os.path.join(OUT_DIR, outbase + ".ttf")
        _, old_deg, new_deg = build(src, style, out, EXTRA_ANGLE)
        print(f"{src}: right stroke {old_deg:.1f} -> {new_deg:.1f} deg  ->  {outbase}.ttf")


if __name__ == "__main__":
    main()
