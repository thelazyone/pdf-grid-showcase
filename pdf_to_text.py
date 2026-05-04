#!/usr/bin/env python3
"""
PDF to Text

Extract plain text from a PDF and write it to a UTF-8 text file.
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Required libraries not found. Please install them using:")
    print("pip install PyMuPDF")
    sys.exit(1)


def extract_pdf_text(pdf_path: str, page_markers: bool) -> Tuple[str, int]:
    """Return full document text and word count (page body only, not markers)."""
    doc = fitz.open(pdf_path)
    try:
        chunks = []
        word_count = 0
        for i in range(len(doc)):
            page = doc.load_page(i)
            body = page.get_text().rstrip()
            word_count += len(body.split())
            if page_markers:
                chunks.append(f"--- Page {i + 1} ---\n{body}")
            else:
                chunks.append(body)
        text = "\n\n".join(chunks).rstrip() + "\n"
        return text, word_count
    finally:
        doc.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract text from a PDF into a UTF-8 text file"
    )
    parser.add_argument("pdf", help="Path to the input PDF file")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output .txt path (default: same name as the PDF with .txt extension)",
    )
    parser.add_argument(
        "--no-page-markers",
        action="store_true",
        help="Do not insert --- Page N --- lines between pages",
    )

    args = parser.parse_args()
    pdf_path = Path(args.pdf)
    if not pdf_path.is_file():
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    out_path = (
        Path(args.output)
        if args.output
        else pdf_path.with_suffix(".txt")
    )

    try:
        text, words = extract_pdf_text(
            str(pdf_path), page_markers=not args.no_page_markers
        )
    except Exception as e:
        print(f"Error reading PDF: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        out_path.write_text(text, encoding="utf-8", newline="\n")
    except OSError as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        sys.exit(1)

    print(
        f"Wrote {len(text)} characters ({words} words) to {out_path}"
    )


if __name__ == "__main__":
    main()
