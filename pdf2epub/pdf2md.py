"""
PDF to Markdown conversion module using marker-pdf for intelligent layout detection.

This module provides functionality to convert PDF files to Markdown format with
enhanced image handling and metadata preservation. It uses the marker-pdf library
for advanced PDF parsing that maintains document structure and formatting.

Key features:
- Batch processing with configurable memory usage
- Intelligent image extraction and optimization
- Language-aware text recognition
- Metadata preservation in JSON format
- Graceful fallbacks for missing dependencies
"""

import argparse
from pathlib import Path
import sys
import json

# Optional dependency: PIL for image processing
# If not available, image processing will be skipped with warnings
try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

import io


def validate_model_list(model_lst) -> bool:
    """
    Validate that the model list from marker-pdf has the expected structure.

    This function checks that all required models are present and have the
    necessary attributes to prevent runtime errors during PDF processing.

    Args:
        model_lst: List of models returned by load_all_models()

    Returns:
        bool: True if models are valid, False otherwise

    Raises:
        ValueError: If critical model validation fails
    """
    if not isinstance(model_lst, list):
        raise ValueError(f"Expected model list, got {type(model_lst)}")

    if len(model_lst) != 6:
        raise ValueError(f"Expected 6 models, got {len(model_lst)}")

    model_names = ["texify", "layout", "order", "detection", "ocr", "table_rec"]

    for i, (model, name) in enumerate(zip(model_lst, model_names)):
        # Check for processor attribute (required by marker-pdf)
        if not hasattr(model, "processor"):
            print(f"Warning: {name} model (index {i}) missing processor attribute")
            return False

        # Check model has basic required methods/attributes
        if not hasattr(model, "__call__") and not hasattr(model, "forward"):
            print(f"Warning: {name} model appears to be missing callable interface")

        # For encoder-decoder models, check key attributes exist
        if hasattr(model, "config"):
            config = model.config
            # Check for encoder-related configuration
            if hasattr(config, "encoder") or hasattr(config, "decoder"):
                print(f"Model {name} has encoder/decoder configuration")

        # Check if model has encoder attribute directly
        if hasattr(model, "encoder"):
            print(f"Model {name} has encoder attribute")

    print("All models passed basic validation")
    return True


def print_troubleshooting_info(error: Exception) -> None:
    """
    Print helpful troubleshooting information for common PDF conversion errors.

    Args:
        error: The exception that occurred during conversion
    """
    error_str = str(error)
    error_type = type(error).__name__

    print(f"\n=== PDF2EPUB Troubleshooting Information ===")
    print(f"Error: {error_type}: {error_str}")

    if "'encoder'" in error_str or "encoder" in error_str.lower():
        print("\nEncoder-related error detected. Common causes:")
        print("1. Model version incompatibility between marker-pdf and dependencies")
        print("2. Incomplete or corrupted model download from HuggingFace")
        print("3. Network interruption during initial model download")
        print("4. Insufficient disk space for model cache")

        print("\nSuggested fixes:")
        print("1. Clear HuggingFace cache: rm -rf ~/.cache/huggingface/")
        print(
            '   Or use: python3 -c "from pdf2epub.pdf2md import clear_model_cache; clear_model_cache()"'
        )
        print(
            "2. Reinstall marker-pdf: pip uninstall marker-pdf && pip install marker-pdf==0.3.10"
        )
        print("3. Check available disk space")
        print("4. Ensure stable internet connection for model downloads")

    elif (
        "memory" in error_str.lower()
        or "oom" in error_str.lower()
        or "out of memory" in error_str.lower()
    ):
        print("\nMemory-related error detected:")
        print("1. Reduce batch_multiplier (try 1)")
        print("2. Process fewer pages at once using --max-pages")
        print("3. Close other applications to free memory")

    elif "cuda" in error_str.lower() or "gpu" in error_str.lower():
        print("\nGPU-related error detected:")
        print("1. CUDA/GPU drivers may be incompatible")
        print("2. Try running with CPU only")
        print("3. Check GPU memory availability")

    elif (
        "connection" in error_str.lower()
        or "network" in error_str.lower()
        or "huggingface.co" in error_str.lower()
    ):
        print("\nNetwork-related error detected:")
        print("1. Check internet connection")
        print("2. Models need to download on first run")
        print("3. Consider using offline mode after initial download")

    print("===============================================\n")


def get_default_output_dir(input_path: Path) -> Path:
    """
    Generate default output directory path based on input PDF path.

    Creates a directory with the same name as the PDF file (without extension)
    located in the same directory as the input PDF. This follows the convention
    of keeping related files together for easy organization.

    Args:
        input_path: Path to the input PDF file

    Returns:
        Path to the output directory (e.g., "/path/to/document.pdf" -> "/path/to/document/")

    Example:
        >>> get_default_output_dir(Path("/docs/report.pdf"))
        Path("/docs/report")
    """
    return input_path.parent / input_path.stem


