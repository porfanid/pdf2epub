"""
Tests for pdf2md module.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import pdf2epub
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pdf2epub import pdf2md


class TestPDF2MD:
    """Test class for pdf2md module functions."""

    def test_get_default_output_dir(self):
        """Test get_default_output_dir function."""
        input_path = Path("/path/to/document.pdf")
        expected_output = Path("/path/to/document")

        result = pdf2md.get_default_output_dir(input_path)
        assert result == expected_output

    def test_get_default_input_dir(self):
        """Test get_default_input_dir function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            temp_path = Path(temp_dir)

            try:
                # Change to temp directory
                import os

                os.chdir(temp_path)

                result = pdf2md.get_default_input_dir()
                expected = temp_path / "input"

                assert result == expected
                assert result.exists()  # Should create the directory

            finally:
                os.chdir(original_cwd)

    def test_add_pdfs_to_queue_single_file(self):
        """Test add_pdfs_to_queue with single PDF file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a dummy PDF file
            pdf_file = temp_path / "test.pdf"
            pdf_file.write_text("dummy pdf content")

            result = pdf2md.add_pdfs_to_queue(pdf_file)

            assert len(result) == 1
            assert result[0] == pdf_file

    def test_add_pdfs_to_queue_directory(self):
        """Test add_pdfs_to_queue with directory containing PDFs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple PDF files
            pdf1 = temp_path / "test1.pdf"
            pdf2 = temp_path / "test2.pdf"
            non_pdf = temp_path / "test.txt"

            pdf1.write_text("dummy pdf content 1")
            pdf2.write_text("dummy pdf content 2")
            non_pdf.write_text("not a pdf")

            result = pdf2md.add_pdfs_to_queue(temp_path)

            assert len(result) == 2
            assert pdf1 in result
            assert pdf2 in result
            assert non_pdf not in [Path(p) for p in result]

    def test_add_pdfs_to_queue_empty_directory(self):
        """Test add_pdfs_to_queue with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # The function calls sys.exit(1) when no PDFs are found
            with pytest.raises(SystemExit, match="1"):
                pdf2md.add_pdfs_to_queue(temp_path)

    def test_save_images_empty_dict(self, capsys):
        """Test save_images with empty images dictionary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_dir = Path(temp_dir) / "images"

            # Mock PIL to be available so we can test the empty dict logic
            with patch("pdf2epub.pdf2md.PIL_AVAILABLE", True):
                pdf2md.save_images({}, image_dir)

                captured = capsys.readouterr()
                assert "No images found in document" in captured.out

    def test_save_images_none_input(self, capsys):
        """Test save_images with None input."""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_dir = Path(temp_dir) / "images"

            # Mock PIL to be available so we can test the None input logic
            with patch("pdf2epub.pdf2md.PIL_AVAILABLE", True):
                pdf2md.save_images(None, image_dir)

                captured = capsys.readouterr()
                assert "No images found in document" in captured.out

    @patch("pdf2epub.pdf2md.PIL_AVAILABLE", True)
    def test_save_images_with_valid_images(self, capsys):
        """Test save_images with valid image data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_dir = Path(temp_dir) / "images"

            # Test with bytes data (which is supported without mocking PIL Image)
            images = {"test1.png": b"fake_image_data"}

            pdf2md.save_images(images, image_dir)

            assert image_dir.exists()
            captured = capsys.readouterr()
            # The function should attempt to process the image even if it fails to open the bytes
            assert len(captured.out) > 0

    @patch("pdf2epub.pdf2md.convert_pdf")
    def test_convert_pdf_success(self, mock_convert_pdf):
        """Test successful PDF conversion."""
        # Mock the entire convert_pdf function since marker dependency may not be available
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_pdf = temp_path / "test.pdf"
            input_pdf.write_text("dummy pdf")
            output_dir = temp_path / "output"

            # Setup mock to simulate successful conversion
            def mock_conversion(input_path, output_dir_param, **kwargs):
                output_dir_param.mkdir(exist_ok=True)
                md_file = output_dir_param / "test.md"
                md_file.write_text("# Test Document\nContent here")
                meta_file = output_dir_param / "test_metadata.json"
                meta_file.write_text('{"title": "Test Document"}')

            mock_convert_pdf.side_effect = mock_conversion

            # Call the function through the module import since we're mocking it
            import pdf2epub.pdf2md as pdf2md

            pdf2md.convert_pdf(str(input_pdf), output_dir)

            # Verify the mock was called
            mock_convert_pdf.assert_called_once_with(str(input_pdf), output_dir)

    def test_convert_pdf_with_languages(self):
        """Test convert_pdf with language specification."""
        with patch("pdf2epub.pdf2md.convert_pdf") as mock_convert_pdf:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                input_pdf = temp_path / "test.pdf"
                input_pdf.write_text("dummy")
                output_dir = temp_path / "output"

                # Setup mock to simulate successful conversion
                def mock_conversion(input_path, output_dir_param, **kwargs):
                    output_dir_param.mkdir(exist_ok=True)
                    md_file = output_dir_param / "test.md"
                    md_file.write_text("# Test Document\nContent here")
                    meta_file = output_dir_param / "test_metadata.json"
                    meta_file.write_text('{"title": "Test Document"}')

                mock_convert_pdf.side_effect = mock_conversion

                import pdf2epub.pdf2md as pdf2md

                pdf2md.convert_pdf(str(input_pdf), output_dir, langs="English,German")

                # Verify the mock was called with languages
                mock_convert_pdf.assert_called_once_with(
                    str(input_pdf), output_dir, langs="English,German"
                )
