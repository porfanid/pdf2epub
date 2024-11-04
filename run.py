#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import json
from marker.convert import convert_single_pdf
from marker.models import load_all_models

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
        
        # Create output paths
        input_filename = Path(input_path).stem
        md_output = output_dir / f"{input_filename}.md"
        meta_output = output_dir / f"{input_filename}_metadata.json"
        
        # Save markdown content
        md_output.write_text(full_text, encoding='utf-8')
        print(f"Markdown saved to: {md_output}")
        
        # Save metadata as JSON
        with open(meta_output, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to: {meta_output}")
        
        # Handle images if present
        if images:
            image_dir = output_dir / f"{input_filename}_images"
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

def main():
    parser = argparse.ArgumentParser(
        description='Convert PDF files to Markdown format using marker-pdf'
    )
    parser.add_argument(
        'input_path',
        type=str,
        help='Path to input PDF file'
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
    
    # Convert paths to Path objects
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)
    
    # Validate input file
    if not input_path.is_file():
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)
    if input_path.suffix.lower() != '.pdf':
        print(f"Error: Input file must be a PDF: {input_path}", file=sys.stderr)
        sys.exit(1)
        
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
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