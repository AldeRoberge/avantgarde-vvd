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

from logutil import log_path, set_verbose, setup_logging

log = setup_logging("make_font")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_ROOT = os.path.join(ROOT, "fonts")
SOURCE_ROOT = os.path.join(FONTS_ROOT, "input")
SYSTEM_FONTS = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
OUT_DIR = os.path.join(FONTS_ROOT, "output")

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

    Prefer ``fonts/input/<family>/file``. For AvantGarde, also fall back to the
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

    log.debug("Looking for source font %r (family=%s).", filename, getattr(family, "key", None))
    for label, path in candidates:
        exists = os.path.isfile(path)
        log.debug("  Checking %s: %s (%s)", label, path, "found" if exists else "not found")
        if exists:
            if label.startswith("system"):
                log.warning(
                    "Couldn't find %s in fonts/input/, "
                    "so I'm using the copy installed on Windows: %s",
                    filename,
                    path,
                )
            else:
                log.info("Using source file %s from %s.", filename, path)
            return path

    log.error("I couldn't find the source font %s anywhere.", filename)
    for label, path in candidates:
        log.error("  Looked in [%s]: %s", label, path)
    raise FileNotFoundError(
        f"Source font not found: {filename}\n"
        + "\n".join(f"  tried: {p}" for _, p in candidates)
    )


def ensure_truetype(font: TTFont) -> None:
    """Convert a CFF/OTF font in-place to a TrueType (glyf) font if needed.

    Follows fontTools' official otf2ttf recipe so Windows accepts the result
    (proper maxp v1.0, post table, glyf.compile, hmtx xMin sync).
    """
    if "glyf" in font and "CFF " not in font:
        log.debug("This font is already TrueType - no conversion needed.")
        return
    if "CFF " not in font and "CFF2" not in font:
        log.error(
            "This font doesn't have outlines I know how to edit "
            "(need TrueType glyf or CFF). Tables present: %s",
            sorted(font.keys()),
        )
        raise ValueError("Unsupported font format (no glyf/CFF)")

    log.info(
        "This font uses PostScript (CFF) outlines. "
        "Converting them to TrueType so Windows will accept the file..."
    )

    glyph_order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()

    font["loca"] = newTable("loca")
    font["glyf"] = glyf = newTable("glyf")
    glyf.glyphOrder = glyph_order
    glyf.glyphs = {}

    # Pass glyph_set into TTGlyphPen so composite glyphs resolve correctly.
    for name in glyph_order:
        tt_pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(Cu2QuPen(tt_pen, max_err=1.0, reverse_direction=True))
        glyf.glyphs[name] = tt_pen.glyph()

    del font["CFF "]
    if "CFF2" in font:
        del font["CFF2"]
    if "VORG" in font:
        del font["VORG"]

    glyf.compile(font)

    # Sync left sidebearings with the new quadratic outlines.
    hmtx = font["hmtx"]
    for glyph_name, glyph in glyf.glyphs.items():
        if hasattr(glyph, "xMin"):
            aw, _ = hmtx[glyph_name]
            hmtx[glyph_name] = (aw, glyph.xMin)

    # CFF fonts ship maxp v0.5; TrueType needs the full v1.0 maxp table.
    font["maxp"] = maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    maxp.numGlyphs = len(glyph_order)
    maxp.maxZones = 1
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = max(
        (len(g.components) if hasattr(g, "components") else 0)
        for g in glyf.glyphs.values()
    )
    maxp.compile(font)

    post = font["post"]
    post.formatType = 2.0
    post.extraNames = []
    post.mapping = {}
    post.glyphOrder = glyph_order
    try:
        post.compile(font)
    except OverflowError:
        log.warning(
            "Glyph names are too long for the 'post' table - "
            "keeping the font usable without them (post format 3)."
        )
        post.formatType = 3.0

    font.sfntVersion = "\x00\x01\x00\x00"
    log.info(
        "Converted %d glyphs to TrueType (maxp v1.0). Ready to edit the V.",
        len(glyph_order),
    )


