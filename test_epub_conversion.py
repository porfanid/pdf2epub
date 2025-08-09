#!/usr/bin/env python3
"""
Test script for EPUB conversion functionality.
This script tests the markdown to EPUB conversion process offline.
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Add the pdf2epub package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import pdf2epub.mark2epub as mark2epub


def test_epub_conversion():
    """Test the markdown to EPUB conversion functionality."""

    # Prepare test environment
    test_dir = Path("test_markdown")
    output_file = Path("/tmp/test_output.epub")

    # Remove output file if it exists
    if output_file.exists():
        output_file.unlink()

    # Ensure required directories exist
    (test_dir / "images").mkdir(exist_ok=True)
    (test_dir / "css").mkdir(exist_ok=True)

    print("Testing Markdown to EPUB conversion...")
    print(f"Input directory: {test_dir}")
    print(f"Output file: {output_file}")

    try:
        # Use batch mode to avoid interactive prompts
        mark2epub.convert_to_epub(test_dir, output_file, batch_mode=True)

        # Verify output (the function creates EPUB in the source directory)
        actual_output = test_dir / f"{test_dir.name}.epub"
        if actual_output.exists():
            file_size = actual_output.stat().st_size
            print(f"✓ EPUB file created successfully at: {actual_output}")
            print(f"✓ File size: {file_size} bytes")

            # Move to expected location for consistency
            if output_file != actual_output:
                shutil.move(str(actual_output), str(output_file))
                print(f"✓ Moved to expected location: {output_file}")

            # Basic validation - check if it's a valid zip file (EPUB format)
            import zipfile

            try:
                with zipfile.ZipFile(output_file, "r") as zip_file:
                    files = zip_file.namelist()
                    required_files = ["META-INF/container.xml", "mimetype"]
                    for req_file in required_files:
                        if req_file in files:
                            print(f"✓ Required file found: {req_file}")
                        else:
                            print(f"✗ Required file missing: {req_file}")
                            return False
                    print(f"✓ EPUB structure is valid ({len(files)} files)")
                    return True
            except zipfile.BadZipFile:
                print("✗ Output file is not a valid EPUB/ZIP file")
                return False
        else:
            print(f"✗ EPUB file was not created at expected location: {actual_output}")
            return False

    except Exception as e:
        print(f"✗ Error during conversion: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_epub_conversion()
    sys.exit(0 if success else 1)
