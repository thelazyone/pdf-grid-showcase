#!/usr/bin/env python3
"""
Concatenate PDFs and/or raster images into one file, in argument order.

Each PDF contributes its pages in order; each image (PNG, JPEG, TIFF) becomes
one page. PyMuPDF opens images as a single-page document with an appropriate
page size.

If page sizes (media box width × height) differ across any page, prompts for
confirmation before writing the output.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Required libraries not found. Please install them using:")
    print("pip install PyMuPDF")
    sys.exit(1)

SIZE_TOL_PT = 0.5

IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".tif", ".tiff"})
PDF_EXTENSION = ".pdf"


def _is_supported_input(p: Path) -> bool:
    s = p.suffix.lower()
    return s == PDF_EXTENSION or s in IMAGE_EXTENSIONS


def _page_size_pt(page: fitz.Page) -> tuple[float, float]:
    r = page.mediabox
    return (r.width, r.height)


def collect_all_page_sizes(paths: Iterable[Path]) -> list[tuple[float, float]]:
    sizes: list[tuple[float, float]] = []
    for p in paths:
        doc = fitz.open(p)
        try:
            for i in range(len(doc)):
                sizes.append(_page_size_pt(doc.load_page(i)))
        finally:
            doc.close()
    return sizes


def sizes_uniform(sizes: list[tuple[float, float]]) -> bool:
    if len(sizes) <= 1:
        return True
    w0, h0 = sizes[0]
    for w, h in sizes[1:]:
        if abs(w - w0) > SIZE_TOL_PT or abs(h - h0) > SIZE_TOL_PT:
            return False
    return True


def unique_size_summary(sizes: list[tuple[float, float]]) -> str:
    seen: dict[tuple[float, float], int] = {}
    for w, h in sizes:
        key = (round(w, 2), round(h, 2))
        seen[key] = seen.get(key, 0) + 1
    parts = [f"{w:.1f}×{h:.1f} pt ({n} page{'s' if n != 1 else ''})" for (w, h), n in sorted(seen.items())]
    return "; ".join(parts)


def confirm_mixed_sizes(sizes: list[tuple[float, float]]) -> bool:
    print(
        "Warning: pages have different sizes (media box).\n"
        f"  {unique_size_summary(sizes)}\n"
        "Combining them as-is may look inconsistent in some viewers.\n"
        "Is it OK to continue?",
        file=sys.stderr,
    )
    if not sys.stdin.isatty():
        print(
            "No interactive terminal (stdin is not a TTY). Cannot prompt.\n"
            "Re-run in a terminal to answer y/n, or use --yes to skip this check.",
            file=sys.stderr,
        )
        return False
    while True:
        ans = input("OK to continue? [y/N]: ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no", ""):
            return False
        print("Please answer y or n.", file=sys.stderr)


def concatenate(paths: list[Path], output: Path) -> None:
    merged = fitz.open()
    try:
        for p in paths:
            src = fitz.open(p)
            try:
                if src.is_pdf:
                    merged.insert_pdf(src)
                else:
                    # Image-backed docs are not valid sources for insert_pdf().
                    pdf_bytes = src.convert_to_pdf()
                    img_pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
                    try:
                        merged.insert_pdf(img_pdf)
                    finally:
                        img_pdf.close()
            finally:
                src.close()
        merged.save(output)
    finally:
        merged.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Concatenate PDFs and/or images (PNG, JPEG, TIFF) in order into one PDF."
        )
    )
    parser.add_argument(
        "inputs",
        metavar="PATH",
        nargs="+",
        type=Path,
        help="Input PDF or image paths (order is preserved).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output PDF path.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Do not prompt when page sizes differ; merge anyway.",
    )
    args = parser.parse_args()

    paths = [p.resolve() for p in args.inputs]
    out = args.output.expanduser().resolve()

    for p in paths:
        if not p.is_file():
            print(f"Error: not a file: {p}", file=sys.stderr)
            sys.exit(1)
        if not _is_supported_input(p):
            exts = sorted(IMAGE_EXTENSIONS | {PDF_EXTENSION})
            print(
                f"Error: unsupported type {p.suffix!r} for {p} "
                f"(supported: {', '.join(exts)})",
                file=sys.stderr,
            )
            sys.exit(1)

    sizes = collect_all_page_sizes(paths)
    if sizes and (not sizes_uniform(sizes)) and not args.yes:
        if not confirm_mixed_sizes(sizes):
            print("Aborted.", file=sys.stderr)
            sys.exit(1)

    concatenate(paths, out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
