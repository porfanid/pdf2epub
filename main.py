#!/usr/bin/env python3
import argparse
from pathlib import Path
import logging
import pdf2epub.pdf2md as pdf2md
import pdf2epub.mark2epub as mark2epub
from pdf2epub.postprocessing.ai import AIPostprocessor
import torch


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Check CUDA availability
    if torch.cuda.is_available():
        logger.info("CUDA is available. Using GPU for processing.")
    elif torch.mps.is_available():
        logger.info("MPS is available. Using Apple Silicon for processing.")
    else:
        logger.info("CUDA is not available. Using CPU for processing.")

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Convert PDF files to EPUB format via Markdown with AI postprocessing"
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        type=str,
        help="Path to input PDF file or directory (default: ./input/*.pdf)",
    )
    parser.add_argument(
        "output_path",
        nargs="?",
        type=str,
        help="Path to output directory (default: directory named after PDF)",
    )
    parser.add_argument(
        "--batch-multiplier",
        type=int,
        default=2,
        help="Multiplier for batch size (higher uses more memory but processes faster)",
    )
    parser.add_argument(
        "--max-pages", type=int, default=None, help="Maximum number of pages to process"
    )
    parser.add_argument(
        "--start-page", type=int, default=None, help="Page number to start from"
    )
    parser.add_argument(
        "--langs",
        type=str,
        default=None,
        help="Comma-separated list of languages in the document",
    )
    parser.add_argument(
        "--skip-epub",
        action="store_true",
        help="Skip EPUB generation, only create markdown",
    )
    parser.add_argument(
        "--skip-md",
        action="store_true",
        help="Skip markdown generation, use existing markdown files",
    )
    parser.add_argument(
        "--skip-ai", action="store_true", help="Skip AI postprocessing step"
    )
    parser.add_argument(
        "--ai-provider",
        type=str,
        default="anthropic",
        choices=["anthropic"],
        help="AI provider to use for postprocessing",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear model cache and exit (useful for fixing model loading issues)",
    )

    args = parser.parse_args()

    # Handle cache clearing request
    if args.clear_cache:
        logger.info("Clearing model cache...")
        success = pdf2md.clear_model_cache()
        if success:
            logger.info("Model cache cleared successfully")
        else:
            logger.info("No cache found to clear or cache clearing failed")
        return

    # Get input path
    input_path = (
        Path(args.input_path) if args.input_path else pdf2md.get_default_input_dir()
    )

    # Get queue of PDFs to process
    queue = pdf2md.add_pdfs_to_queue(input_path)
    logger.info(f"Found {len(queue)} PDF files to process")

    # Process each PDF
    for pdf_path in queue:
        logger.info(f"\nProcessing: {pdf_path.name}")

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
                    logger.error(f"Error: Markdown directory not found: {markdown_dir}")
                    continue
                logger.info(f"Using existing markdown files from: {markdown_dir}")

            # Convert PDF to Markdown unless skipped
            if not args.skip_md:
                logger.info("Converting PDF to Markdown...")
                pdf2md.convert_pdf(
                    str(pdf_path),
                    markdown_dir,
                    args.batch_multiplier,
                    args.max_pages,
                    args.start_page,
                    args.langs,
                )

            # Handle AI postprocessing if not skipped
            if not args.skip_ai:
                try:
                    markdown_file = markdown_dir / f"{pdf_path.stem}.md"
                    if markdown_file.exists():
                        logger.info("\nInitiating AI postprocessing analysis...")
                        processor = AIPostprocessor(markdown_dir)

                        # Run AI postprocessing
                        processor.run_postprocessing(
                            markdown_path=markdown_file, ai_provider=args.ai_provider
                        )

                        logger.info("AI postprocessing completed successfully")
                    else:
                        logger.warning(
                            f"Warning: Markdown file not found for AI processing: {markdown_file}"
                        )
                except Exception as e:
                    logger.error(f"Error during AI postprocessing: {e}")
                    logger.info("Proceeding with original markdown")

            # Convert Markdown to EPUB unless skipped
            if not args.skip_epub:
                logger.info("Converting Markdown to EPUB...")
                mark2epub.convert_to_epub(markdown_dir, output_path)
                logger.info("EPUB conversion completed")

        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {str(e)}")

            # Provide troubleshooting information for common errors
            if "'encoder'" in str(e) or "KeyError" in str(e):
                logger.info("This appears to be a model loading issue.")
                logger.info("Try running: python3 main.py --clear-cache")
                logger.info("Then retry your conversion.")

            continue


if __name__ == "__main__":
    main()
