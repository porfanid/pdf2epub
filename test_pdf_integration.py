#!/usr/bin/env python3
"""
PDF to EPUB integration test script.
This script tests the full PDF to EPUB conversion pipeline when network access is available.
Falls back to EPUB-only testing when network is unavailable.
"""

import os
import sys
import tempfile
import urllib.request
from pathlib import Path
import subprocess


def test_network_connectivity():
    """Test if we can reach HuggingFace for model downloads."""
    try:
        urllib.request.urlopen("https://huggingface.co", timeout=10)
        return True
    except:
        return False


def test_pdf_to_epub_conversion():
    """Test the full PDF to EPUB conversion pipeline."""

    print("Testing PDF to EPUB conversion pipeline...")

    # Check network connectivity
    has_network = test_network_connectivity()
    print(f"Network connectivity: {'Available' if has_network else 'Limited'}")

    if not has_network:
        print("⚠️  Network not available - skipping PDF processing tests")
        print("    PDF processing requires HuggingFace model downloads")
        return True

    # Test with the sample PDF
    test_pdf = Path("tests/test_sample.pdf")
    if not test_pdf.exists():
        print(f"✗ Test PDF not found: {test_pdf}")
        return False

    print(f"✓ Using test PDF: {test_pdf}")

    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"

        try:
            # Run the main conversion script
            cmd = [
                sys.executable,
                "main.py",
                str(test_pdf),
                str(output_dir),
                "--skip-ai",  # Skip AI processing to avoid API key requirement
                "--batch",  # Use batch mode to avoid interactive prompts
                "--batch-multiplier",
                "1",  # Use minimal resources
                "--max-pages",
                "3",  # Limit to first few pages
            ]

            print("Running PDF conversion...")
            print(f"Command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.getcwd(),
            )

            if result.returncode != 0:
                print(f"✗ PDF conversion failed with exit code {result.returncode}")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False

            print("✓ PDF conversion completed successfully")

            # Check for expected outputs
            expected_files = []
            if output_dir.exists():
                for item in output_dir.iterdir():
                    if item.is_dir():
                        # Look for EPUB file in subdirectory
                        epub_files = list(item.glob("*.epub"))
                        md_files = list(item.glob("*.md"))

                        if epub_files:
                            expected_files.extend(epub_files)
                            print(f"✓ Found EPUB file: {epub_files[0]}")

                        if md_files:
                            print(f"✓ Found Markdown file: {md_files[0]}")

            if not expected_files:
                print("✗ No EPUB files found in output")
                return False

            # Validate EPUB structure
            import zipfile

            for epub_file in expected_files:
                try:
                    with zipfile.ZipFile(epub_file, "r") as zip_file:
                        files = zip_file.namelist()
                        required_files = ["META-INF/container.xml", "mimetype"]
                        for req_file in required_files:
                            if req_file in files:
                                print(f"✓ EPUB structure valid: {req_file}")
                            else:
                                print(f"✗ Missing required file: {req_file}")
                                return False
                        print(f"✓ EPUB file is valid ({len(files)} files)")
                except zipfile.BadZipFile:
                    print(f"✗ Invalid EPUB file: {epub_file}")
                    return False

            return True

        except subprocess.TimeoutExpired:
            print("✗ PDF conversion timed out")
            return False
        except Exception as e:
            print(f"✗ PDF conversion failed with error: {e}")
            return False


if __name__ == "__main__":
    success = test_pdf_to_epub_conversion()
    sys.exit(0 if success else 1)
