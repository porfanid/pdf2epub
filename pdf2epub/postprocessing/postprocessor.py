import json
import re
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import tempfile
import shutil

class MarkdownPostprocessor:
    def __init__(self, input_path: str, json_patterns: Dict):
        """
        Initialize the postprocessor with input file path and patterns
        
        Args:
            input_path: Path to the markdown file to process
            json_patterns: Dictionary containing error patterns and fixes
        """
        print("Initializing MarkdownPostprocessor")
        self.input_path = Path(input_path)
        self.json_patterns = json_patterns
        self.backup_path = None
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    #def _create_backup(self) -> None:
    #    """Create a backup of the original file."""
    #    try:
            # Create temporary backup
    #        with tempfile.NamedTemporaryFile(delete=False) as tmp:
    #            self.backup_path = Path(tmp.name)
    #            shutil.copy2(self.input_path, self.backup_path)
    #        self.logger.info(f"Created backup at {self.backup_path}")
    #    except Exception as e:
    #        self.logger.error(f"Failed to create backup: {e}")
    #        raise

    #def _restore_from_backup(self) -> None:
    #    """Restore the original file from backup if something goes wrong."""
    #    if self.backup_path and self.backup_path.exists():
    #        try:
    #            shutil.copy2(self.backup_path, self.input_path)
    #            self.logger.info("Successfully restored from backup")
    #        except Exception as e:
    #            self.logger.error(f"Failed to restore from backup: {e}")
    #            raise
    #        finally:
    #            try:
    #                self.backup_path.unlink()
    #                self.backup_path = None
    #            except Exception as e:
    #                self.logger.error(f"Failed to remove backup file: {e}")

    def _validate_pattern(self, pattern: Dict) -> bool:
        """
        Validate a pattern dictionary has all required fields and valid regex.
        
        Args:
            pattern: Dictionary containing pattern information
            
        Returns:
            bool: True if pattern is valid, False otherwise
        """
        required_fields = ['pattern_id', 'regex', 'severity']
        
        # Check required fields
        if not all(field in pattern for field in required_fields):
            self.logger.warning(f"Pattern missing required fields: {pattern}")
            return False
            
        # Validate regex pattern
        try:
            re.compile(pattern['regex'])
        except re.error as e:
            self.logger.warning(f"Invalid regex pattern '{pattern['regex']}': {e}")
            return False
            
        return True

    def _safe_replace(self, content: str, pattern: str, replacement: str) -> str:
        """
        Safely apply regex replacement while preserving markdown formatting.
        
        Args:
            content: The markdown content
            pattern: Regex pattern to match
            replacement: Replacement string
            
        Returns:
            str: Updated content with safe replacements
        """
        try:
            # Compile pattern
            regex = re.compile(pattern)
            
            # First pass - identify matches
            matches = list(regex.finditer(content))
            if not matches:
                return content
                
            # Process matches in reverse order to preserve positions
            for match in reversed(matches):
                start, end = match.span()
                
                # Don't modify if within markdown formatting
                pre_context = content[max(0, start-2):start]
                post_context = content[end:min(len(content), end+2)]
                
                # Skip if we're inside markdown syntax
                if '`' in pre_context or '`' in post_context:  # Code blocks
                    continue
                if '*' in pre_context or '*' in post_context:  # Emphasis
                    continue
                if '_' in pre_context or '_' in post_context:  # Emphasis
                    continue
                if '[' in pre_context or ']' in post_context:  # Links
                    continue
                
                # Apply replacement
                content = content[:start] + regex.sub(replacement, match.group(0)) + content[end:]
                
            return content
            
        except Exception as e:
            self.logger.error(f"Error in safe_replace: {e}")
            return content

    def process_file(self) -> bool:
        """
        Process the markdown file using the patterns.json.
        
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            # Create backup first
            #self._create_backup()
            
            # Read input file
            with open(self.input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            patterns_applied = 0
            
            # Process each pattern
            for pattern in self.json_patterns.get('patterns', []):
                if not self._validate_pattern(pattern):
                    continue
                    
            # Apply pattern based on severity
                self.logger.info(f"Processing pattern: {pattern}")
                
                matches = list(re.finditer(pattern['regex'], content))
                self.logger.info(f"Found {len(matches)} matches for pattern {pattern['pattern_id']}")
                
                for match in matches:
                    self.logger.info(f"Match found for pattern {pattern['pattern_id']}: {match.group(0)}")
                
                if pattern['severity'] == 'high':
                    # For high severity, actually modify the content
                    replacement = pattern.get('replacement')
                    if not replacement:  # If no replacement specified, try to determine one
                        if '\\b' in pattern['regex']:  # If it's a word boundary pattern
                            replacement = ' '  # Add space between words
                        else:
                            replacement = match.group(0)  # Keep original if no clear fix
                            
                    self.logger.info(f"Applying high severity fix with replacement: {replacement}")
                    content = self._safe_replace(content, pattern['regex'], replacement)
                    patterns_applied += 1
                    
                elif pattern['severity'] == 'medium':
                    # For medium severity, apply fixes but log them
                    replacement = pattern.get('replacement')
                    if not replacement:
                        if '\\b' in pattern['regex']:
                            replacement = ' '
                        else:
                            replacement = match.group(0)
                            
                    self.logger.info(f"Applying medium severity fix with replacement: {replacement}")
                    content = self._safe_replace(content, pattern['regex'], replacement)
                    patterns_applied += 1
                    
                elif pattern['severity'] == 'low':
                    # Only log low severity patterns
                    self.logger.info("Skipping low severity pattern (logging only)")
            
            # Only write if changes were made
            #if content != original_content:
            # Write to temporary file first
            temp_output = Path(str(self.input_path) + '.tmp')
            with open(temp_output, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Replace original file
            temp_output.replace(self.input_path)
            
            self.logger.info(f"Applied {patterns_applied} patterns successfully")
                
            # Remove backup if everything succeeded
            if self.backup_path:
                self.backup_path.unlink()
                self.backup_path = None
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing file: {e}")
            #self._restore_from_backup()
            return False

def process_markdown(markdown_dir: str, json_path: str) -> bool:
    """
    Process a markdown file using patterns from a JSON file.
    
    Args:
        markdown_dir: Path to the directory containing the markdown file
        json_path: Path to the JSON file containing patterns
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting markdown processing")
        
        # Get the markdown directory path
        markdown_dir_path = Path(markdown_dir)
        if not markdown_dir_path.exists():
            raise FileNotFoundError(f"Markdown directory not found: {markdown_dir}")
            
        # Find all markdown files in the directory
        markdown_files = list(markdown_dir_path.glob("*.md"))
        if not markdown_files:
            raise FileNotFoundError(f"No markdown files found in directory: {markdown_dir}")
            
        logger.info(f"Found {len(markdown_files)} markdown files to process")
        logger.info(f"JSON patterns file: {json_path}")
        
        # Verify JSON file exists
        if not Path(json_path).exists():
            raise FileNotFoundError(f"JSON patterns file not found: {json_path}")
            
        # Load JSON patterns
        logger.info("Loading JSON patterns...")
        with open(json_path, 'r', encoding='utf-8') as f:
            patterns = json.load(f)
        logger.info(f"Loaded {len(patterns.get('patterns', []))} patterns")
        
        success = True
        # Process each markdown file
        for markdown_file in markdown_files:
            logger.info(f"Processing file: {markdown_file.name}")
            processor = MarkdownPostprocessor(str(markdown_file), patterns)
            if not processor.process_file():
                logger.error(f"Failed to process {markdown_file.name}")
                success = False
        
        if success:
            logger.info("All files processed successfully")
        else:
            logger.error("Some files failed to process")
            
        return success
        
    except Exception as e:
        logger.error(f"Failed to process markdown: {e}")
        return False

