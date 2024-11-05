from pathlib import Path
import json
import anthropic
import subprocess
from typing import Optional, Tuple
import os
import sys
from ..postprocessor import process_markdown
import logging

class AIPostprocessor:
    def __init__(self, work_dir: Path):
        """Initialize AI postprocessor with working directory."""
        self.work_dir = work_dir
        
        # Check for API key in environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please set it with your Anthropic API key."
            )
            
        self.client = anthropic.Anthropic(api_key=api_key)

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _get_system_prompt(self) -> str:
        """Read the system prompt from prompt.txt."""
        # Get the absolute path to the module directory
        module_dir = Path(__file__).resolve().parent
        prompt_path = module_dir.parent / "prompt.txt"
        
        self.logger.info(f"Looking for prompt.txt at: {prompt_path}")
        
        try:
            if not prompt_path.exists():
                raise FileNotFoundError(f"prompt.txt not found at {prompt_path}")
                
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    raise ValueError("prompt.txt is empty")
                return content
                
        except Exception as e:
            raise RuntimeError(f"Failed to read prompt.txt: {e}")

    def _get_markdown_sample(self, markdown_path: Path, max_tokens: int = 1000) -> str:
        """Get a sample of the markdown file up to max_tokens."""
        try:
            if not markdown_path.exists():
                raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
                
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    raise ValueError("Markdown file is empty")
                    
                # Rough approximation of token count (words * 1.3)
                words = content.split()[:int(max_tokens / 1.3)]
                return ' '.join(words)
                
        except Exception as e:
            raise RuntimeError(f"Failed to read markdown file: {e}")

    def analyze_with_claude(self, markdown_path: Path) -> Tuple[bool, Optional[Path]]:
        """
        Analyze markdown with Claude and return whether to proceed with postprocessing.
        
        Returns:
            Tuple[bool, Optional[Path]]: (proceed with postprocessing, path to JSON file)
        """
        try:
            # Get system prompt and markdown sample
            system_prompt = self._get_system_prompt()
            self.logger.info("Successfully loaded system prompt")
            
            markdown_sample = self._get_markdown_sample(markdown_path)
            self.logger.info(f"Successfully loaded markdown sample from {markdown_path}")

            # Create the message for Claude
            self.logger.info("Sending request to Claude...")
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=8192,
                temperature=0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": markdown_sample}
                ]
            )

            # Parse Claude's response as JSON
            try:
# Clean up the response text
                response_text = message.content[0].text                
                # Parse JSON first to get the structure
                patterns = json.loads(response_text)
            
                
                # Validate JSON structure
                if not isinstance(patterns, dict) or "patterns" not in patterns:
                    raise ValueError("Invalid JSON structure in Claude's response")
                
            except Exception as e:
                raise RuntimeError(f"Failed to parse Claude's response as JSON: {e}")

            # Save patterns to JSON file
            json_path = self.work_dir / "patterns.json"
            self.logger.info(f"Saving patterns to: {json_path}")
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(patterns, f, indent=2)
            self.logger.info("Successfully saved patterns to JSON file")

            # Ask user if they want to proceed with postprocessing
            while True:
                response = input("\nWould you like to run AI postprocessing on the markdown? (y/n): ").lower()
                if response in ['y', 'yes']:
                    return True, json_path
                elif response in ['n', 'no']:
                    return False, None
                else:
                    print("Please enter 'y' or 'n'")

        except Exception as e:
            self.logger.error(f"Error during AI analysis: {e}")
            return False, None

    def run_postprocessing(self, markdown_path: Path, json_path: Path) -> bool:
        """Run the postprocessor directly as a module."""
        try:
            self.logger.info(f"Running postprocessing on {markdown_path} with patterns from {json_path}")
            
            # Run postprocessor directly
            success = process_markdown(str(markdown_path), str(json_path))
            
            if success:
                self.logger.info("Postprocessing completed successfully")
                return True
            else:
                self.logger.error("Postprocessing failed")
                return False
            
        except Exception as e:
            self.logger.error(f"Error running postprocessing: {e}")
            return False