def analyze_V(points):
    """Identify the 7 structural points of the V outline by geometry."""
    log.debug("Reading the V outline (%d points): %s", len(points), points)

    if len(points) != 7:
        log.error(
            "I expected the V to be a simple 7-point outline, but found %d points: %s",
            len(points),
            points,
        )
        raise ValueError(f"V glyph must have 7 outline points, got {len(points)}")

    ytop = max(y for _, y in points)
    ybot = min(y for _, y in points)

    top = sorted([p for p in points if p[1] == ytop])
    bottom = sorted([p for p in points if p[1] == ybot])
    middle = [p for p in points if p[1] not in (ytop, ybot)]

    log.debug("  Top of letter y=%s, baseline y=%s", ytop, ybot)
    log.debug(
        "  Top corners (%d): %s | Bottom (%d): %s | Notch (%d): %s",
        len(top), top, len(bottom), bottom, len(middle), middle,
    )

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
        "  Mapped corners - left top %s/%s, notch %s, right top %s/%s, tip %s",
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

    log.debug(
        "Measuring stem width of %r across the middle (y=%.1f, %d outline points).",
        gname, y, len(pts),
    )

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
    log.debug("  Crossed edges at x=%s -> stem width %.1f.", sorted(xs), width)
    return width


def rebuild_V(font: TTFont, extra_angle: float):
    log.info("Rewriting the capital V (adding %s° of slant on the right stroke)...", extra_angle)

    glyf = font["glyf"]
    hmtx = font["hmtx"]
    cmap = font.getBestCmap()

    for ch, need in (("V", "glyph"), ("I", "stem width"), ("H", "sidebearing")):
        if ord(ch) not in cmap:
            raise KeyError(f"Font cmap does not include capital {ch} (needed for {need})")

    gname = cmap[ord("V")]
    i_name = cmap[ord("I")]
    h_name = cmap[ord("H")]
    log.debug("Glyph names inside the font: V=%r, I=%r, H=%r", gname, i_name, h_name)

    g = glyf[gname]
    try:
        g.recalcBounds(glyf)
    except Exception:
        log.debug("Couldn't refresh the original V bounds (that's usually fine).", exc_info=True)
    log.debug(
        "Original V has %s contour(s), bounds (%s,%s) to (%s,%s).",
        g.numberOfContours,
        getattr(g, "xMin", "?"),
        getattr(g, "yMin", "?"),
        getattr(g, "xMax", "?"),
        getattr(g, "yMax", "?"),
    )

    old_aw, old_lsb = hmtx[gname]
    log.debug("Original V spacing: advance width %s, left sidebearing %s.", old_aw, old_lsb)

    coords, endPts, flags = g.getCoordinates(glyf)
    pts = [tuple(p) for p in coords]
    log.info("Original V outline points: %s", pts)
    log.debug("Contour end-points=%s, on-curve flags=%s", endPts, list(flags))

    if g.numberOfContours != 1:
        log.warning(
            "This V has %d contours; I usually expect just one. I'll keep going anyway.",
            g.numberOfContours,
        )

    P = analyze_V(pts)
    ytop, ybot = P["ytop"], P["ybot"]
    _, ny = P["notch"]
    height = ytop - ybot
    if height <= 0:
        raise ValueError(f"Invalid V height: ytop={ytop} ybot={ybot}")

    W = round(measure_stem_width(glyf, i_name))
    log.info("Matching the vertical stem to the letter I - width is %s units.", W)

    orig_left_top = P["TLi"][0] - P["TLo"][0]
    orig_right_top = P["TRo"][0] - P["TRi"][0]
    log.debug(
        "For reference, the old V tops were %s (left) and %s (right); we use %s instead.",
        orig_left_top, orig_right_top, W,
    )

    _, h_lsb = hmtx[h_name]
    a = h_lsb
    stem_inner = a + W
    log.info(
        "Placing the stem like H: left edge at x=%s, right edge at x=%s.",
        a, stem_inner,
    )

    theta = math.atan2(P["TRo"][0] - P["tip"][0], height)
    theta2 = theta + math.radians(extra_angle)
    tan2 = math.tan(theta2)
    horiz2 = W
    log.info(
        "Right stroke lean: %.1f° originally, now %.1f° (+%s°).",
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
    log.info("Here's the new V outline:")
    for label, pt in zip(labels, new_coords):
        log.info("  - %-18s %s", label, pt)

    stem_w = new_coords[1][0] - new_coords[0][0]
    right_w = new_coords[4][0] - new_coords[3][0]
    bottom_w = new_coords[5][0] - new_coords[6][0]
    log.info(
        "Width check - stem top %s, right top %s, bottom %s (all should match).",
        stem_w, right_w, bottom_w,
    )
    if not (stem_w == right_w == bottom_w == W):
        log.warning(
            "Those widths don't all match %s (got stem=%s, right=%s, bottom=%s). "
            "Worth a visual check.",
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
    log.info(
        "Updated spacing: advance width %s -> %s (kept the old right sidebearing of %s).",
        old_aw, new_aw, rsb,
    )

    return gname, math.degrees(theta), math.degrees(theta2)


def rename_font(font: TTFont, family_name: str, style: str):
    name = font["name"]
    full = f"{family_name} {style}".strip()
    ps = full.replace(" ", "")

    old_family = name.getDebugName(1)
    old_full = name.getDebugName(4)
    log.info(
        "Renaming font from %r (%r) to family %r, style %r.",
        old_family, old_full, family_name, style,
    )

    def setn(nameID, value):
        name.setName(value, nameID, 3, 1, 0x409)
        name.setName(value, nameID, 1, 0, 0)
        log.debug("  Name table entry %d set to %r", nameID, value)

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
    log.info("-- Building %s (%s) as '%s' --", src, style, fam_name)

    src_path = resolve_source(src, family)
    log_path(log, "Input font", src_path, level=20)

    try:
        font = TTFont(src_path)
    except Exception:
        log.exception("Couldn't open the font file at %s", src_path)
        raise

    log.debug("Font tables present: %s", sorted(font.keys()))
    log.info(
        "Font metrics: %s units per em, italic angle %s°.",
        font["head"].unitsPerEm, font["post"].italicAngle,
    )

    ensure_truetype(font)

    gname, old_deg, new_deg = rebuild_V(font, extra_angle)

    for tag in ("hdmx", "LTSH", "VDMX"):
        if tag in font:
            log.debug("Removing outdated metrics table %r (it no longer matches).", tag)
            del font[tag]

    rename_font(font, fam_name, style)

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    try:
        font.save(out_path)
    except Exception:
        log.exception("Couldn't save the new font to %s", out_path)
        raise

    log_path(log, "The new font", out_path, level=20)
    log.info(
        "Finished %s - V leans %.1f deg -> %.1f deg. Saved successfully.",
        style, old_deg, new_deg,
    )
    return gname, old_deg, new_deg


def build_family(family: Family, extra_angle: float = EXTRA_ANGLE) -> List[Tuple[str, Exception]]:
    log.info("")
    log.info("=== Starting family: %s (%s) ===", family.new_family, family.key)
    log_path(log, "Source folder", family_source_dir(family))
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
            log.error(
                "Sorry - %s / %s didn't build. Reason: %s",
                family.key, variant.style, exc,
            )
            log.debug("Full traceback:\n%s", traceback.format_exc())
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
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detail (debug) logs.",
    )
    parser.add_argument(
        "--angle",
        type=float,
        default=EXTRA_ANGLE,
        help=f"Extra degrees on the right stroke (default {EXTRA_ANGLE}).",
    )
    args = parser.parse_args(argv)

    set_verbose(log, args.verbose)

    keys = args.families if args.families else list(FAMILIES.keys())
    unknown = [k for k in keys if k not in FAMILIES]
    if unknown:
        log.error(
            "I don't know the family name(s) %s. Try one of: %s",
            unknown, ", ".join(sorted(FAMILIES)),
        )
        return 2

    log.info("Welcome - building SlashV fonts.")
    log.info("Project folder: %s", ROOT)
    log_path(log, "Source root", SOURCE_ROOT)
    log_path(log, "Output folder", OUT_DIR)
    log.info(
        "I'll build: %s. Right-stroke boost: +%s°.",
        ", ".join(keys), args.angle,
    )

    os.makedirs(OUT_DIR, exist_ok=True)

    all_errors = []
    for key in keys:
        all_errors.extend(build_family(FAMILIES[key], args.angle))

    log.info("")
    log.info("-- Summary --")
    if all_errors:
        log.error("%d style(s) couldn't be built:", len(all_errors))
        for label, exc in all_errors:
            log.error("  - %s - %s", label, exc)
        log.error("Scroll up for details. Fix the issue and run again when you're ready.")
        return 1

    log.info("All done - every requested style is ready in %s", OUT_DIR)
    log.info("Next tip: run run.bat (or install_fonts.ps1) to put them on Windows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
