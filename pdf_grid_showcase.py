#!/usr/bin/env python3
"""
PDF Mosaic Creator

This script creates a mosaic image from all pages of a PDF file.
The user can specify the number of columns and the horizontal size of each page.
"""

import sys
import os
import io
import argparse
from typing import List, Tuple
from PIL import Image, ImageDraw
import math

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Required libraries not found. Please install them using:")
    print("pip install PyMuPDF pillow")
    sys.exit(1)


def get_pdf_page_count(pdf_path: str) -> int:
    """Get the number of pages in a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        return page_count
    except Exception as e:
        print(f"Error reading PDF: {e}")
        sys.exit(1)


def get_user_input() -> Tuple[int, int]:
    """Get user input for columns and horizontal size."""
    while True:
        try:
            columns = int(input("How many columns should the grid have? "))
            if columns > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")

    while True:
        try:
            width = int(input("What should be the horizontal size (width) in pixels of each page? "))
            if width > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")

    return columns, width


def convert_pdf_to_images(pdf_path: str, target_width: int) -> List[Image.Image]:
    """Convert PDF pages to PIL Images with specified width."""
    print("Converting PDF pages to images...")
    
    try:
        doc = fitz.open(pdf_path)
        images = []
        
        for page_num in range(len(doc)):
            print(f"Processing page {page_num + 1}/{len(doc)}")
            
            # Get the page
            page = doc.load_page(page_num)
            
            # Calculate zoom factor to achieve target width
            page_rect = page.rect
            original_width = page_rect.width
            zoom_factor = target_width / original_width
            
            # Create transformation matrix
            mat = fitz.Matrix(zoom_factor, zoom_factor)
            
            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            images.append(img)
            
            # Clean up
            pix = None
        
        doc.close()
        return images
    
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        sys.exit(1)


def create_mosaic(images: List[Image.Image], columns: int) -> Image.Image:
    """Create a mosaic image from the list of page images."""
    if not images:
        raise ValueError("No images to create mosaic")
    
    num_pages = len(images)
    rows = math.ceil(num_pages / columns)
    
    # All images should have the same width (we resized them), but heights might vary
    page_width = images[0].width
    page_height = max(img.height for img in images)  # Use max height for consistency
    
    # Calculate mosaic dimensions
    mosaic_width = columns * page_width
    mosaic_height = rows * page_height
    
    print(f"Creating mosaic: {mosaic_width}x{mosaic_height} pixels")
    print(f"Grid: {rows} rows × {columns} columns")
    
    # Create black background
    mosaic = Image.new('RGB', (mosaic_width, mosaic_height), color='black')
    
    # Place images in the mosaic
    for i, img in enumerate(images):
        row = i // columns
        col = i % columns
        
        # For the last row, check if we need to center the remaining images
        if row == rows - 1:  # Last row
            remaining_pages = num_pages - (row * columns)
            if remaining_pages < columns:
                # Center the remaining pages
                offset = (columns - remaining_pages) * page_width // 2
                x = col * page_width + offset
            else:
                x = col * page_width
        else:
            x = col * page_width
        
        y = row * page_height
        
        # Center the image vertically if it's shorter than page_height
        if img.height < page_height:
            y_offset = (page_height - img.height) // 2
            y += y_offset
        
        mosaic.paste(img, (x, y))
        print(f"Placed page {i + 1} at position ({x}, {y})")
    
    return mosaic


def main():
    parser = argparse.ArgumentParser(description='Create a mosaic from PDF pages')
    parser.add_argument('pdf_file', help='Path to the PDF file')
    parser.add_argument('-o', '--output', help='Output image file (default: same name as PDF with .png extension)', 
                        default=None)
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.exists(args.pdf_file):
        print(f"Error: PDF file '{args.pdf_file}' not found.")
        sys.exit(1)
    
    # Set default output filename if not specified
    if args.output is None:
        # Get the base filename without extension and add .png
        base_name = os.path.splitext(os.path.basename(args.pdf_file))[0]
        args.output = f"{base_name}.png"
    
    # Get number of pages
    print(f"Reading PDF: {args.pdf_file}")
    page_count = get_pdf_page_count(args.pdf_file)
    print(f"PDF has {page_count} pages.")
    
    # Get user input
    columns, width = get_user_input()
    
    print(f"\nConfiguration:")
    print(f"- PDF file: {args.pdf_file}")
    print(f"- Pages: {page_count}")
    print(f"- Columns: {columns}")
    print(f"- Page width: {width} pixels")
    print(f"- Rows needed: {math.ceil(page_count / columns)}")
    
    # Convert PDF to images
    images = convert_pdf_to_images(args.pdf_file, width)
    
    # Create mosaic
    print("\nCreating mosaic...")
    mosaic = create_mosaic(images, columns)
    
    # Save mosaic
    print(f"Saving mosaic to: {args.output}")
    mosaic.save(args.output, quality=95, optimize=True)
    
    print(f"\nMosaic created successfully!")
    print(f"Output file: {args.output}")
    print(f"Dimensions: {mosaic.width}x{mosaic.height} pixels")


if __name__ == "__main__":
    main()