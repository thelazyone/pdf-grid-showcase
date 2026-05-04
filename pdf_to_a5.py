#!/usr/bin/env python3
"""
PDF page scaler

Target size can be given as pixel width and height plus DPI (converted to PDF
points), or as a paper preset (mm-accurate). Each page is drawn with vector
preservation via show_pdf_page: same aspect as target → scale only; otherwise a
symmetric axis-aligned crop on the long dimension, then scale to fill.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Required libraries not found. Please install them using:")
    print("pip install PyMuPDF")
    sys.exit(1)

MM_TO_PT = 72.0 / 25.4

# ISO 216 page sizes in mm (width x height, portrait).
PAPER_MM: dict[str, Tuple[float, float]] = {
    "a6": (105.0, 148.0),
    "a5": (148.0, 210.0),
    "a4": (210.0, 297.0),
    "a3": (297.0, 420.0),
}


def paper_dimensions_pt(mm_key: str, landscape: bool) -> Tuple[float, float]:
    k = mm_key.lower().strip()
    if k not in PAPER_MM:
        raise ValueError(
            f"Unknown paper preset {mm_key!r}; try: {', '.join(sorted(PAPER_MM))}"
        )
    pw_mm, ph_mm = PAPER_MM[k]
    if landscape:
        pw_mm, ph_mm = ph_mm, pw_mm
    return pw_mm * MM_TO_PT, ph_mm * MM_TO_PT


def pixels_to_pts(width_px: float, height_px: float, dpi: float) -> Tuple[float, float]:
    if dpi <= 0:
        raise ValueError("DPI must be positive")
    s = 72.0 / dpi
    return width_px * s, height_px * s


def cover_aspect_clip(src_rect: fitz.Rect, target_w: float, target_h: float) -> fitz.Rect:
    """Smallest axis-aligned clip of src_rect with the same aspect as target."""
    tw, th = target_w, target_h
    sw, sh = src_rect.width, src_rect.height
    if sw <= 0 or sh <= 0:
        return src_rect
    sa = sw / sh
    ta = tw / th
    if abs(sa - ta) < 1e-6:
        return src_rect
    if sa > ta:
        new_w = sh * ta
        x0 = src_rect.x0 + (sw - new_w) / 2
        return fitz.Rect(x0, src_rect.y0, x0 + new_w, src_rect.y0 + sh)
    new_h = sw / ta
    y0 = src_rect.y0 + (sh - new_h) / 2
    return fitz.Rect(src_rect.x0, y0, src_rect.x0 + sw, y0 + new_h)


def scale_pdf_pages(inp: str, outp: str, target_w_pt: float, target_h_pt: float) -> None:
    target = fitz.Rect(0, 0, target_w_pt, target_h_pt)

    src = fitz.open(inp)
    try:
        dst = fitz.open()
        try:
            for i in range(len(src)):
                sp = src.load_page(i)
                clip = cover_aspect_clip(sp.rect, target_w_pt, target_h_pt)
                dp = dst.new_page(width=target_w_pt, height=target_h_pt)
                dp.show_pdf_page(target, src, i, clip=clip)
        finally:
            dst.save(outp)
            dst.close()
    finally:
        src.close()


def _parse_paper_arg(raw: str) -> Tuple[str, bool]:
    """Return (PAPER_MM key, landscape). Accepts e.g. a5, a5-landscape, a5l."""
    r = raw.lower().strip().replace("_", "-")
    if r.endswith("-landscape"):
        base = r[: -len("-landscape")].rstrip("-")
        return base, True
    if len(r) >= 2 and r.endswith("l") and r[:-1] in PAPER_MM:
        return r[:-1], True
    return r, False


def parse_pixel_size(spec: str) -> Tuple[int, int]:
    s = spec.strip().lower().replace("*", "x")
    parts = [p.strip() for p in s.replace("×", "x").split("x")]
    if len(parts) != 2:
        raise ValueError("Expected WIDTHxHEIGHT in pixels (e.g. 1748x2480)")
    return int(parts[0]), int(parts[1])


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Scale each PDF page to a target size: use --size WxH or "
            "--width-px/--height-px (with --dpi), or --paper for ISO sizes. "
            "Aspect ratio is kept; mismatch is handled with a centered crop."
        ),
    )
    parser.add_argument("pdf", help="Path to the input PDF file")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output PDF path (default: input basename + _scaled.pdf)",
    )
    parser.add_argument(
        "--width-px",
        type=int,
        default=None,
        metavar="W",
        help="Target page width in pixels (use with --height-px)",
    )
    parser.add_argument(
        "--height-px",
        type=int,
        default=None,
        metavar="H",
        help="Target page height in pixels (use with --width-px)",
    )
    parser.add_argument(
        "--size",
        type=str,
        default=None,
        metavar="WxH",
        help="Target size as WIDTHxHEIGHT pixels (alternative to --width-px/--height-px)",
    )
    parser.add_argument(
        "--dpi",
        type=float,
        default=300.0,
        help="Resolution for converting pixels to PDF points (default: 300)",
    )
    parser.add_argument(
        "--paper",
        type=str,
        default=None,
        metavar="NAME",
        help=(
            "Paper preset by ISO size, e.g. a5, a4, a6, or a5-landscape / a5l. "
            "Ignored when pixel size is set (--size or --width-px/--height-px)."
        ),
    )
    parser.add_argument(
        "--landscape",
        action="store_true",
        help="With --paper only: swap width and height (landscape)",
    )

    args = parser.parse_args()

    tw_pt: float
    th_pt: float
    label: str

    wpx: Optional[int] = args.width_px
    hpx: Optional[int] = args.height_px
    if args.size is not None:
        if wpx is not None or hpx is not None:
            print(
                "Error: use either --size or --width-px/--height-px, not both.",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            sw, sh = parse_pixel_size(args.size)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        wpx, hpx = sw, sh

    have_px = wpx is not None or hpx is not None
    if have_px:
        if wpx is None or hpx is None:
            print(
                "Error: --width-px and --height-px must be given together "
                "(or use --size WxH).",
                file=sys.stderr,
            )
            sys.exit(1)
        wx, hx = wpx, hpx
        if wx <= 0 or hx <= 0:
            print("Error: pixel dimensions must be positive.", file=sys.stderr)
            sys.exit(1)
        tw_pt, th_pt = pixels_to_pts(float(wx), float(hx), args.dpi)
        label = f"{wx}x{hx}px @ {args.dpi:g} DPI"
    else:
        paper_arg = args.paper if args.paper is not None else "a5"
        base, land = _parse_paper_arg(paper_arg)
        land = land or args.landscape
        tw_pt, th_pt = paper_dimensions_pt(base, land)
        label = f"paper {base.upper()}" + (" landscape" if land else "")

    pdf_path = Path(args.pdf)
    if not pdf_path.is_file():
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    out_path = (
        Path(args.output)
        if args.output
        else pdf_path.with_name(pdf_path.stem + "_scaled.pdf")
    )

    try:
        scale_pdf_pages(str(pdf_path), str(out_path), tw_pt, th_pt)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {label} ({tw_pt:.2f}x{th_pt:.2f} pt): {out_path}")


if __name__ == "__main__":
    main()
