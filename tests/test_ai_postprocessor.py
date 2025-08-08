"""
Tests for AI postprocessing module.
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

from pdf2epub.postprocessing.ai import AIPostprocessor


class TestAIPostprocessor:
    """Test class for AIPostprocessor."""
    
    def test_init(self):
        """Test AIPostprocessor initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            
            processor = AIPostprocessor(work_dir)
            
            assert processor.work_dir == work_dir
            assert processor.json_path == work_dir / "patterns.json"
    
    def test_get_system_prompt_success(self):
        """Test _get_system_prompt with existing prompt file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            processor = AIPostprocessor(work_dir)
            
            # Create a mock prompt file in the expected location
            prompt_content = "This is a test system prompt."
            
            # We need to create the prompt.txt in the right location
            # The method looks for it in parent directory of ai module
            with patch.object(processor, '_get_system_prompt', return_value=prompt_content):
                result = processor._get_system_prompt()
                assert result == prompt_content
    
    def test_get_system_prompt_file_not_found(self):
        """Test _get_system_prompt when prompt file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            processor = AIPostprocessor(work_dir)
            
            with pytest.raises(RuntimeError, match="Failed to read prompt.txt"):
                processor._get_system_prompt()
    
    def test_get_markdown_sample_success(self):
        """Test _get_markdown_sample with valid markdown file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            processor = AIPostprocessor(work_dir)
            
            # Create test markdown file
            md_file = work_dir / "test.md"
            markdown_content = "# Test Document\n\nThis is test content with multiple words to test token limiting functionality."
            md_file.write_text(markdown_content)
            
            result = processor._get_markdown_sample(md_file, max_tokens=10)
            
            # Should return truncated content based on word count
            assert len(result.split()) <= 8  # Rough approximation
            assert "Test Document" in result
    
    def test_get_markdown_sample_file_not_found(self):
        """Test _get_markdown_sample with non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            processor = AIPostprocessor(work_dir)
            
            non_existent = work_dir / "non_existent.md"
            
            with pytest.raises(RuntimeError, match="Failed to read markdown file"):
                processor._get_markdown_sample(non_existent)
    
    def test_get_markdown_sample_empty_file(self):
        """Test _get_markdown_sample with empty file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            processor = AIPostprocessor(work_dir)
            
            # Create empty markdown file
            md_file = work_dir / "empty.md"
            md_file.write_text("")
            
            with pytest.raises(RuntimeError, match="Failed to read markdown file"):
                processor._get_markdown_sample(md_file)
    
    @patch('pdf2epub.postprocessing.ai.anthropicapi.Anthropic_Analysis.getjsonparams')
    @patch('pdf2epub.postprocessing.ai.process_markdown')
    def test_run_postprocessing_success(self, mock_process_markdown, mock_getjsonparams):
        """Test successful run_postprocessing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            processor = AIPostprocessor(work_dir)
            
            # Create test markdown file
            md_file = work_dir / "test.md"
            md_file.write_text("# Test\n\nContent here.")
            
            # Mock the AI response
            mock_json_response = '{"patterns": {"error1": "fix1"}, "improvements": {"suggestion1": "change1"}}'
            mock_getjsonparams.return_value = mock_json_response
            
            # Mock system prompt
            with patch.object(processor, '_get_system_prompt', return_value="test prompt"):
                processor.run_postprocessing(md_file, "anthropic")
            
            # Verify JSON file was created
            json_file = work_dir / "patterns.json"
            assert json_file.exists()
            
            # Verify the content
            with open(json_file, 'r') as f:
                saved_data = json.load(f)
                assert "patterns" in saved_data
                assert "improvements" in saved_data
            
            # Verify process_markdown was called
            mock_process_markdown.assert_called_once_with(work_dir, json_file)
    
    def test_run_postprocessing_unsupported_provider(self):
        """Test run_postprocessing with unsupported AI provider."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            processor = AIPostprocessor(work_dir)
            
            md_file = work_dir / "test.md"
            md_file.write_text("content")
            
            with pytest.raises(ValueError, match="Unsupported AI provider"):
                processor.run_postprocessing(md_file, "unsupported_provider")
    
    @patch('pdf2epub.postprocessing.ai.anthropicapi.Anthropic_Analysis.getjsonparams')
    def test_run_postprocessing_json_decode_error(self, mock_getjsonparams):
        """Test run_postprocessing with invalid JSON response."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            processor = AIPostprocessor(work_dir)
            
            md_file = work_dir / "test.md"
            md_file.write_text("content")
            
            # Mock invalid JSON response
            mock_getjsonparams.return_value = "invalid json {"
            
            with patch.object(processor, '_get_system_prompt', return_value="test prompt"):
                with pytest.raises(json.JSONDecodeError):
                    processor.run_postprocessing(md_file, "anthropic")
    
    @patch('pdf2epub.postprocessing.ai.anthropicapi.Anthropic_Analysis.getjsonparams')
    def test_run_postprocessing_multiple_iterations(self, mock_getjsonparams):
        """Test run_postprocessing with multiple AI iterations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            processor = AIPostprocessor(work_dir)
            
            md_file = work_dir / "test.md"
            md_file.write_text("content")
            
            # Mock different responses for each iteration
            responses = [
                '{"patterns": {"error1": "fix1"}}',
                '{"improvements": {"suggestion1": "change1"}}'
            ]
            mock_getjsonparams.side_effect = responses
            
            with patch.object(processor, '_get_system_prompt', return_value="test prompt"):
                with patch('pdf2epub.postprocessing.ai.process_markdown'):
                    processor.run_postprocessing(md_file, "anthropic")
            
            # Verify combined JSON
            json_file = work_dir / "patterns.json"
            with open(json_file, 'r') as f:
                saved_data = json.load(f)
                assert "patterns" in saved_data
                assert "improvements" in saved_data
                assert saved_data["patterns"]["error1"] == "fix1"
                assert saved_data["improvements"]["suggestion1"] == "change1"