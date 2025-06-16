import sys
import os
from PIL import Image, ImageOps
import numpy as np
import argparse
import math

#!/usr/bin/env python3


def main():
    parser = argparse.ArgumentParser(description='Convert PNG image to SVG with individual pixel paths')
    parser.add_argument('input', help='Input PNG file')
    parser.add_argument('-o', '--output', help='Output SVG file')
    parser.add_argument('--max-size', type=int, default=500, help='Maximum dimension (width or height) for image processing')
    parser.add_argument('--max-colors', type=int, default=256, help='Maximum number of colors for the SVG')
    parser.add_argument('--force-full', action='store_true', help='Force processing the full image without simplification')
    args = parser.parse_args()

    # Check if input file exists
    if not os.path.isfile(args.input):
        print(f"Error: Input file '{args.input}' does not exist")
        sys.exit(1)
    
    # Set output file if not specified
    if args.output is None:
        base_name = os.path.splitext(args.input)[0]
        args.output = f"{base_name}.svg"
    
    # Load the image
    try:
        img = Image.open(args.input).convert('RGBA')
    except Exception as e:
        print(f"Error opening image: {e}")
        sys.exit(1)
    
    original_width, original_height = img.size
    
    # Check if image needs to be resized
    is_too_large = original_width > args.max_size or original_height > args.max_size
    if is_too_large and not args.force_full:
        print(f"Image is large ({original_width}x{original_height}). Resizing...")
        # Calculate scaling factor to fit within max_size
        scale_factor = min(args.max_size / original_width, args.max_size / original_height)
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        print(f"Resized to {new_width}x{new_height}")
    
    width, height = img.size
    pixels = np.array(img)
    
    # Extract unique colors (ignoring alpha for now)
    unique_colors = {}
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y][x]
            if a > 0:  # Only include visible pixels
                color_key = f"#{r:02x}{g:02x}{b:02x}"
                if color_key not in unique_colors:
                    unique_colors[color_key] = []
                unique_colors[color_key].append((x, y))
    
    # Check if there are too many colors
    color_count = len(unique_colors)
    point_count = sum(len(points) for points in unique_colors.values())
    print(f"Found {color_count} unique colors across {point_count} points")
    
    # Assess SVG complexity before proceeding
    is_complex, recommendation = assess_svg_complexity(width, height, color_count, point_count)
    
    if is_complex and not args.force_full:
        print(f"WARNING: {recommendation}")
        
        if not args.force_full and input("Proceed with automatic optimization? [Y/n]: ").lower() != 'n':
            if color_count > args.max_colors:
                print(f"Simplifying from {color_count} colors to {args.max_colors} colors...")
                
                # Use our improved quantization method
                img_quantized = quantize_with_dither(img, args.max_colors)
                
                # Replace our image with the quantized version
                img = img_quantized
                pixels = np.array(img)
                
                # Re-extract unique colors
                unique_colors = {}
                for y in range(height):
                    for x in range(width):
                        r, g, b, a = pixels[y][x]
                        if a > 0:  # Only include visible pixels
                            color_key = f"#{r:02x}{g:02x}{b:02x}"
                            if color_key not in unique_colors:
                                unique_colors[color_key] = []
                            unique_colors[color_key].append((x, y))
                
                print(f"Reduced to {len(unique_colors)} colors")
        else:
            print("Continuing with original image parameters. The resulting SVG may be very large.")
    elif color_count > args.max_colors and not args.force_full:
        print(f"Too many colors ({color_count}). Simplifying to {args.max_colors} colors...")
        
        # Use our improved quantization method
        img_quantized = quantize_with_dither(img, args.max_colors)
        
        # Replace our image with the quantized version
        img = img_quantized
        pixels = np.array(img)
        
        # Re-extract unique colors
        unique_colors = {}
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[y][x]
                if a > 0:  # Only include visible pixels
                    color_key = f"#{r:02x}{g:02x}{b:02x}"
                    if color_key not in unique_colors:
                        unique_colors[color_key] = []
                    unique_colors[color_key].append((x, y))
        
        print(f"Reduced to {len(unique_colors)} colors")
    
    # Generate SVG
    svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
