#!/usr/bin/env python3
"""
Command-line interface for pdf2epub package.

This module provides a comprehensive CLI tool for converting PDF files to EPUB format
through an intermediate Markdown representation. It supports batch processing,
configurable AI postprocessing, and flexible output options.

Features:
- Single PDF or batch directory processing
- GPU acceleration detection and utilization
- Configurable conversion parameters (pages, languages, batch size)
- Optional AI-powered postprocessing for improved quality
- Flexible output control (skip markdown, skip EPUB, skip AI)
- Comprehensive logging and error handling

Workflow:
1. Parse command-line arguments and validate inputs
2. Detect and configure GPU/CPU processing capabilities  
3. Queue PDF files for processing (single file or directory scan)
4. For each PDF:
   a. Convert PDF to Markdown (unless --skip-md)
   b. Apply AI postprocessing (unless --skip-ai)
   c. Convert Markdown to EPUB (unless --skip-epub)
5. Report results and handle errors gracefully

Example usage:
    # Basic conversion
    pdf2epub document.pdf
    
    # Advanced options
    pdf2epub book.pdf --start-page 10 --max-pages 50 --langs "English,German"
    
    # Skip certain steps
    pdf2epub thesis.pdf --skip-epub --skip-ai
"""

import argparse
from pathlib import Path
import logging
import sys

# Import our package modules
from . import pdf2md, mark2epub
from .postprocessing.ai import AIPostprocessor

# Optional dependency: PyTorch for GPU acceleration
# Check availability for optimal performance configuration
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


def main():
    """
    Main CLI entry point with comprehensive argument parsing and workflow management.
    
    This function orchestrates the entire PDF to EPUB conversion process:
    1. Sets up logging and system capability detection
    2. Parses and validates command-line arguments
    3. Builds processing queue from input specification
    4. Processes each PDF through the conversion pipeline
    5. Handles errors gracefully with informative messages
    
    The function is designed to be robust and user-friendly, providing clear
    feedback at each step and continuing processing even if individual files fail.
    """
    # Configure comprehensive logging for user feedback
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Detect and report system capabilities for optimal performance
    if TORCH_AVAILABLE and torch.cuda.is_available():
        logger.info("CUDA is available. Using GPU for processing.")
        logger.info(f"GPU: {torch.cuda.get_device_name()}")
    elif TORCH_AVAILABLE:
        logger.info("CUDA is not available. Using CPU for processing.")
    else:
        logger.info("PyTorch not available. GPU acceleration disabled.")
        
    # Set up comprehensive argument parser with all conversion options
    parser = argparse.ArgumentParser(
        description='Convert PDF files to EPUB format via Markdown with AI postprocessing',
        epilog="""
Examples:
  %(prog)s document.pdf                    # Basic conversion
  %(prog)s book.pdf output/               # Specify output directory  
  %(prog)s --start-page 10 --max-pages 50 book.pdf  # Process specific pages
  %(prog)s --langs "English,German" multilang.pdf   # Specify languages
  %(prog)s --skip-epub document.pdf       # Only create markdown
  %(prog)s --skip-ai --skip-md existing/  # Only create EPUB from existing markdown
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input/Output arguments
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
    
    # PDF Processing arguments
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
    
    # Workflow control arguments
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
    parser.add_argument(
        '--ai-provider',
        type=str,
        default='anthropic',
        choices=['anthropic'],
        help='AI provider to use for postprocessing'
    )
    
    args = parser.parse_args()
    
    # Determine input path with fallback to default directory
    input_path = Path(args.input_path) if args.input_path else pdf2md.get_default_input_dir()
    
    # Build processing queue from input specification
    queue = pdf2md.add_pdfs_to_queue(input_path)
    logger.info(f"Found {len(queue)} PDF files to process")
    
    # Process each PDF in the queue
    for pdf_path in queue:
        logger.info(f"\nProcessing: {pdf_path.name}")
        logger.info(f"File size: {pdf_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Determine output paths for this PDF
        if args.output_path:
            output_path = Path(args.output_path)
            markdown_dir = output_path / pdf_path.stem
        else:
            markdown_dir = pdf2md.get_default_output_dir(pdf_path)
            output_path = markdown_dir.parent
            
        try:
            # Validate markdown directory if skipping MD generation
            if args.skip_md:
                if not markdown_dir.exists():
                    logger.error(f"Error: Markdown directory not found: {markdown_dir}")
                    logger.error("Cannot skip markdown generation without existing markdown files")
                    continue
                logger.info(f"Using existing markdown files from: {markdown_dir}")
                
            # Step 1: Convert PDF to Markdown (unless skipped)
            if not args.skip_md:
                logger.info("Converting PDF to Markdown...")
                logger.info(f"Output directory: {markdown_dir}")
                
                # Log conversion parameters for transparency
                if args.batch_multiplier != 2:
                    logger.info(f"Using batch multiplier: {args.batch_multiplier}")
                if args.max_pages:
                    logger.info(f"Processing maximum {args.max_pages} pages")
                if args.start_page:
                    logger.info(f"Starting from page {args.start_page}")
                if args.langs:
                    logger.info(f"Using languages: {args.langs}")
                
                pdf2md.convert_pdf(
                    str(pdf_path),
                    markdown_dir,
                    args.batch_multiplier,
                    args.max_pages,
                    args.start_page,
                    args.langs
                )
                logger.info("PDF to Markdown conversion completed successfully")
            
            # Step 2: Apply AI postprocessing (unless skipped)
            if not args.skip_ai:
                try:
                    markdown_file = markdown_dir / f"{pdf_path.stem}.md"
                    if markdown_file.exists():
                        logger.info("\nInitiating AI postprocessing analysis...")
                        logger.info(f"AI Provider: {args.ai_provider}")
                        logger.info("This may take several minutes depending on document length...")
                        
                        processor = AIPostprocessor(markdown_dir)
                        
                        # Run AI postprocessing with error handling
                        processor.run_postprocessing(
                            markdown_path=markdown_file,
                            ai_provider=args.ai_provider
                        )
                        
                        logger.info("AI postprocessing completed successfully")
                    else:
                        logger.warning(f"Warning: Markdown file not found for AI processing: {markdown_file}")
                        logger.warning("Skipping AI postprocessing for this file")
                        
                except Exception as e:
                    logger.error(f"Error during AI postprocessing: {e}")
                    logger.info("Proceeding with original markdown (AI postprocessing is optional)")
            
            # Step 3: Convert Markdown to EPUB (unless skipped)
            if not args.skip_epub:
                logger.info("Converting Markdown to EPUB...")
                logger.info(f"EPUB will be created in: {output_path}")
                
                mark2epub.convert_to_epub(markdown_dir, output_path)
                logger.info("EPUB conversion completed successfully")
                
                # Report final output location
                epub_file = markdown_dir / f"{markdown_dir.name}.epub"
                if epub_file.exists():
                    logger.info(f"Final EPUB: {epub_file}")
                    logger.info(f"EPUB size: {epub_file.stat().st_size / 1024 / 1024:.1f} MB")
            
            logger.info(f"Successfully completed processing: {pdf_path.name}")
                
        except Exception as e:
            # Log error but continue with other files
            logger.error(f"Error processing {pdf_path.name}: {str(e)}")
            logger.error("Continuing with next file...")
            continue

    logger.info("\nAll files processed. Conversion complete!")


if __name__ == '__main__':
    main()