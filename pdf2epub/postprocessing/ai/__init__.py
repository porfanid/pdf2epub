from pathlib import Path
import json
from typing import Optional, Tuple, Dict
import logging
from . import anthropicapi
from ..postprocessor import process_markdown

AI_PROVIDER = "anthropic"

class AIPostprocessor:
    def __init__(self, work_dir: Path):
        """Initialize AI postprocessor with working directory."""
        self.work_dir = work_dir
        self.json_path = work_dir / "patterns.json"
        self.markdown_path = work_dir
        
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)



    def run_postprocessing(self, markdown_path: Path, ai_provider: str) -> dict:
        """Run the postprocessor directly as a module."""
        if ai_provider != "anthropic":
            raise ValueError(f"Unsupported AI provider: {ai_provider}")
            
        combined_json = {}
        
        try:
            system_prompt = self._get_system_prompt()
            self.logger.info("Successfully loaded system prompt")
            request = self._get_markdown_sample(markdown_path)
            self.logger.info(f"Successfully loaded markdown sample from {markdown_path}")
            
            for i in range(2):
                try:
                    analyzer = anthropicapi.Anthropic_Analysis.getjsonparams(system_prompt, request)
                    current_json = json.loads(analyzer)
                    
                    if i == 0:
                        # First iteration - set initial JSON
                        combined_json = current_json
                        self.logger.info("Initial JSON data populated")
                    else:
                        # Second iteration - append new data
                        combined_json.update(current_json)
                        self.logger.info("Additional JSON data appended")
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON response in iteration {i}: {e}")
                    raise
                except Exception as e:
                    self.logger.error(f"Error in iteration {i}: {e}")
                    raise
                    
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(combined_json, f, indent=4)
                self.logger.info(f"JSON data written to {self.json_path}")
                
            process_markdown(self.work_dir, self.json_path)
        
        except Exception as e:
            self.logger.error(f"Error in run_postprocessing: {e}")
            raise

        
        
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

    def _get_markdown_sample(self, markdown_path: Path, max_tokens: int = 50000) -> str:
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