'''
    
    # Create paths for each color using a more efficient algorithm for large image/color sets
    for color, points in unique_colors.items():
        if len(points) > 1000:
            # For colors with many pixels, use a more efficient path approach
            # Group adjacent pixels into rectangles where possible
            rects = []
            pixels_set = set(points)
            
            while pixels_set:
                x, y = next(iter(pixels_set))
                pixels_set.remove((x, y))
                
                # Try to expand horizontally
                width = 1
                while (x + width, y) in pixels_set:
                    pixels_set.remove((x + width, y))
                    width += 1
                
                # Try to expand vertically (check if all pixels in the row are present)
                height = 1
                can_expand = True
                while can_expand:
                    # Check if all pixels in the next row are present
                    for dx in range(width):
                        if (x + dx, y + height) not in pixels_set:
                            can_expand = False
                            break
                    
                    if can_expand:
                        # Remove all pixels in this row
                        for dx in range(width):
                            pixels_set.remove((x + dx, y + height))
                        height += 1
                
                rects.append((x, y, width, height))
            
            # Create path from rectangles
            path_data = ""
            for x, y, w, h in rects:
                path_data += f"M{x} {y}h{w}v{h}h-{w}z "
        else:
            # For colors with fewer pixels, use the original approach
            path_data = ""
            for x, y in points:
                path_data += f"M{x} {y}h1v1h-1z "
        
        svg_content += f'  <path fill="{color}" d="{path_data}" />\n'
    
    svg_content += '</svg>'
    
    # Write to output file
    try:
        with open(args.output, 'w') as f:
            f.write(svg_content)
        
        # Calculate SVG file size and provide summary
        svg_size = os.path.getsize(args.output) / 1024  # Size in KB
        
        print(f"Successfully converted {args.input} to {args.output}")
        print(f"SVG Statistics:")
        print(f"  - Image dimensions: {width}x{height}")
        print(f"  - Unique colors: {len(unique_colors)}")
        print(f"  - SVG file size: {svg_size:.2f} KB")
        
        # Provide warning if the SVG is still large
        if svg_size > 5000:  # If larger than 5MB
            print(f"\nWARNING: The generated SVG is quite large ({svg_size:.2f} KB).")
            print("Consider using smaller images or fewer colors for better performance.")
            print(f"Try: python {os.path.basename(__file__)} {args.input} --max-size 300 --max-colors 64")
        
        # Assess SVG complexity and provide recommendations
        point_count = sum(len(points) for points in unique_colors.values())
        is_complex, recommendation = assess_svg_complexity(width, height, len(unique_colors), point_count)
        if is_complex:
            print("\nWARNING: The generated SVG may be complex to render.")
            print(f"Recommendation: {recommendation}")
    except Exception as e:
        print(f"Error writing SVG file: {e}")
        sys.exit(1)


def assess_svg_complexity(width, height, color_count, point_count):
    """
    Assess if an SVG is likely to be renderable in a browser without performance issues.
    Returns a tuple of (is_complex, recommendation) where recommendation is None if not complex.
    """
    # These thresholds are estimates and may need adjustment based on testing
    MAX_TOTAL_PIXELS = 250000  # 500x500
    MAX_TOTAL_PATHS = 100000
    MAX_RECOMMENDED_COLORS = 64
    
    total_pixels = width * height
    is_complex = False
    recommendation = None
    
    if total_pixels > MAX_TOTAL_PIXELS and point_count > MAX_TOTAL_PATHS:
        is_complex = True
        new_size = int(math.sqrt(MAX_TOTAL_PIXELS))
        recommendation = f"This image is complex ({width}x{height} with {color_count} colors). "
        recommendation += f"Try --max-size {new_size} --max-colors {min(color_count, MAX_RECOMMENDED_COLORS)}"
    elif total_pixels > MAX_TOTAL_PIXELS:
        is_complex = True
        new_size = int(math.sqrt(MAX_TOTAL_PIXELS))
        recommendation = f"This image is large ({width}x{height}). Try --max-size {new_size}"
    elif color_count > MAX_RECOMMENDED_COLORS and point_count > MAX_TOTAL_PATHS:
        is_complex = True
        recommendation = f"This image has many colors ({color_count}). Try --max-colors {MAX_RECOMMENDED_COLORS}"
    
    return is_complex, recommendation


def quantize_with_dither(img, max_colors):
    """
    Apply color quantization with dithering for better visual quality
    while reducing color count.
    """
    # Convert to P mode (palette) with dithering for better visual quality
    img_rgb = img.convert('RGB')
    img_quantized = img_rgb.convert(
        'P', 
        palette=Image.ADAPTIVE, 
        colors=max_colors,
        dither=Image.FLOYDSTEINBERG
    )
    
    # Convert back to RGBA
    img_result = img_quantized.convert('RGBA')
    
    # Copy alpha channel from original image
    alpha = img.getchannel('A')
    img_result.putalpha(alpha)
    
    return img_result


if __name__ == "__main__":
    main()