def get_default_input_dir() -> Path:
    """
    Get default input directory (./input) relative to current working directory.

    This function provides a standardized location for input PDFs when no specific
    path is provided. It creates the directory if it doesn't exist, ensuring the
    application can always find a place to look for input files.

    Returns:
        Path to the input directory, guaranteed to exist

    Example:
        >>> get_default_input_dir()
        Path("/current/working/directory/input")
    """
    input_dir = Path.cwd() / "input"
    input_dir.mkdir(exist_ok=True)  # Create directory if it doesn't exist
    return input_dir


def save_images(images: dict, image_dir: Path) -> None:
    """
    Save images with proper error handling and format detection.

    This function handles the complex task of saving images extracted from PDFs
    in various formats. It preserves original filenames and handles different
    image data types that may be returned by the marker-pdf library.

    Args:
        images: Dictionary of images from marker-pdf conversion where keys are filenames
                and values can be PIL Image objects, bytes, or file paths
        image_dir: Directory to save images to (will be created if it doesn't exist)

    Note:
        Requires PIL/Pillow for image processing. If not available, the function
        will skip image processing and print a warning.
    """
    # Check if PIL is available for image processing
    if not PIL_AVAILABLE:
        print("PIL/Pillow not available, skipping image processing")
        return

    # Handle case where no images were extracted
    if not images:
        print("No images found in document")
        return

    # Ensure the output directory exists
    image_dir.mkdir(exist_ok=True)
    saved_count = 0

    # Process each image in the dictionary
    for filename, image_data in images.items():
        try:
            # Skip empty or None image data
            if not image_data:
                continue

            image_path = image_dir / filename

            # Handle different image data formats returned by marker-pdf
            if isinstance(image_data, Image.Image):
                # Direct PIL Image object - save directly
                image_data.save(image_path)
                saved_count += 1

            elif isinstance(image_data, bytes):
                # Raw image bytes - convert to PIL Image first
                img = Image.open(io.BytesIO(image_data))
                img.save(image_path)
                saved_count += 1

            elif isinstance(image_data, str):
                # File path string - check if file exists and copy
                if Path(image_data).exists():
                    img = Image.open(image_data)
                    img.save(image_path)
                    saved_count += 1
                else:
                    print(f"Image path does not exist: {image_data}")
            else:
                # Unknown data type - log warning and skip
                print(f"Unsupported image data type for {filename}: {type(image_data)}")

        except Exception as e:
            # Continue processing other images even if one fails
            print(f"Error saving image {filename}: {str(e)}")
            continue

    # Report results to user
    if saved_count > 0:
        print(f"Successfully saved {saved_count} images to: {image_dir}")
    else:
        print("No valid images were found to save")


