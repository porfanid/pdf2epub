"""
Tests for enhanced error handling in pdf2md module.
"""

import pytest
from pathlib import Path
import tempfile
import sys
import os

# Add parent directory to path to import pdf2epub
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pdf2epub.pdf2md import (
    validate_model_list,
    print_troubleshooting_info,
    clear_model_cache,
)


class TestPDF2MDErrorHandling:
    """Test class for pdf2md error handling functions."""

    def test_validate_model_list_invalid_input(self):
        """Test validate_model_list with invalid input types."""
        with pytest.raises(ValueError, match="Expected model list"):
            validate_model_list("not a list")

        with pytest.raises(ValueError, match="Expected model list"):
            validate_model_list({"not": "a list"})

    def test_validate_model_list_wrong_length(self):
        """Test validate_model_list with wrong list length."""
        with pytest.raises(ValueError, match="Expected 6 models"):
            validate_model_list([1, 2, 3])

        with pytest.raises(ValueError, match="Expected 6 models"):
            validate_model_list([])

    def test_validate_model_list_missing_processor(self):
        """Test validate_model_list with models missing processor."""
        # Create mock objects without processor attribute
        mock_models = [type('Model', (), {})() for _ in range(6)]
        
        # This should return False because none have processor
        result = validate_model_list(mock_models)
        assert result is False

    def test_validate_model_list_valid_models(self):
        """Test validate_model_list with valid model structure."""
        # Create mock models with processor attribute
        mock_models = []
        for i in range(6):
            model = type('Model', (), {})()
            model.processor = "mock_processor"
            model.__call__ = lambda: None  # Make it callable
            mock_models.append(model)
        
        result = validate_model_list(mock_models)
        assert result is True

    def test_print_troubleshooting_info_encoder_error(self, capsys):
        """Test troubleshooting info for encoder errors."""
        error = KeyError("'encoder'")
        print_troubleshooting_info(error)
        
        captured = capsys.readouterr()
        assert "Encoder-related error detected" in captured.out
        assert "Model version incompatibility" in captured.out
        assert "Clear HuggingFace cache" in captured.out

    def test_print_troubleshooting_info_memory_error(self, capsys):
        """Test troubleshooting info for memory errors."""
        error = RuntimeError("out of memory error")
        print_troubleshooting_info(error)
        
        captured = capsys.readouterr()
        assert "Memory-related error detected" in captured.out
        assert "batch_multiplier" in captured.out

    def test_print_troubleshooting_info_network_error(self, capsys):
        """Test troubleshooting info for network errors."""
        error = ConnectionError("Failed to connect to huggingface.co")
        print_troubleshooting_info(error)
        
        captured = capsys.readouterr()
        assert "Network-related error detected" in captured.out
        assert "internet connection" in captured.out

    def test_clear_model_cache_no_cache(self, capsys):
        """Test cache clearing when no cache exists."""
        # This should handle the case where cache directories don't exist
        result = clear_model_cache()
        
        captured = capsys.readouterr()
        # Should either clear something or report no cache found
        assert "cache" in captured.out.lower()

    def test_clear_model_cache_with_temp_cache(self):
        """Test cache clearing with a temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock a cache directory structure
            cache_dir = Path(temp_dir) / "test_cache"
            cache_dir.mkdir()
            
            # Create a dummy file in cache
            (cache_dir / "dummy_model").write_text("test")
            
            # Patch the cache directories to use our temp directory
            import pdf2epub.pdf2md as pdf2md
            original_home = Path.home
            
            try:
                # Mock Path.home() to return our temp directory
                Path.home = lambda: Path(temp_dir)
                
                # Since we mocked home, clear_model_cache should look in temp_dir
                result = clear_model_cache()
                
                # The function may or may not find our specific structure
                # but it should not crash
                assert isinstance(result, bool)
                
            finally:
                # Restore original Path.home
                Path.home = original_home