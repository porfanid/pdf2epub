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

            result = pdf2md.add_pdfs_to_queue(temp_path)

            assert len(result) == 0
            assert isinstance(result, list)

    def test_save_images_empty_dict(self, capsys):
        """Test save_images with empty images dictionary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_dir = Path(temp_dir) / "images"

            pdf2md.save_images({}, image_dir)

            captured = capsys.readouterr()
            assert "No images found in document" in captured.out

    def test_save_images_none_input(self, capsys):
        """Test save_images with None input."""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_dir = Path(temp_dir) / "images"

            pdf2md.save_images(None, image_dir)

            captured = capsys.readouterr()
            assert "No images found in document" in captured.out

    @patch("pdf2md.Image")
    def test_save_images_with_valid_images(self, mock_image, capsys):
        """Test save_images with valid image data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_dir = Path(temp_dir) / "images"

            # Mock PIL Image
            mock_img = MagicMock()
            mock_image.Image = mock_img

            # Test with PIL Image object
            images = {"test1.png": mock_img}

            pdf2md.save_images(images, image_dir)

            assert image_dir.exists()
            captured = capsys.readouterr()
            assert "Successfully saved" in captured.out

    @patch("pdf2epub.pdf2md.load_all_models")
    @patch("pdf2epub.pdf2md.convert_single_pdf")
    def test_convert_pdf_success(self, mock_convert, mock_load_models):
        """Test successful PDF conversion."""
        # Mock the marker functions
        mock_load_models.return_value = ["mock_models"]
        mock_convert.return_value = (
            "# Test Document\nContent here",
            {"image1.png": "image_data"},
            {"title": "Test Document"},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_pdf = temp_path / "test.pdf"
            input_pdf.write_text("dummy pdf")
            output_dir = temp_path / "output"

            pdf2md.convert_pdf(str(input_pdf), output_dir)

            # Check that markdown file was created
            md_file = output_dir / "test.md"
            assert md_file.exists()

            # Check that metadata file was created
            meta_file = output_dir / "test_metadata.json"
            assert meta_file.exists()

            # Verify function calls
            mock_load_models.assert_called_once()
            mock_convert.assert_called_once()

    def test_convert_pdf_with_languages(self):
        """Test convert_pdf with language specification."""
        with patch("pdf2epub.pdf2md.load_all_models") as mock_load:
            with patch("pdf2epub.pdf2md.convert_single_pdf") as mock_convert:
                mock_load.return_value = ["mock_models"]
                mock_convert.return_value = ("content", {}, {})

                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    input_pdf = temp_path / "test.pdf"
                    input_pdf.write_text("dummy")
                    output_dir = temp_path / "output"

                    pdf2md.convert_pdf(
                        str(input_pdf), output_dir, langs="English,German"
                    )

                    # Check that languages were parsed correctly
                    call_args = mock_convert.call_args
                    assert call_args[1]["langs"] == ["English", "German"]