def convert_pdf(
    input_path: str,
    output_dir: Path,
    batch_multiplier: int = 2,
    max_pages: int = None,
    start_page: int = None,
    langs: str = None,
) -> None:
    """
    Convert a single PDF file to markdown format with enhanced image handling.

    This is the core conversion function that uses marker-pdf for intelligent
    PDF parsing. It extracts text, images, and metadata while preserving
    document structure and formatting as much as possible.

    Args:
        input_path: Path to the input PDF file
        output_dir: Directory to save the markdown output and associated files
        batch_multiplier: Controls memory usage vs speed trade-off (higher = more memory, faster processing)
        max_pages: Maximum number of pages to process (None = all pages)
        start_page: Page number to start from (1-indexed, None = start from beginning)
        langs: Comma-separated string of languages in the document for better OCR (e.g., "English,German")

    Raises:
        ImportError: If marker-pdf is not installed
        FileNotFoundError: If input PDF doesn't exist
        SystemExit: If conversion fails

    Output Files:
        - {pdf_name}.md: Main markdown content
        - {pdf_name}_metadata.json: Document metadata and conversion info
        - images/: Directory containing extracted images (if any)
    """
    try:
        # Import marker-pdf components (delayed import to handle missing dependency gracefully)
        try:
            from marker.models import load_all_models
            from marker.convert import convert_single_pdf
        except ImportError:
            raise ImportError(
                "marker-pdf not available. Install with: pip install marker-pdf==0.3.10"
            )

        # Load all required models for PDF processing
        # This includes OCR, layout detection, and table recognition models
        print("Loading PDF processing models...")
        try:
            model_lst = load_all_models()
            print(f"Successfully loaded {len(model_lst)} models")

            # Validate model list structure and integrity
            validate_model_list(model_lst)

        except Exception as e:
            print(f"Error during model loading: {e}")
            print(f"Error type: {type(e).__name__}")
            raise

        # Parse languages parameter if provided
        # Convert from comma-separated string to list for marker-pdf
        languages = None
        if langs:
            languages = [lang.strip() for lang in langs.split(",")]
            print(f"Using languages for OCR: {languages}")

        # Perform the actual PDF conversion
        # This is the main processing step that can take significant time
        print(f"Converting PDF: {input_path}")
        print(f"Batch multiplier: {batch_multiplier} (higher = more memory usage)")
        if max_pages:
            print(f"Processing maximum {max_pages} pages")
        if start_page:
            print(f"Starting from page {start_page}")

        try:
            full_text, images, metadata = convert_single_pdf(
                input_path,
                model_lst,
                batch_multiplier=batch_multiplier,
                max_pages=max_pages,
                start_page=start_page,
                langs=languages,
            )
        except KeyError as e:
            print(f"KeyError during PDF conversion: {e}")
            print_troubleshooting_info(e)
            raise
        except Exception as e:
            print(f"Unexpected error during PDF conversion: {e}")
            print(f"Error type: {type(e).__name__}")
            print_troubleshooting_info(e)
            import traceback

            traceback.print_exc()
            raise

        # Create output directory structure
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save the main markdown content
        # Use UTF-8 encoding to handle international characters
        md_output = output_dir / f"{Path(input_path).stem}.md"
        md_output.write_text(full_text, encoding="utf-8")
        print(f"Markdown saved to: {md_output}")

        # Save metadata as JSON for potential future use
        # This includes document properties, conversion settings, and statistics
        meta_output = output_dir / f"{Path(input_path).stem}_metadata.json"
        with open(meta_output, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to: {meta_output}")

        # Handle image extraction and cleanup
        try:
            if images:
                print(f"Processing {len(images)} extracted images...")
                image_dir = output_dir / "images"
                save_images(images, image_dir)

                # Clean up PIL Image objects to free memory
                # This is important for large documents with many images
                for img in images.values():
                    if isinstance(img, Image.Image):
                        try:
                            img.close()
                        except Exception as e:
                            print(f"Warning: Failed to close image: {e}")

                # Clear the images dictionary to help with garbage collection
                images.clear()
            else:
                print("No images found in the document")

        except Exception as e:
            # Don't fail the entire conversion if image processing fails
            print(f"Warning: Error during image cleanup: {e}")

    except Exception as e:
        # Print error and exit with error code for CLI usage
        print(f"Error converting {input_path}: {str(e)}", file=sys.stderr)
        sys.exit(1)


def clear_model_cache() -> bool:
    """
    Clear HuggingFace model cache to resolve model loading issues.

    This function attempts to clear the HuggingFace cache directory
    which can resolve issues with corrupted or incomplete model downloads.

    Returns:
        bool: True if cache was cleared successfully, False otherwise
    """
    import shutil
    from pathlib import Path
    import os

    # Common HuggingFace cache locations
    cache_dirs = [
        Path.home() / ".cache" / "huggingface",
        Path.home() / ".cache" / "torch",
        Path(os.environ.get("HF_HOME", "")) if "HF_HOME" in os.environ else None,
    ]

    cleared_any = False

    for cache_dir in cache_dirs:
        if cache_dir and cache_dir.exists():
            try:
                print(f"Clearing cache directory: {cache_dir}")
                shutil.rmtree(cache_dir)
                print(f"Successfully cleared: {cache_dir}")
                cleared_any = True
            except Exception as e:
                print(f"Failed to clear {cache_dir}: {e}")

    if not cleared_any:
        print("No cache directories found to clear")

    return cleared_any


def add_pdfs_to_queue(input_path: Path) -> list[Path]:
    """
    Add PDF files to the processing queue with comprehensive validation.

    This function handles both single PDF files and directories containing PDFs.
    It performs validation to ensure only valid PDF files are added to the
    processing queue, providing clear error messages for common issues.

    Args:
        input_path: Path to either a single PDF file or directory containing PDFs

    Returns:
        List of Path objects representing valid PDF files to process

    Raises:
        SystemExit: If no valid PDFs are found or input validation fails

    Examples:
        >>> add_pdfs_to_queue(Path("/docs/report.pdf"))
        [Path("/docs/report.pdf")]

        >>> add_pdfs_to_queue(Path("/docs/"))
        [Path("/docs/book1.pdf"), Path("/docs/book2.pdf")]
    """
    queue = []

    if input_path.is_dir():
        # Directory mode: find all PDF files in the directory
        print(f"Scanning directory for PDF files: {input_path}")
        pdfs = list(input_path.glob("*.pdf"))

        if not pdfs:
            print(f"No PDF files found in directory: {input_path}", file=sys.stderr)
            print(
                "Make sure the directory contains files with .pdf extension",
                file=sys.stderr,
            )
            sys.exit(1)

        print(f"Found {len(pdfs)} PDF file(s) in directory")
        queue.extend(pdfs)

    else:
        # Single file mode: validate the specific file
        if not input_path.is_file():
            print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
            sys.exit(1)

        if input_path.suffix.lower() != ".pdf":
            print(f"Error: Input file must be a PDF: {input_path}", file=sys.stderr)
            print(f"Found file extension: {input_path.suffix}", file=sys.stderr)
            sys.exit(1)

        print(f"Added single PDF file to queue: {input_path.name}")
        queue.append(input_path)

    return queue
