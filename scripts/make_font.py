"""
Build SlashV font families: AvantGarde SlashV and Adventor SlashV.

Rewrites the capital V so the left stroke is vertical and the right stroke
leans further right, joined as a single connected glyph.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import traceback
from array import array
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

from logutil import log_path, setup_logging

log = setup_logging("make_font")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_ROOT = os.path.join(ROOT, "source")
SYSTEM_FONTS = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
OUT_DIR = os.path.join(ROOT, "fonts")

# Default extra slant (degrees) past each face's original right-stroke angle.
EXTRA_ANGLE = 8.0

# Back-compat for older preview scripts that imported SRC_DIR.
SRC_DIR = os.path.join(SOURCE_ROOT, "avantgarde")


@dataclass(frozen=True)
class Variant:
    source_file: str
    style: str
    out_base: str


@dataclass(frozen=True)
class Family:
    key: str
    new_family: str
    source_subdir: str
    variants: Tuple[Variant, ...]
    # Also look under Windows user fonts (AvantGarde only).
    system_fallback: bool = False


FAMILIES: dict[str, Family] = {
    "avantgarde": Family(
        key="avantgarde",
        new_family="AvantGarde SlashV",
        source_subdir="avantgarde",
        system_fallback=True,
        variants=(
            Variant("AVGARDN.TTF", "Book", "AvantGardeSlashV-Book"),
            Variant("AVGARDD.TTF", "Demi", "AvantGardeSlashV-Demi"),
            Variant("AVGARDDO.TTF", "Demi Oblique", "AvantGardeSlashV-DemiOblique"),
        ),
    ),
    "adventor": Family(
        key="adventor",
        new_family="Adventor SlashV",
        source_subdir="tex-gyre-adventor",
        system_fallback=False,
        variants=(
            Variant("texgyreadventor-regular.otf", "Regular", "AdventorSlashV-Regular"),
            Variant("texgyreadventor-bold.otf", "Bold", "AdventorSlashV-Bold"),
            Variant("texgyreadventor-italic.otf", "Italic", "AdventorSlashV-Italic"),
            Variant("texgyreadventor-bolditalic.otf", "Bold Italic", "AdventorSlashV-BoldItalic"),
        ),
    ),
}


def family_source_dir(family: Family) -> str:
    return os.path.join(SOURCE_ROOT, family.source_subdir)


def resolve_source(filename: str, family: Optional[Family] = None) -> str:
    """Resolve a source font path.

    Prefer ``source/<family>/file``. For AvantGarde, also fall back to the
    Windows user fonts folder. If *family* is omitted (legacy callers), try
    AvantGarde locations then Adventor.
    """
    candidates: List[Tuple[str, str]] = []

    if family is not None:
        local = os.path.join(family_source_dir(family), filename)
        candidates.append(("local", local))
        if family.system_fallback and SYSTEM_FONTS:
            candidates.append(("system", os.path.join(SYSTEM_FONTS, filename)))
    else:
        # Legacy / convenience: search known folders.
        for key in ("avantgarde", "adventor"):
            fam = FAMILIES[key]
            candidates.append((f"local:{key}", os.path.join(family_source_dir(fam), filename)))
        if SYSTEM_FONTS:
            candidates.append(("system", os.path.join(SYSTEM_FONTS, filename)))

    log.debug("resolve_source(%r, family=%s)", filename, getattr(family, "key", None))
    for label, path in candidates:
        exists = os.path.isfile(path)
        log.debug("  try %-12s %s  exists=%s", label, path, exists)
        if exists:
            if label.startswith("system"):
                log.warning("source %s not in source/; using %s", filename, path)
            else:
                log.info("source %s -> %s", filename, path)
            return path

    log.error("source font NOT FOUND: %s", filename)
    for label, path in candidates:
        log.error("  looked [%s]: %s", label, path)
    raise FileNotFoundError(
        f"Source font not found: {filename}\n"
        + "\n".join(f"  tried: {p}" for _, p in candidates)
    )


def ensure_truetype(font: TTFont) -> None:
    """Convert a CFF/OTF font in-place to a TrueType (glyf) font if needed."""
    if "glyf" in font and "CFF " not in font:
        log.debug("font already TrueType (glyf present)")
        return
    if "CFF " not in font and "CFF2" not in font:
        log.error("font has neither glyf nor CFF outlines; tables=%s", sorted(font.keys()))
        raise ValueError("Unsupported font format (no glyf/CFF)")

    log.info("converting CFF outlines -> TrueType (glyf)...")
    gs = font.getGlyphSet()
    order = font.getGlyphOrder()
    font["loca"] = newTable("loca")
    font["glyf"] = newTable("glyf")
    font["glyf"].glyphs = {}
    font["glyf"].glyphOrder = order

    converted = 0
    for name in order:
        pen = TTGlyphPen(None)
        # reverse_direction: CFF and TT winding conventions differ.
        gs[name].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
        font["glyf"][name] = pen.glyph()
        converted += 1

    del font["CFF "]
    if "CFF2" in font:
        del font["CFF2"]
    if "VORG" in font:
        del font["VORG"]
    font.sfntVersion = "\x00\x01\x00\x00"
    log.info("converted %d glyphs to quadratic TrueType outlines", converted)


def analyze_V(points):
    """Identify the 7 structural points of the V outline by geometry."""
    log.debug("analyze_V: %d raw points: %s", len(points), points)

    if len(points) != 7:
        log.error("analyze_V expected 7 points, got %d: %s", len(points), points)
        raise ValueError(f"V glyph must have 7 outline points, got {len(points)}")

    ytop = max(y for _, y in points)
    ybot = min(y for _, y in points)

    top = sorted([p for p in points if p[1] == ytop])
    bottom = sorted([p for p in points if p[1] == ybot])
    middle = [p for p in points if p[1] not in (ytop, ybot)]

    log.debug("  ytop=%s ybot=%s", ytop, ybot)
    log.debug("  top (%d)=%s bottom (%d)=%s middle (%d)=%s",
              len(top), top, len(bottom), bottom, len(middle), middle)

    if not (len(top) == 4 and len(bottom) == 2 and len(middle) == 1):
        raise AssertionError(
            f"Unexpected V outline topology: top={top} bottom={bottom} middle={middle}"
        )

    result = {
        "TLo": top[0],
        "TLi": top[1],
        "TRi": top[2],
        "TRo": top[3],
        "botL": bottom[0],
        "tip": bottom[1],
        "notch": middle[0],
        "ytop": ytop,
        "ybot": ybot,
    }
    log.debug(
        "  classified TLo=%s TLi=%s notch=%s TRi=%s TRo=%s tip=%s",
        result["TLo"], result["TLi"], result["notch"],
        result["TRi"], result["TRo"], result["tip"],
    )
    return result


def measure_stem_width(glyf, gname):
    """Horizontal thickness of a glyph's stem, measured across its middle."""
    g = glyf[gname]
    coords, endPts, _ = g.getCoordinates(glyf)
    pts = [tuple(p) for p in coords]
    ys = [y for _, y in pts]
    y = (max(ys) + min(ys)) / 2.0

    log.debug("measure_stem_width(%r): %d pts, y-scan=%.1f", gname, len(pts), y)

    xs = []
    start = 0
    for end in endPts:
        contour = pts[start : end + 1]
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

    if len(xs) < 2:
        raise ValueError(f"Could not measure stem width of glyph {gname!r} (hits={xs})")

    width = max(xs) - min(xs)
    log.debug("  hits=%s -> width=%.3f", sorted(xs), width)
    return width


