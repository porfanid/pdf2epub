#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import sys
from typing import Optional
from marker.convert import convert_single_pdf
from marker.models import load_all_models
import json

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
        default=2,
        help='Multiplier for batch size (higher uses more VRAM but processes faster)'
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

def convert_pdf(
    input_path: str,
    output_dir: Path,
    batch_multiplier: int = 2,
    max_pages: Optional[int] = None,
    start_page: Optional[int] = None,
    langs: Optional[str] = None
) -> None:
    """
    Convert a single PDF file to markdown format.
    
    Args:
        input_path: Path to the input PDF file
        output_dir: Directory where markdown and metadata will be saved
        batch_multiplier: Multiplier for batch size
        max_pages: Maximum number of pages to process
        start_page: Page number to start from
        langs: Comma-separated list of languages
    """
    try:
        # Load models
        model_lst = load_all_models()
        
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
            image_dir = output_dir / f"{input_filename}_images"
            image_dir.mkdir(exist_ok=True)
            for idx, img in enumerate(images):
                img_path = image_dir / f"image_{idx}.png"
                img.save(img_path)
        
        print(f"Successfully converted {input_path}")
        print(f"Markdown saved to: {md_output}")
        print(f"Metadata saved to: {meta_output}")
        
    except Exception as e:
        print(f"Error converting {input_path}: {str(e)}", file=sys.stderr)
        raise

def main():
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