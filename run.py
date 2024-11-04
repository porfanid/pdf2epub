#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import sys
from typing import Optional
from marker.convert import convert_single_pdf
from marker.models import load_all_models
import json
import torch
import transformers

def setup_environment():
    """Set up the environment variables and configurations needed."""
    # Force CPU usage and set appropriate configurations
    os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Disable CUDA
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["TRANSFORMERS_ATTENTION_IMPLEMENTATION"] = "eager"
    # Set lower torch threads for CPU
    torch.set_num_threads(4)
    # Reduce logging noise
    transformers.utils.logging.set_verbosity_error()

def get_device_settings():
    """Configure device-specific settings."""
    device = torch.device('cpu')
    # Use float32 for CPU
    dtype = torch.float32
    return device, dtype

def convert_pdf(
    input_path: str,
    output_dir: Path,
    batch_multiplier: int = 1,  # Reduced default for CPU
    max_pages: Optional[int] = None,
    start_page: Optional[int] = None,
    langs: Optional[str] = None
) -> None:
    """
    Convert a single PDF file to markdown format.
    """
    try:
        # Set device specific settings
        device, dtype = get_device_settings()
        
        # Load models with specific device and dtype
        model_lst = load_all_models(device=device, dtype=dtype)
        
        # Convert languages string to list if provided
        languages = langs.split(',') if langs else None
        
        # Convert the PDF
        full_text, images, metadata = convert_single_pdf(
            input_path,
            model_lst,
            batch_multiplier=batch_multiplier,
            max_pages=max_pages,
            start_page=start_page,
            langs=languages
        )
        
        # Create output filename
        input_filename = Path(input_path).stem
        md_output = output_dir / f"{input_filename}.md"
        meta_output = output_dir / f"{input_filename}_metadata.json"
        
        # Save markdown content
        md_output.write_text(full_text, encoding='utf-8')
        
        # Save metadata
        meta_output.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        
        # Save images if any
        if images:
            print(f"Found {len(images)} images")
            print(f"Image types: {[type(img) for img in images]}")
            print(f"First image sample: {str(images[0])[:100] if images else 'No images'}")
            image_dir = output_dir / f"{input_filename}_images"
            image_dir.mkdir(exist_ok=True)
            for idx, img in enumerate(images):
                img_path = image_dir / f"image_{idx}.png"
                # Handle different types of image data
                if hasattr(img, 'save'):
                    # PIL Image object
                    img.save(img_path)
                elif isinstance(img, str):
                    # String path or data
                    with open(img_path, 'w', encoding='utf-8') as f:
                        f.write(img)
                elif isinstance(img, bytes):
                    # Binary data
                    with open(img_path, 'wb') as f:
                        f.write(img)
                else:
                    print(f"Warning: Skipping image {idx} - unsupported format: {type(img)}")
        
        print(f"Successfully converted {input_path}")
        print(f"Markdown saved to: {md_output}")
        print(f"Metadata saved to: {meta_output}")
        
    except Exception as e:
        print(f"Error converting {input_path}: {str(e)}", file=sys.stderr)
        raise

def setup_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Convert PDF files to Markdown format using marker-pdf',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'input_path',
        type=str,
        help='Path to input PDF file or directory containing PDFs'
    )
    parser.add_argument(
        'output_path',
        type=str,
        help='Path to output directory for markdown files'
    )
    parser.add_argument(
        '--batch-multiplier',
        type=int,
        default=1,  # Reduced default for CPU
        help='Multiplier for batch size (higher uses more memory but processes faster)'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help='Maximum number of pages to process (default: process all pages)'
    )
    parser.add_argument(
        '--start-page',
        type=int,
        default=None,
        help='Page number to start from (default: start from first page)'
    )
    parser.add_argument(
        '--langs',
        type=str,
        default=None,
        help='Comma-separated list of languages in the document (e.g., "English,Spanish")'
    )
    return parser

def main():
    # Set up environment before anything else
    setup_environment()
    
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Convert input and output paths to Path objects
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    if input_path.is_file():
        # Convert single PDF file
        if not input_path.suffix.lower() == '.pdf':
            print(f"Error: Input file must be a PDF, got: {input_path}", file=sys.stderr)
            sys.exit(1)
        
        convert_pdf(
            str(input_path),
            output_path,
            args.batch_multiplier,
            args.max_pages,
            args.start_page,
            args.langs
        )
    
    elif input_path.is_dir():
        # Convert all PDFs in directory
        pdf_files = list(input_path.glob('*.pdf'))
        if not pdf_files:
            print(f"No PDF files found in directory: {input_path}", file=sys.stderr)
            sys.exit(1)
        
        for pdf_file in pdf_files:
            print(f"\nProcessing: {pdf_file}")
            convert_pdf(
                str(pdf_file),
                output_path,
                args.batch_multiplier,
                args.max_pages,
                args.start_page,
                args.langs
            )
    
    else:
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()