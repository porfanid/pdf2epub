"""
Tests for mark2epub module.
"""
import pytest
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import pdf2epub
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pdf2epub import mark2epub


class TestMark2EPUB:
    """Test class for mark2epub module functions."""
    
    def test_get_user_input_with_default(self):
        """Test get_user_input function with default value."""
        with patch('builtins.input', return_value=''):
            result = mark2epub.get_user_input("Test prompt", "default_value")
            assert result == "default_value"
    
    def test_get_user_input_with_custom_value(self):
        """Test get_user_input function with custom value."""
        with patch('builtins.input', return_value='custom_value'):
            result = mark2epub.get_user_input("Test prompt", "default_value")
            assert result == "custom_value"
    
    def test_get_metadata_from_user_empty_metadata(self):
        """Test get_metadata_from_user with empty existing metadata."""
        mock_inputs = [
            "My Book Title",       # dc:title
            "John Doe",           # dc:creator
            "book-123",           # dc:identifier
            "en",                 # dc:language
            "MIT License",        # dc:rights
            "My Publisher",       # dc:publisher
            "2024-01-01"         # dc:date
        ]
        
        with patch('builtins.input', side_effect=mock_inputs):
            result = mark2epub.get_metadata_from_user()
            
            metadata = result["metadata"]
            assert metadata["dc:title"] == "My Book Title"
            assert metadata["dc:creator"] == "John Doe"
            assert metadata["dc:identifier"] == "book-123"
            assert metadata["dc:language"] == "en"
            assert metadata["dc:rights"] == "MIT License"
            assert metadata["dc:publisher"] == "My Publisher"
            assert metadata["dc:date"] == "2024-01-01"
    
    def test_get_metadata_from_user_with_existing(self):
        """Test get_metadata_from_user with existing metadata."""
        existing = {
            "metadata": {
                "dc:title": "Existing Title",
                "dc:creator": "Existing Author"
            }
        }
        
        # Mock user pressing enter for all prompts (use defaults)
        with patch('builtins.input', return_value=''):
            result = mark2epub.get_metadata_from_user(existing)
            
            metadata = result["metadata"]
            assert metadata["dc:title"] == "Existing Title"
            assert metadata["dc:creator"] == "Existing Author"
    
    def test_review_markdown_file_not_found(self):
        """Test review_markdown with non-existent file."""
        non_existent_path = Path("/non/existent/file.md")
        
        should_continue, reason = mark2epub.review_markdown(non_existent_path)
        
        assert not should_continue
        assert "not found" in reason.lower()
    
    def test_review_markdown_valid_file(self):
        """Test review_markdown with valid markdown file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            md_file = Path(temp_dir) / "test.md"
            md_file.write_text("# Test Markdown\n\nThis is a test.")
            
            should_continue, reason = mark2epub.review_markdown(md_file)
            
            assert should_continue
            assert reason == ""
    
    def test_process_markdown_for_images_no_images(self):
        """Test process_markdown_for_images with no images."""
        markdown_text = "# Title\n\nJust text content."
        
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            
            result_text, image_list = mark2epub.process_markdown_for_images(
                markdown_text, work_dir
            )
            
            assert result_text == markdown_text
            assert len(image_list) == 0
    
    def test_process_markdown_for_images_with_images(self):
        """Test process_markdown_for_images with image references."""
        markdown_text = "# Title\n\n![Alt text](images/test.png)\n\nMore content."
        
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            images_dir = work_dir / "images"
            images_dir.mkdir()
            
            # Create a dummy image file
            test_image = images_dir / "test.png"
            test_image.write_bytes(b"fake image data")
            
            result_text, image_list = mark2epub.process_markdown_for_images(
                markdown_text, work_dir
            )
            
            assert "test.png" in image_list
            assert len(image_list) == 1
    
    @patch('pdf2epub.mark2epub.Image.open')
    def test_copy_and_optimize_image(self, mock_image_open):
        """Test copy_and_optimize_image function."""
        mock_img = MagicMock()
        mock_img.size = (2000, 1500)  # Larger than max_dimension
        mock_image_open.return_value = mock_img
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            src_path = temp_path / "source.png"
            dest_path = temp_path / "dest.png"
            
            # Create dummy source file
            src_path.write_bytes(b"fake image")
            
            mark2epub.copy_and_optimize_image(src_path, dest_path, max_dimension=1800)
            
            # Check that image processing was called
            mock_img.thumbnail.assert_called_once_with((1800, 1800))
            mock_img.save.assert_called_once_with(dest_path, optimize=True)
    
    def test_get_all_filenames(self):
        """Test get_all_filenames function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "file1.md").write_text("content")
            (temp_path / "file2.md").write_text("content")
            (temp_path / "file3.txt").write_text("content")
            (temp_path / "image.png").write_bytes(b"image")
            
            result = mark2epub.get_all_filenames(str(temp_path), [".md"])
            
            assert "file1.md" in result
            assert "file2.md" in result
            assert "file3.txt" not in result
            assert "image.png" not in result
    
    def test_get_container_xml(self):
        """Test get_container_XML function."""
        result = mark2epub.get_container_XML()
        
        assert '<?xml version="1.0"' in result
        assert 'container' in result
        assert 'META-INF' in result
    
    def test_get_coverpage_xml(self):
        """Test get_coverpage_XML function."""
        result = mark2epub.get_coverpage_XML("Test Title", ["Author 1", "Author 2"])
        
        assert "Test Title" in result
        assert "Author 1" in result
        assert "Author 2" in result
        assert '<?xml version="1.0"' in result
    
    def test_convert_to_epub_missing_directory(self):
        """Test convert_to_epub with missing markdown directory."""
        non_existent = Path("/non/existent/directory")
        output_path = Path("/tmp/output")
        
        with pytest.raises(Exception):
            mark2epub.convert_to_epub(non_existent, output_path)
    
    @patch('pdf2epub.mark2epub.get_metadata_from_user')
    @patch('pdf2epub.mark2epub.zipfile.ZipFile')
    def test_convert_to_epub_basic_flow(self, mock_zipfile, mock_get_metadata):
        """Test basic convert_to_epub flow."""
        # Mock metadata input
        mock_get_metadata.return_value = {
            "metadata": {
                "dc:title": "Test Book",
                "dc:creator": "Test Author",
                "dc:identifier": "test-123",
                "dc:language": "en",
                "dc:rights": "All rights reserved",
                "dc:publisher": "Test Publisher",
                "dc:date": "2024-01-01"
            },
            "default_css": ["style.css"],
            "chapters": [],
            "cover_image": None
        }
        
        # Mock zipfile
        mock_zip = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            markdown_dir = temp_path / "markdown"
            markdown_dir.mkdir()
            
            # Create test markdown file
            md_file = markdown_dir / "test.md"
            md_file.write_text("# Test\n\nContent here.")
            
            # Create metadata file
            metadata_file = markdown_dir / "test_metadata.json"
            metadata_file.write_text('{"title": "Test"}')
            
            output_path = temp_path / "output"
            
            mark2epub.convert_to_epub(markdown_dir, output_path)
            
            # Verify that ZIP operations were called
            assert mock_zip.writestr.called