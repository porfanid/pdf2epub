"""
Integration tests for the pdf2epub package.
"""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import patch
import sys
import os

# Add parent directory to path to import pdf2epub
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pdf2epub


class TestPackageIntegration:
    """Integration tests for the main package API."""

    def test_package_imports(self):
        """Test that all expected functions are importable."""
        # Test direct imports
        assert hasattr(pdf2epub, "convert_pdf")
        assert hasattr(pdf2epub, "convert_to_epub")
        assert hasattr(pdf2epub, "AIPostprocessor")
        assert hasattr(pdf2epub, "add_pdfs_to_queue")
        assert hasattr(pdf2epub, "get_default_output_dir")
        assert hasattr(pdf2epub, "get_default_input_dir")

        # Test convenience functions
        assert hasattr(pdf2epub, "convert_pdf_to_markdown")
        assert hasattr(pdf2epub, "convert_markdown_to_epub")

    def test_package_metadata(self):
        """Test package metadata."""
        assert hasattr(pdf2epub, "__version__")
        assert hasattr(pdf2epub, "__author__")
        assert pdf2epub.__version__ == "0.1.0"
        assert pdf2epub.__author__ == "porfanid"

    def test_convert_pdf_to_markdown_wrapper(self):
        """Test the convenience wrapper function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pdf2epub.convert_pdf") as mock_convert:
                pdf_path = str(Path(temp_dir) / "test.pdf")
                output_dir = str(Path(temp_dir) / "output")

                pdf2epub.convert_pdf_to_markdown(
                    pdf_path, output_dir, batch_multiplier=3, max_pages=10
                )

                mock_convert.assert_called_once_with(
                    pdf_path, Path(output_dir), batch_multiplier=3, max_pages=10
                )

    def test_convert_markdown_to_epub_wrapper(self):
        """Test the convenience wrapper function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pdf2epub.convert_to_epub") as mock_convert:
                markdown_dir = str(Path(temp_dir) / "markdown")
                output_path = str(Path(temp_dir) / "output")

                pdf2epub.convert_markdown_to_epub(markdown_dir, output_path)

                mock_convert.assert_called_once_with(
                    Path(markdown_dir), Path(output_path)
                )

    def test_ai_postprocessor_import(self):
        """Test AIPostprocessor can be imported and instantiated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)

            processor = pdf2epub.AIPostprocessor(work_dir)

            assert processor.work_dir == work_dir
            assert isinstance(processor, pdf2epub.AIPostprocessor)

    def test_all_exports(self):
        """Test that __all__ contains all expected exports."""
        expected_exports = [
            "convert_pdf",
            "add_pdfs_to_queue",
            "get_default_output_dir",
            "get_default_input_dir",
            "convert_to_epub",
            "AIPostprocessor",
        ]

        for export in expected_exports:
            assert export in pdf2epub.__all__
            assert hasattr(pdf2epub, export)

    def test_submodule_access(self):
        """Test that submodules are accessible."""
        # These should work for advanced users who want direct access
        import pdf2epub.pdf2md
        import pdf2epub.mark2epub
        import pdf2epub.postprocessing.ai

        assert hasattr(pdf2epub.pdf2md, "convert_pdf")
        assert hasattr(pdf2epub.mark2epub, "convert_to_epub")
        assert hasattr(pdf2epub.postprocessing.ai, "AIPostprocessor")
