#!/usr/bin/env python3
import argparse
from pathlib import Path
import modules.pdf2md as pdf2md

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
    
    # Get input path
    input_path = Path(args.input_path) if args.input_path else pdf2md.get_default_input_dir()
    
    # Get queue of PDFs to process
    queue = pdf2md.add_pdfs_to_queue(input_path)
    print(f"Found {len(queue)} PDF files to process")
    
    # Process each PDF
    for pdf_path in queue:
        # Get output directory for this PDF
        if args.output_path:
            # If output path specified, create subdirectory for each PDF
            output_path = Path(args.output_path) / pdf_path.stem
        else:
            # Use default next to each PDF
            output_path = pdf2md.get_default_output_dir(pdf_path)
            
        print(f"\nProcessing: {pdf_path.name}")
        
        # Convert the PDF
        pdf2md.convert_pdf(
            str(pdf_path),
            output_path,
            args.batch_multiplier,
            args.max_pages,
            args.start_page,
            args.langs
        )

if __name__ == '__main__':
    main()