"""
PDF2EPUB: Convert PDF files to EPUB format via Markdown with intelligent layout detection.

This package provides a comprehensive solution for converting PDF documents to EPUB
e-books through an intermediate Markdown representation. It combines advanced PDF
parsing, AI-powered postprocessing, and EPUB generation to create high-quality
e-books that preserve document structure and formatting.

Architecture Overview:
===================

The package follows a modular pipeline architecture:

1. **PDF to Markdown (pdf2md)**: Uses marker-pdf for intelligent PDF parsing
   - Advanced layout detection and text extraction
   - Image extraction and optimization
   - Metadata preservation
   - Language-aware OCR processing

2. **AI Postprocessing (postprocessing)**: Optional quality improvement
   - Pattern-based error detection and correction
   - AI-powered analysis using Claude API
   - Extensible plugin architecture for multiple AI providers
   - Graceful fallbacks when AI services are unavailable

3. **Markdown to EPUB (mark2epub)**: EPUB 3.0 compliant book generation
   - Interactive metadata collection
   - Professional styling and formatting
   - Image optimization for e-readers
   - Cross-platform compatibility

4. **Command Line Interface (cli)**: User-friendly command-line tool
   - Batch processing capabilities
   - Flexible workflow control
   - Comprehensive logging and error handling

Public API Design:
================

The package provides both convenience functions for common workflows and
direct access to core functionality for advanced use cases:

Convenience Functions:
    convert_pdf_to_markdown() - High-level PDF to Markdown conversion
    convert_markdown_to_epub() - High-level Markdown to EPUB conversion

Core Functions:
    convert_pdf() - Direct PDF conversion with full parameter control
    convert_to_epub() - Direct EPUB generation
    AIPostprocessor - AI-powered content improvement

Example usage:
    >>> import pdf2epub
    >>> pdf2epub.convert_pdf_to_markdown("document.pdf", "output/")
    >>> pdf2epub.convert_markdown_to_epub("output/", "final/")

Advanced usage:
    >>> processor = pdf2epub.AIPostprocessor(work_dir)
    >>> processor.run_postprocessing(markdown_file, "anthropic")

Dependencies:
============

Core Dependencies (always required):
    - markdown>=3.7: Markdown to HTML conversion with extensions

Optional Dependencies (installed with pdf2epub[full]):
    - marker-pdf: Advanced PDF parsing and layout detection
    - anthropic: AI postprocessing via Claude API
    - Pillow: Image processing and optimization
    - torch: GPU acceleration for PDF processing

The package is designed with graceful degradation - missing optional
dependencies will disable related features but won't break core functionality.
"""

# Import core conversion functions from modules
from .pdf2md import convert_pdf, add_pdfs_to_queue, get_default_output_dir, get_default_input_dir
from .mark2epub import convert_to_epub
from .postprocessing.ai import AIPostprocessor

# Package metadata
__version__ = "0.1.0"
__author__ = "porfanid"

# Comprehensive public API with clear categorization
__all__ = [
    # PDF to Markdown conversion functions
    "convert_pdf",              # Core PDF conversion with full parameter control
    "add_pdfs_to_queue",       # Batch processing queue management
    "get_default_output_dir",  # Output directory path generation
    "get_default_input_dir",   # Input directory path generation
    
    # Markdown to EPUB conversion functions
    "convert_to_epub",         # Core EPUB generation functionality
    
    # AI Postprocessing classes
    "AIPostprocessor",         # AI-powered content improvement
]


def convert_pdf_to_markdown(pdf_path: str, output_dir: str, **kwargs) -> None:
    """
    Convert a PDF file to Markdown format with intelligent layout detection.
    
    This convenience function provides a simplified interface to the core PDF
    conversion functionality. It handles path conversion and provides sensible
    defaults for most use cases.
    
    Args:
        pdf_path: Path to the input PDF file (relative or absolute)
        output_dir: Directory to save the markdown output and images
        **kwargs: Additional conversion options passed to convert_pdf():
            - batch_multiplier (int): Memory vs speed trade-off (default: 2)
            - max_pages (int): Maximum pages to process (default: None = all)
            - start_page (int): Starting page number (default: None = beginning)
            - langs (str): Comma-separated language list for OCR (default: None)
    
    Example:
        >>> convert_pdf_to_markdown("document.pdf", "output/")
        >>> convert_pdf_to_markdown("book.pdf", "output/", max_pages=50, langs="English,German")
    """
    from pathlib import Path
    convert_pdf(pdf_path, Path(output_dir), **kwargs)


def convert_markdown_to_epub(markdown_dir: str, output_path: str) -> None:
    """
    Convert Markdown files to EPUB format with professional styling.
    
    This convenience function provides a simplified interface to EPUB generation.
    It automatically handles metadata collection, image processing, and EPUB
    packaging according to EPUB 3.0 specifications.
    
    Args:
        markdown_dir: Directory containing markdown files and images
        output_path: Output directory where the EPUB file will be created
    
    Note:
        The function will interactively prompt for metadata (title, author, etc.)
        and optionally allow review of markdown content before conversion.
    
    Example:
        >>> convert_markdown_to_epub("markdown_output/", "final_books/")
    """
    from pathlib import Path
    convert_to_epub(Path(markdown_dir), Path(output_path))
