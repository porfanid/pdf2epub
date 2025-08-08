"""
PDF2EPUB: Convert PDF files to EPUB format via Markdown with intelligent layout detection.

This package provides functionality to convert PDF files to EPUB format through an
intermediate Markdown representation, with optional AI-powered postprocessing for
improved output quality.

Main modules:
- pdf2md: PDF to Markdown conversion
- mark2epub: Markdown to EPUB conversion
- postprocessing: AI-powered postprocessing with plugin architecture

Example usage:
    >>> import pdf2epub
    >>> pdf2epub.convert_pdf_to_markdown("document.pdf", "output_dir")
    >>> pdf2epub.convert_markdown_to_epub("output_dir", "final_output")
"""

from .pdf2md import (
    convert_pdf,
    add_pdfs_to_queue,
    get_default_output_dir,
    get_default_input_dir,
)
from .mark2epub import convert_to_epub
from .postprocessing.ai import AIPostprocessor

__version__ = "0.1.0"
__author__ = "porfanid"

# Public API
__all__ = [
    # PDF to Markdown conversion
    "convert_pdf",
    "add_pdfs_to_queue",
    "get_default_output_dir",
    "get_default_input_dir",
    # Markdown to EPUB conversion
    "convert_to_epub",
    # AI Postprocessing
    "AIPostprocessor",
]


def convert_pdf_to_markdown(pdf_path: str, output_dir: str, **kwargs) -> None:
    """
    Convert a PDF file to Markdown format.

    Args:
        pdf_path: Path to the input PDF file
        output_dir: Directory to save the markdown output
        **kwargs: Additional options (batch_multiplier, max_pages, start_page, langs)
    """
    from pathlib import Path

    convert_pdf(pdf_path, Path(output_dir), **kwargs)


def convert_markdown_to_epub(markdown_dir: str, output_path: str) -> None:
    """
    Convert Markdown files to EPUB format.

    Args:
        markdown_dir: Directory containing markdown files
        output_path: Output directory for EPUB file
    """
    from pathlib import Path

    convert_to_epub(Path(markdown_dir), Path(output_path))
