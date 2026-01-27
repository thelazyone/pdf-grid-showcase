#!/usr/bin/env python3
"""
green_remover.py - Replace specific green color with bright light blue in images

Usage: python green_remover.py <folder_path> [replacement_color]

Arguments:
    folder_path       - Path to folder containing images
    replacement_color - Optional hex color (default: #00D4FF - bright light blue)

Examples:
    python green_remover.py cards
    python green_remover.py cards #FF00FF
"""

import sys
import os
from pathlib import Path
from PIL import Image
import numpy as np


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def replace_color(image_path, target_color, replacement_color, tolerance=10):
    """
    Replace target_color with replacement_color in the image
    
    Args:
        image_path: Path to the image file
        target_color: RGB tuple of color to replace (e.g., (90, 126, 38))
        replacement_color: RGB tuple of new color (e.g., (0, 212, 255))
        tolerance: Color matching tolerance (default 10)
    """
    # Open image and convert to RGBA for proper handling
    img = Image.open(image_path)
    img = img.convert('RGBA')
    
    # Convert to numpy array for efficient processing
    data = np.array(img)
    
    # Extract RGB channels
    r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    
    # Create mask for pixels that match the target color (within tolerance)
    mask = (
        (np.abs(r.astype(int) - target_color[0]) <= tolerance) &
        (np.abs(g.astype(int) - target_color[1]) <= tolerance) &
        (np.abs(b.astype(int) - target_color[2]) <= tolerance)
    )
    
    # Count matching pixels
    pixel_count = np.sum(mask)
    
    # Replace the color
    data[mask, 0] = replacement_color[0]  # Red channel
    data[mask, 1] = replacement_color[1]  # Green channel
    data[mask, 2] = replacement_color[2]  # Blue channel
    
    # Convert back to image
    result_img = Image.fromarray(data)
    
    # Convert back to original mode if it was RGB
    original_mode = Image.open(image_path).mode
    if original_mode == 'RGB':
        result_img = result_img.convert('RGB')
    
    return result_img, pixel_count


def process_folder(folder_path, target_color_hex='#5a7e26', replacement_color_hex='#00D4FF'):
    """
    Process all images in the folder and replace the target color
    
    Args:
        folder_path: Path to folder containing images
        target_color_hex: Hex color to replace (default: #5a7e26)
        replacement_color_hex: Hex color to use as replacement (default: #00D4FF - bright light blue)
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist")
        return
    
    if not folder.is_dir():
        print(f"Error: '{folder_path}' is not a directory")
        return
    
    # Convert hex colors to RGB
    target_rgb = hex_to_rgb(target_color_hex)
    replacement_rgb = hex_to_rgb(replacement_color_hex)
    
    print(f"Processing images in: {folder_path}")
    print(f"Replacing color {target_color_hex} {target_rgb} with {replacement_color_hex} {replacement_rgb}")
    print("-" * 60)
    
    # Supported image formats
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    
    # Find all image files
    image_files = [f for f in folder.iterdir() 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"No image files found in '{folder_path}'")
        return
    
    processed_count = 0
    total_pixels_replaced = 0
    
    for image_file in image_files:
        try:
            print(f"Processing: {image_file.name}...", end=" ")
            
            # Process the image
            result_img, pixel_count = replace_color(
                image_file, 
                target_rgb, 
                replacement_rgb,
                tolerance=10
            )
            
            # Save with _processed suffix (or overwrite - you can choose)
            # For safety, I'll save with a suffix first
            output_path = image_file.parent / f"{image_file.stem}_processed{image_file.suffix}"
            
            # Save the image with good quality
            if image_file.suffix.lower() in ['.jpg', '.jpeg']:
                result_img.save(output_path, quality=95)
            else:
                result_img.save(output_path)
            
            print(f"OK ({pixel_count:,} pixels replaced)")
            processed_count += 1
            total_pixels_replaced += pixel_count
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("-" * 60)
    print(f"Complete! Processed {processed_count}/{len(image_files)} images")
    print(f"Total pixels replaced: {total_pixels_replaced:,}")
    print(f"\nProcessed images saved with '_processed' suffix")


def main():
    if len(sys.argv) < 2:
        print("Usage: python green_remover.py <folder_path> [replacement_color]")
        print("\nArguments:")
        print("  folder_path       - Path to folder containing images")
        print("  replacement_color - Optional hex color (e.g., #00D4FF)")
        print("                      Default: #00D4FF (bright light blue)")
        print("\nExamples:")
        print("  python green_remover.py cards")
        print("  python green_remover.py cards #FF00FF")
        print("  python green_remover.py /path/to/images #FFFFFF")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    replacement_color = sys.argv[2] if len(sys.argv) > 2 else '#00D4FF'
    
    # Validate hex color format
    if not replacement_color.startswith('#'):
        replacement_color = '#' + replacement_color
    
    if len(replacement_color) != 7:
        print(f"Error: Invalid hex color '{replacement_color}'. Must be in format #RRGGBB")
        sys.exit(1)
    
    process_folder(folder_path, replacement_color_hex=replacement_color)


if __name__ == "__main__":
    main()
