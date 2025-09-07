#!/usr/bin/env python3
"""
Image optimization script for Lane's Lexicon scanned pages.
Converts high-resolution colored images to black and white optimized versions
for text comparison and OCR purposes.
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageOps
import time

def get_file_size_mb(filepath):
    """Get file size in MB."""
    return os.path.getsize(filepath) / (1024 * 1024)

def optimize_image(input_path, output_path, method="resize_bw", scale_factor=0.25, file_format="PNG", quality=85):
    """
    Optimize image using resize_bw method with different file formats.
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path to save optimized image
        method (str): Optimization method (only "resize_bw" supported)
        scale_factor (float): Scaling factor for resize operations (default 0.25)
        file_format (str): Output file format ("PNG", "JPEG", "WEBP", "TIFF")
        quality (int): Quality for lossy formats (1-100)
    """
    
    print(f"Processing: {input_path}")
    print(f"Original size: {get_file_size_mb(input_path):.2f} MB")
    
    # Open image
    with Image.open(input_path) as img:
        original_size = img.size
        print(f"Original dimensions: {original_size}")
        
        # Resize and convert to grayscale (25% size)
        new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
        resized = img.resize(new_size, Image.Resampling.LANCZOS)
        grayscale = ImageOps.grayscale(resized)
        
        # Save in different formats
        if file_format == "PNG":
            grayscale.save(output_path, "PNG", optimize=True, compress_level=9)
        elif file_format == "JPEG":
            # Convert to RGB for JPEG (JPEG doesn't support grayscale directly)
            rgb_grayscale = grayscale.convert('RGB')
            output_path = output_path.replace('.png', '.jpg')
            rgb_grayscale.save(output_path, "JPEG", quality=quality, optimize=True)
        elif file_format == "WEBP":
            output_path = output_path.replace('.png', '.webp')
            grayscale.save(output_path, "WEBP", quality=quality, optimize=True)
        elif file_format == "TIFF":
            output_path = output_path.replace('.png', '.tiff')
            grayscale.save(output_path, "TIFF", compression="lzw", optimize=True)
    
    # Check results
    if os.path.exists(output_path):
        new_size_mb = get_file_size_mb(output_path)
        original_size_mb = get_file_size_mb(input_path)
        reduction = ((original_size_mb - new_size_mb) / original_size_mb) * 100
        
        print(f"Optimized size: {new_size_mb:.2f} MB")
        print(f"Size reduction: {reduction:.1f}%")
        print(f"Saved to: {output_path}")
        print("-" * 50)
        
        return {
            'method': method,
            'original_size_mb': original_size_mb,
            'new_size_mb': new_size_mb,
            'reduction_percent': reduction,
            'output_path': output_path
        }
    else:
        print(f"Error: Output file not created - {output_path}")
        return None

def test_optimization_methods(input_files, input_base_dir):
    """Test different optimization methods on sample files."""
    
    methods = [
        ("resize_25_webp_30", {"method": "resize_bw", "scale_factor": 0.25, "file_format": "WEBP", "quality": 30}),
    ]
    
    results = []
    
    for input_file in input_files:
        if not os.path.exists(input_file):
            print(f"Warning: Input file not found - {input_file}")
            continue
            
        filename = Path(input_file).stem
        
        # Determine output directory based on input folder
        input_folder = Path(input_file).parent.name
        if input_folder == "ba":
            output_dir = Path(input_base_dir) / "ba_min"
        elif input_folder == "ta":
            output_dir = Path(input_base_dir) / "ta_min"
        elif input_folder == "va":
            output_dir = Path(input_base_dir) / "va_min"
        else:
            print(f"Warning: Unknown folder {input_folder}, using ba_min")
            output_dir = Path(input_base_dir) / "ba_min"
        
        print(f"\n{'='*60}")
        print(f"TESTING FILE: {filename} (from {input_folder} folder)")
        print(f"Output directory: {output_dir}")
        print(f"{'='*60}")
        
        file_results = []
        
        for method_name, params in methods:
            # Create output directory for this folder
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Keep original filename, just change extension
            file_format = params.get("file_format", "PNG")
            if file_format == "PNG":
                output_file = output_dir / f"{filename}.png"
            elif file_format == "JPEG":
                output_file = output_dir / f"{filename}.jpg"
            elif file_format == "WEBP":
                output_file = output_dir / f"{filename}.webp"
            elif file_format == "TIFF":
                output_file = output_dir / f"{filename}.tiff"
            
            print(f"\nMethod: {method_name}")
            result = optimize_image(input_file, str(output_file), **params)
            if result:
                result['filename'] = filename
                file_results.append(result)
        
        results.extend(file_results)
    
    return results

def print_summary(results):
    """Print summary of optimization results."""
    print(f"\n{'='*80}")
    print("OPTIMIZATION SUMMARY")
    print(f"{'='*80}")
    
    # Group by method
    methods = {}
    for result in results:
        method = result['method']
        if method not in methods:
            methods[method] = []
        methods[method].append(result)
    
    for method, method_results in methods.items():
        avg_reduction = sum(r['reduction_percent'] for r in method_results) / len(method_results)
        avg_new_size = sum(r['new_size_mb'] for r in method_results) / len(method_results)
        
        print(f"\nMethod: {method}")
        print(f"  Average size reduction: {avg_reduction:.1f}%")
        print(f"  Average optimized size: {avg_new_size:.2f} MB")
        
        for result in method_results:
            print(f"    {result['filename']}: {result['original_size_mb']:.2f} MB → {result['new_size_mb']:.2f} MB ({result['reduction_percent']:.1f}% reduction)")

def main():
    # Configuration
    base_dir = Path(r"c:\Users\navee\OneDrive\lane\lan")
    input_base_dir = base_dir / "db" / "images"
    
    # Get all PNG files from ba, ta, and va folders
    folders_to_process = ["ba", "ta", "va"]
    test_files = []
    
    for folder in folders_to_process:
        folder_path = input_base_dir / folder
        if folder_path.exists():
            png_files = list(folder_path.glob("*.png"))
            test_files.extend(png_files)
            print(f"Found {len(png_files)} PNG files in {folder} folder")
        else:
            print(f"Warning: {folder} folder not found at {folder_path}")
    
    if not test_files:
        print("No PNG files found to process!")
        return 1
    
    print("Lane's Lexicon Image Optimization Tool - Final Production Run")
    print("=" * 50)
    print(f"Input base directory: {input_base_dir}")
    print(f"Total files to process: {len(test_files)}")
    print(f"Processing folders: {folders_to_process}")
    print("Using WebP quality 30 - optimal size/quality balance")
    print("Output will be saved to respective _min folders")
    
    # Check if Pillow is available
    try:
        from PIL import Image
        print(f"PIL/Pillow version: {Image.__version__}")
    except ImportError:
        print("Error: PIL/Pillow is not installed. Please install it with:")
        print("pip install Pillow")
        return 1
    
    # Test optimization methods
    start_time = time.time()
    results = test_optimization_methods([str(f) for f in test_files], input_base_dir)
    end_time = time.time()
    
    # Print summary
    if results:
        print_summary(results)
        print(f"\nTotal processing time: {end_time - start_time:.2f} seconds")
        print(f"\nOptimized images saved in respective _min folders")
        
        # Recommend best method
        best_method = min(results, key=lambda x: x['new_size_mb'])
        print(f"\nRecommended method for smallest size: {best_method['method']}")
        print(f"  Average size: {best_method['new_size_mb']:.2f} MB")
        print(f"  Reduction: {best_method['reduction_percent']:.1f}%")
    else:
        print("No results generated. Please check input files and try again.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