def rebuild_V(font: TTFont, extra_angle: float):
    log.info("--- rebuild V glyph (extra_angle=%s°) ---", extra_angle)

    glyf = font["glyf"]
    hmtx = font["hmtx"]
    cmap = font.getBestCmap()

    for ch, need in (("V", "glyph"), ("I", "stem width"), ("H", "sidebearing")):
        if ord(ch) not in cmap:
            raise KeyError(f"Font cmap does not include capital {ch} (needed for {need})")

    gname = cmap[ord("V")]
    i_name = cmap[ord("I")]
    h_name = cmap[ord("H")]
    log.debug("cmap: V=%r I=%r H=%r", gname, i_name, h_name)

    g = glyf[gname]
    try:
        g.recalcBounds(glyf)
    except Exception:
        log.debug("recalcBounds on original V skipped/failed", exc_info=True)
    log.debug(
        "original V: contours=%s bounds=(%s,%s)-(%s,%s)",
        g.numberOfContours,
        getattr(g, "xMin", "?"),
        getattr(g, "yMin", "?"),
        getattr(g, "xMax", "?"),
        getattr(g, "yMax", "?"),
    )

    old_aw, old_lsb = hmtx[gname]
    log.debug("original V hmtx: aw=%s lsb=%s", old_aw, old_lsb)

    coords, endPts, flags = g.getCoordinates(glyf)
    pts = [tuple(p) for p in coords]
    log.info("original V points: %s", pts)
    log.debug("endPts=%s flags=%s", endPts, list(flags))

    if g.numberOfContours != 1:
        log.warning("original V has %d contours (expected 1)", g.numberOfContours)

    P = analyze_V(pts)
    ytop, ybot = P["ytop"], P["ybot"]
    _, ny = P["notch"]
    height = ytop - ybot
    if height <= 0:
        raise ValueError(f"Invalid V height: ytop={ytop} ybot={ybot}")

    W = round(measure_stem_width(glyf, i_name))
    log.info("stem width from 'I': %s font units", W)

    orig_left_top = P["TLi"][0] - P["TLo"][0]
    orig_right_top = P["TRo"][0] - P["TRi"][0]
    log.debug("original top widths left=%s right=%s (using I=%s)", orig_left_top, orig_right_top, W)

    _, h_lsb = hmtx[h_name]
    a = h_lsb
    stem_inner = a + W
    log.info("stem placement: outer x=%s (H lsb), inner x=%s", a, stem_inner)

    theta = math.atan2(P["TRo"][0] - P["tip"][0], height)
    theta2 = theta + math.radians(extra_angle)
    tan2 = math.tan(theta2)
    horiz2 = W
    log.info(
        "right stroke angle: %.2f° -> %.2f° (EXTRA_ANGLE=%s)",
        math.degrees(theta), math.degrees(theta2), extra_angle,
    )

    x_top_inner = stem_inner + (ytop - ny) * tan2
    x_top_outer = x_top_inner + horiz2
    x_tip = stem_inner

    new_coords = [
        (a, ytop),
        (stem_inner, ytop),
        (stem_inner, ny),
        (round(x_top_inner), ytop),
        (round(x_top_outer), ytop),
        (round(x_tip), ybot),
        (a, ybot),
    ]
    labels = [
        "stem top outer", "stem top inner", "notch",
        "right top inner", "right top outer", "tip", "stem bottom outer",
    ]
    log.info("new V coordinates:")
    for label, pt in zip(labels, new_coords):
        log.info("  %-18s %s", label, pt)

    stem_w = new_coords[1][0] - new_coords[0][0]
    right_w = new_coords[4][0] - new_coords[3][0]
    bottom_w = new_coords[5][0] - new_coords[6][0]
    log.info("metrics check: stem_top=%s right_top=%s bottom=%s", stem_w, right_w, bottom_w)
    if not (stem_w == right_w == bottom_w == W):
        log.warning(
            "width mismatch! expected %s, got stem=%s right=%s bottom=%s",
            W, stem_w, right_w, bottom_w,
        )

    g.coordinates = GlyphCoordinates(new_coords)
    g.flags = array("B", [1] * len(new_coords))
    g.endPtsOfContours = [len(new_coords) - 1]
    g.numberOfContours = 1

    prog = ttProgram.Program()
    prog.fromBytecode(b"")
    g.program = prog
    g.recalcBounds(glyf)

    rsb = old_aw - P["TRo"][0]
    new_aw = g.xMax + rsb
    hmtx[gname] = (new_aw, g.xMin)
    log.info("hmtx: advance %s -> %s (rsb=%s, lsb=%s)", old_aw, new_aw, rsb, g.xMin)

    return gname, math.degrees(theta), math.degrees(theta2)


