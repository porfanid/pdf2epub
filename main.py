#!/usr/bin/env python3
import argparse
from pathlib import Path
import modules.pdf2md as pdf2md
import modules.mark2epub as mark2epub
from modules.postprocessing.ai import AIPostprocessor
import torch

def main():
    if torch.cuda.is_available():
        print("CUDA is available. Using GPU for processing.")
    else:
        print("CUDA is not available. Using CPU for processing.")
        
    parser = argparse.ArgumentParser(
        description='Convert PDF files to EPUB format via Markdown with optional AI postprocessing'
    )
    parser.add_argument(
        'input_path',
        nargs='?',
        type=str,
        help='Path to input PDF file or directory (default: ./input/*.pdf)'
    )
    parser.add_argument(
        'output_path',
        nargs='?',
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
    parser.add_argument(
        '--skip-epub',
        action='store_true',
        help='Skip EPUB generation, only create markdown'
    )
    parser.add_argument(
        '--skip-md',
        action='store_true',
        help='Skip markdown generation, use existing markdown files'
    )
    parser.add_argument(
        '--skip-ai',
        action='store_true',
        help='Skip AI postprocessing step'
    )
    
    args = parser.parse_args()
    
    # Get input path
    input_path = Path(args.input_path) if args.input_path else pdf2md.get_default_input_dir()
    
    # Get queue of PDFs to process
    queue = pdf2md.add_pdfs_to_queue(input_path)
    print(f"Found {len(queue)} PDF files to process")
    
    # Process each PDF
    for pdf_path in queue:
        print(f"\nProcessing: {pdf_path.name}")
        
        # Get output directory for this PDF
        if args.output_path:
            output_path = Path(args.output_path)
            markdown_dir = output_path / pdf_path.stem
        else:
            markdown_dir = pdf2md.get_default_output_dir(pdf_path)
            output_path = markdown_dir.parent
            
        try:
            # Check if markdown directory exists when skipping MD generation
            if args.skip_md:
                if not markdown_dir.exists():
                    print(f"Error: Markdown directory not found: {markdown_dir}")
                    continue
                print(f"Using existing markdown files from: {markdown_dir}")
                
            # Convert PDF to Markdown unless skipped
            if not args.skip_md:
                print("Converting PDF to Markdown...")
                pdf2md.convert_pdf(
                    str(pdf_path),
                    markdown_dir,
                    args.batch_multiplier,
                    args.max_pages,
                    args.start_page,
                    args.langs
                )
            
            # Handle AI postprocessing if not skipped
            if not args.skip_ai:
                try:
                    markdown_file = markdown_dir / f"{pdf_path.stem}.md"
                    if markdown_file.exists():
                        print("\nInitiating AI postprocessing analysis...")
                        ai_processor = AIPostprocessor(markdown_dir)
                        should_process, json_path = ai_processor.analyze_with_claude(markdown_file)
                        
                        if should_process and json_path:
                            print("Running AI postprocessing...")
                            if not ai_processor.run_postprocessing(markdown_file, json_path):
                                print("Warning: AI postprocessing failed, proceeding with original markdown")
                        else:
                            print("Skipping AI postprocessing")
                    else:
                        print(f"Warning: Markdown file not found for AI processing: {markdown_file}")
                except Exception as e:
                    print(f"Error during AI postprocessing: {e}")
                    print("Proceeding with original markdown")
            
            # Convert Markdown to EPUB unless skipped
            if not args.skip_epub:
                print("Converting Markdown to EPUB...")
                mark2epub.convert_to_epub(markdown_dir, output_path)
                
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {str(e)}")
            continue

if __name__ == '__main__':
    main()