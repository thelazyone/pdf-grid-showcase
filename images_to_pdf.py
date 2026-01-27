#!/usr/bin/env python3
"""
Images to PDF Converter

This script combines all images from a folder into a single PDF file.
Images are fitted to A4 pages at 300 DPI with margins.
Horizontal images are automatically rotated to fit better on the page.
"""

import sys
import os
import io
import argparse
from pathlib import Path
from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Required libraries not found. Please install them using:")
    print("pip install PyMuPDF pillow")
    sys.exit(1)


# A4 dimensions at 300 DPI (in pixels)
# A4 is 210mm × 297mm = 8.27in × 11.69in
# At 300 DPI: 2480 × 3508 pixels
A4_WIDTH_PX = 2480
A4_HEIGHT_PX = 3508

# Convert pixels to points (72 DPI for PDF)
# 1 inch = 72 points = 300 pixels (at 300 DPI)
# So: points = pixels * 72 / 300
A4_WIDTH_PT = A4_WIDTH_PX * 72 / 300
A4_HEIGHT_PT = A4_HEIGHT_PX * 72 / 300

# Supported image extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp'}


def get_images_from_folder(folder_path: str) -> list:
    """Get all image files from the specified folder."""
    image_files = []
    
    try:
        folder = Path(folder_path)
        if not folder.exists():
            print(f"Error: Folder '{folder_path}' not found.")
            sys.exit(1)
        
        if not folder.is_dir():
            print(f"Error: '{folder_path}' is not a directory.")
            sys.exit(1)
        
        # Get all image files
        for file_path in sorted(folder.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                image_files.append(file_path)
        
        return image_files
    
    except Exception as e:
        print(f"Error reading folder: {e}")
        sys.exit(1)


def images_to_pdf(image_files: list, output_pdf: str, margin_mm: float = 10.0, jpeg_quality: int = 85):
    """Convert a list of image files to a PDF with A4 pages at 300 DPI.
    
    Args:
        image_files: List of image file paths
        output_pdf: Output PDF filename
        margin_mm: Margin size in millimeters (default: 10mm)
        jpeg_quality: JPEG compression quality 1-100 (default: 85)
    """
    if not image_files:
        print("No images found in the specified folder.")
        sys.exit(1)
    
    print(f"Found {len(image_files)} images")
    print(f"Page size: A4 (210mm × 297mm) at 300 DPI")
    print(f"Margins: {margin_mm}mm")
    print(f"JPEG quality: {jpeg_quality}")
    
    # Convert margin from mm to pixels at 300 DPI
    # 1 inch = 25.4mm, 300 DPI means 300 pixels per inch
    margin_px = int(margin_mm * 300 / 25.4)
    
    # Calculate usable area (A4 - margins)
    usable_width_px = A4_WIDTH_PX - (2 * margin_px)
    usable_height_px = A4_HEIGHT_PX - (2 * margin_px)
    
    try:
        # Create a new PDF document
        pdf_doc = fitz.open()
        
        for i, img_path in enumerate(image_files, 1):
            print(f"Processing image {i}/{len(image_files)}: {img_path.name}")
            
            try:
                # Open the image with PIL
                img = Image.open(img_path)
                
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        rgb_img.paste(img, mask=img.split()[-1] if len(img.split()) > 3 else None)
                        img = rgb_img
                
                # Check if image is horizontal (landscape)
                img_width, img_height = img.size
                is_horizontal = img_width > img_height
                
                # Rotate horizontal images 90 degrees clockwise
                if is_horizontal:
                    img = img.rotate(-90, expand=True)
                    img_width, img_height = img.size
                    print(f"  → Rotated (was horizontal: {img_height}×{img_width} → {img_width}×{img_height})")
                
                # Calculate scaling factor to fit within usable area
                width_scale = usable_width_px / img_width
                height_scale = usable_height_px / img_height
                scale = min(width_scale, height_scale)
                
                # Calculate new dimensions
                new_width_px = int(img_width * scale)
                new_height_px = int(img_height * scale)
                
                # Resize the image
                img = img.resize((new_width_px, new_height_px), Image.Resampling.LANCZOS)
                
                # Save to a temporary bytes buffer with JPEG compression
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', quality=jpeg_quality, optimize=True)
                img_buffer.seek(0)
                
                # Create a new A4 page
                page = pdf_doc.new_page(width=A4_WIDTH_PT, height=A4_HEIGHT_PT)
                
                # Calculate position to center the image (in points)
                # Convert pixels to points for positioning
                new_width_pt = new_width_px * 72 / 300
                new_height_pt = new_height_px * 72 / 300
                margin_pt = margin_px * 72 / 300
                
                x_offset = (A4_WIDTH_PT - new_width_pt) / 2
                y_offset = (A4_HEIGHT_PT - new_height_pt) / 2
                
                # Insert the image centered on the page
                rect = fitz.Rect(x_offset, y_offset, x_offset + new_width_pt, y_offset + new_height_pt)
                page.insert_image(rect, stream=img_buffer.getvalue())
                
                print(f"  → Scaled to {new_width_px}×{new_height_px}px, centered on page")
                
            except Exception as e:
                print(f"Warning: Could not process {img_path.name}: {e}")
                continue
        
        # Delete existing file if it exists
        if os.path.exists(output_pdf):
            print(f"\nRemoving existing file: {output_pdf}")
            os.remove(output_pdf)
        
        # Save the PDF
        print(f"Saving PDF to: {output_pdf}")
        total_pages = len(pdf_doc)
        pdf_doc.save(output_pdf)
        pdf_doc.close()
        
        print(f"PDF created successfully!")
        print(f"Output file: {output_pdf}")
        print(f"Total pages: {total_pages}")
    
    except Exception as e:
        print(f"Error creating PDF: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Convert images from a folder to a PDF with A4 pages')
    parser.add_argument('folder', help='Path to the folder containing images')
    parser.add_argument('-o', '--output', help='Output PDF file (default: folder name with .pdf extension)', 
                        default=None)
    parser.add_argument('-m', '--margin', type=float, default=10.0,
                        help='Margin size in millimeters (default: 10mm)')
    parser.add_argument('-q', '--quality', type=int, default=85,
                        help='JPEG compression quality 1-100 (default: 85, higher=better quality/larger file)')
    
    args = parser.parse_args()
    
    # Validate quality
    if args.quality < 1 or args.quality > 100:
        print("Error: Quality must be between 1 and 100")
        sys.exit(1)
    
    # Get all image files from the folder
    image_files = get_images_from_folder(args.folder)
    
    # Set default output filename if not specified
    if args.output is None:
        # Use the folder name as the PDF name
        folder_name = os.path.basename(os.path.normpath(args.folder))
        args.output = f"{folder_name}.pdf"
    
    # Convert images to PDF
    images_to_pdf(image_files, args.output, args.margin, args.quality)


if __name__ == "__main__":
    main()