def rename_font(font: TTFont, family_name: str, style: str):
    name = font["name"]
    full = f"{family_name} {style}".strip()
    ps = full.replace(" ", "")

    old_family = name.getDebugName(1)
    old_full = name.getDebugName(4)
    log.info(
        "rename: %r / %r  ->  family=%r style=%r full=%r",
        old_family, old_full, family_name, style, full,
    )

    def setn(nameID, value):
        name.setName(value, nameID, 3, 1, 0x409)
        name.setName(value, nameID, 1, 0, 0)
        log.debug("  nameID %2d = %r", nameID, value)

    setn(1, family_name)
    setn(2, style)
    setn(3, f"{family_name} {style} 1.0")
    setn(4, full)
    setn(6, ps)
    setn(16, family_name)
    setn(17, style)


def build(
    src: str,
    style: str,
    out_path: str,
    extra_angle: float = EXTRA_ANGLE,
    family: Optional[Family] = None,
    new_family: Optional[str] = None,
):
    """Build one SlashV style. *family* is preferred; *new_family* overrides the name."""
    fam_name = new_family or (family.new_family if family else "SlashV")
    log.info("========== build %s (%s) / family=%s ==========", src, style, fam_name)

    src_path = resolve_source(src, family)
    log_path(log, "input", src_path, level=20)

    try:
        font = TTFont(src_path)
    except Exception:
        log.exception("failed to open font: %s", src_path)
        raise

    log.debug("tables: %s", sorted(font.keys()))
    log.info(
        "unitsPerEm=%s  italicAngle=%s  sfntVersion=%r",
        font["head"].unitsPerEm, font["post"].italicAngle, font.sfntVersion,
    )

    ensure_truetype(font)

    gname, old_deg, new_deg = rebuild_V(font, extra_angle)

    for tag in ("hdmx", "LTSH", "VDMX"):
        if tag in font:
            log.debug("dropping stale metrics table %r", tag)
            del font[tag]

    rename_font(font, fam_name, style)

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    try:
        font.save(out_path)
    except Exception:
        log.exception("failed to save font: %s", out_path)
        raise

    log_path(log, "output", out_path, level=20)
    log.info("done %s: V %.2f° -> %.2f°  ->  %s", style, old_deg, new_deg, out_path)
    return gname, old_deg, new_deg


