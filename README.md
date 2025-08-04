# PDF Grid Showcase

A Python script that creates a mosaic image from all pages of a PDF file. I found myself too many times writing rulebooks for games and wanting to showcase the whole book in a single image. it's doable, but it usually implies Photoshop and/or online tools, just to create one single jpg.

## Installation

Simply install the Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python pdf_grid_showcase.py <path_to_pdf_file> [-o output_filename]
```

The script will:
1. Display the number of pages in your PDF
2. Ask you how many columns you want in the grid
3. Ask for the horizontal size (width) in pixels for each page
4. Create and save the mosaic image, with the same name of the input pdf

## Requirements

- Python 3.6+
- PyMuPDF (fitz)
- pillow