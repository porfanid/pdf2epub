#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import json
from marker.convert import convert_single_pdf
from marker.models import load_all_models

def get_default_output_dir(input_path: Path) -> Path:
    """
    Generate default output directory path based on input PDF path.
    Creates a directory with same name as PDF (without extension) next to the PDF.
    """
    return input_path.parent / input_path.stem

def get_default_input_dir() -> Path:
    """
    Get default input directory (./input) relative to current working directory.
    Creates it if it doesn't exist.
    """
    input_dir = Path.cwd() / 'input'
    input_dir.mkdir(exist_ok=True)
    return input_dir

def convert_pdf(
    input_path: str,
    output_dir: Path,
    batch_multiplier: int = 2,
    max_pages: int = None,
    start_page: int = None,
    langs: str = None
) -> None:
    """
    Convert a single PDF file to markdown format.
    
    Args:
        input_path: Path to the input PDF file
        output_dir: Directory where output files will be saved
        batch_multiplier: Multiplier for batch size (higher uses more memory but processes faster)
        max_pages: Maximum number of pages to process (None for all pages)
        start_page: Page number to start from (None for first page)
        langs: Comma-separated list of languages in the document
    """
    try:
        # Load models
        model_lst = load_all_models()
        
        # Convert languages string to list if provided
        languages = [lang.strip() for lang in langs.split(',')] if langs else None
        
        # Convert the PDF
        full_text, images, metadata = convert_single_pdf(
            input_path,
            model_lst,
            batch_multiplier=batch_multiplier,
            max_pages=max_pages,
            start_page=start_page,
            langs=languages
        )
        
        # All output will go to the output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save markdown content
        md_output = output_dir / f"{Path(input_path).stem}.md"
        md_output.write_text(full_text, encoding='utf-8')
        print(f"Markdown saved to: {md_output}")
        
        # Save metadata as JSON
        meta_output = output_dir / f"{Path(input_path).stem}_metadata.json"
        with open(meta_output, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to: {meta_output}")
        
        # Handle images if present
        if images:
            image_dir = output_dir / "images"
            image_dir.mkdir(exist_ok=True)
            
            for idx, image_data in enumerate(images.values()):
                image_path = image_dir / f"image_{idx}.png"
                if isinstance(image_data, (str, bytes)):
                    mode = 'wb' if isinstance(image_data, bytes) else 'w'
                    with open(image_path, mode) as f:
                        f.write(image_data)
            
            print(f"Images saved to: {image_dir}")
            
    except Exception as e:
        print(f"Error converting {input_path}: {str(e)}", file=sys.stderr)
        sys.exit(1)

def get_input_path(path_arg: str | None) -> Path:
    """
    Determine input path based on argument or default directory.
    """
    if path_arg:
        path = Path(path_arg)
        # If it's a directory, look for PDFs in it
        if path.is_dir():
            pdfs = list(path.glob('*.pdf'))
            if not pdfs:
                print(f"No PDF files found in directory: {path}", file=sys.stderr)
                sys.exit(1)
            return pdfs[0]  # Return first PDF found
        return path
    else:
        # Use default input directory
        input_dir = get_default_input_dir()
        pdfs = list(input_dir.glob('*.pdf'))
        if not pdfs:
            print(f"No PDF files found in default input directory: {input_dir}", file=sys.stderr)
            print("Please place PDF files in the 'input' directory or specify an input path.", file=sys.stderr)
            sys.exit(1)
        return pdfs[0]  # Return first PDF found

def main():
    parser = argparse.ArgumentParser(
        description='Convert PDF files to Markdown format using marker-pdf'
    )
    parser.add_argument(
        'input_path',
        nargs='?',  # Make argument optional
        type=str,
        help='Path to input PDF file or directory (default: ./input/*.pdf)'
    )
    parser.add_argument(
        'output_path',
        nargs='?',  # Make argument optional
        type=str,
        help='Path to output directory (default: directory named after PDF)'
    )
    parser.add_argument(
        '--batch-multiplier',
        type=int,
        default=2,
        help='Multiplier for batch size (higher uses more memory but processes faster)'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help='Maximum number of pages to process'
    )
    parser.add_argument(
        '--start-page',
        type=int,
        default=None,
        help='Page number to start from'
    )
    parser.add_argument(
        '--langs',
        type=str,
        default=None,
        help='Comma-separated list of languages in the document'
    )
    
    args = parser.parse_args()
    
    # Get input path (with smart defaults)
    input_path = get_input_path(args.input_path)
    
    # Validate input file
    if not input_path.is_file():
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)
    if input_path.suffix.lower() != '.pdf':
        print(f"Error: Input file must be a PDF: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # Get output directory (with smart defaults)
    output_path = Path(args.output_path) if args.output_path else get_default_output_dir(input_path)
    
    # Convert the PDF
    convert_pdf(
        str(input_path),
        output_path,
        args.batch_multiplier,
        args.max_pages,
        args.start_page,
        args.langs
    )

if __name__ == '__main__':
    main()