def build_family(family: Family, extra_angle: float = EXTRA_ANGLE) -> List[Tuple[str, Exception]]:
    log.info("######## family %s (%s) ########", family.key, family.new_family)
    log_path(log, "source dir", family_source_dir(family))
    errors = []
    for variant in family.variants:
        out = os.path.join(OUT_DIR, variant.out_base + ".ttf")
        try:
            build(
                variant.source_file,
                variant.style,
                out,
                extra_angle=extra_angle,
                family=family,
            )
        except Exception as exc:
            log.error("FAILED %s / %s: %s", family.key, variant.style, exc)
            log.debug("traceback:\n%s", traceback.format_exc())
            errors.append((f"{family.key}:{variant.source_file}", exc))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build SlashV fonts (AvantGarde and/or TeX Gyre Adventor)."
    )
    parser.add_argument(
        "families",
        nargs="*",
        default=None,
        help="Which families to build: avantgarde, adventor (default: all).",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="INFO only (default DEBUG).")
    parser.add_argument(
        "--angle",
        type=float,
        default=EXTRA_ANGLE,
        help=f"Extra degrees on the right stroke (default {EXTRA_ANGLE}).",
    )
    args = parser.parse_args(argv)

    if args.quiet:
        log.setLevel(20)
        for h in log.handlers:
            h.setLevel(20)

    keys = args.families if args.families else list(FAMILIES.keys())
    unknown = [k for k in keys if k not in FAMILIES]
    if unknown:
        log.error("unknown family key(s): %s  (known: %s)", unknown, sorted(FAMILIES))
        return 2
    log.info("avantgarde-vvd / make_font.py")
    log.info("ROOT=%s", ROOT)
    log_path(log, "SOURCE_ROOT", SOURCE_ROOT)
    log_path(log, "OUT_DIR", OUT_DIR)
    log.info("families=%s  angle=%s", keys, args.angle)

    os.makedirs(OUT_DIR, exist_ok=True)

    all_errors = []
    for key in keys:
        all_errors.extend(build_family(FAMILIES[key], args.angle))

    log.info("========== summary ==========")
    if all_errors:
        log.error("%d build(s) FAILED:", len(all_errors))
        for label, exc in all_errors:
            log.error("  %s: %s", label, exc)
        return 1

    log.info("all requested families built OK -> %s", OUT_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
