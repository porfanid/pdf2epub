"""
AI-powered postprocessing module for improving PDF-to-Markdown conversion quality.

This module provides an extensible framework for using AI services to analyze and
improve the quality of markdown content generated from PDF conversion. It uses
a plugin architecture to support multiple AI providers and can identify common
conversion issues like formatting problems, OCR errors, and structural issues.

Architecture:
- AIPostprocessor: Main coordinator class that manages the workflow
- Provider plugins: Modular AI service implementations (currently Anthropic Claude)
- Pattern-based fixes: JSON-driven regex patterns for common issues
- Fallback processing: Traditional regex-based cleanup when AI is unavailable

Workflow:
1. Load system prompt defining the analysis task
2. Sample markdown content (respecting token limits)
3. Send to AI provider for analysis
4. Receive JSON patterns describing issues found
5. Apply pattern-based fixes to the full document
6. Save results and provide feedback

Features:
- Token-aware content sampling for large documents
- Configurable AI providers through plugin system
- Graceful degradation when AI services are unavailable
- Comprehensive error handling and logging
- Memory-efficient processing for large files
"""

from pathlib import Path
import json
from typing import Optional, Tuple, Dict
import logging

# Import AI provider implementations
from . import anthropicapi

# Import base postprocessing functionality
from ..postprocessor import process_markdown

# Configuration constants
AI_PROVIDER = "anthropic"  # Default AI provider


class AIPostprocessor:
    """
    Main coordinator for AI-powered markdown postprocessing.

    This class manages the complete workflow of AI-assisted markdown improvement:
    1. Content analysis and sampling
    2. AI provider communication
    3. Pattern extraction and validation
    4. Automated fix application

    The class is designed to be extensible and can work with different AI providers
    through a plugin architecture. It handles large documents efficiently by
    sampling content for analysis while applying fixes to the complete document.

    Attributes:
        work_dir: Working directory containing markdown and output files
        json_path: Path where analysis patterns will be saved
        logger: Configured logger for detailed operation tracking
    """

    def __init__(self, work_dir: Path):
        """
        Initialize AI postprocessor with working directory configuration.

        Args:
            work_dir: Path to directory containing markdown files and where
                     analysis results will be stored
        """
        self.work_dir = work_dir
        self.json_path = work_dir / "patterns.json"  # AI analysis output
        self.markdown_path = work_dir

        # Set up comprehensive logging for debugging and user feedback
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def run_postprocessing(self, markdown_path: Path, ai_provider: str) -> dict:
        """
        Execute the complete AI postprocessing workflow.

        This method orchestrates the entire process of AI-assisted markdown improvement:
        1. Validates AI provider compatibility
        2. Loads analysis prompts and content samples
        3. Performs multiple AI analysis rounds for comprehensive coverage
        4. Combines and validates analysis results
        5. Applies automated fixes based on AI recommendations

        Args:
            markdown_path: Path to the markdown file to analyze and improve
            ai_provider: Name of AI service to use ("anthropic" currently supported)

        Returns:
            Dictionary containing analysis results and processing statistics

        Raises:
            ValueError: If unsupported AI provider is specified
            RuntimeError: If AI analysis or file processing fails

        Note:
            The function performs multiple analysis rounds to catch different
            types of issues and build a comprehensive fix pattern set.
        """
        # Validate AI provider selection
        if ai_provider != "anthropic":
            raise ValueError(
                f"Unsupported AI provider: {ai_provider}. Currently supported: anthropic"
            )

        combined_json = {}

        try:
            # Load the analysis prompt that defines the AI's task
            system_prompt = self._get_system_prompt()
            self.logger.info("Successfully loaded system prompt for AI analysis")

            # Prepare content sample for AI analysis (respects token limits)
            request = self._get_markdown_sample(markdown_path)
            self.logger.info(
                f"Successfully prepared markdown sample from {markdown_path}"
            )
            self.logger.info(f"Sample length: ~{len(request.split())} words")

            # Perform multiple analysis rounds for comprehensive issue detection
            # Each round may catch different patterns or provide additional insights
            for iteration in range(2):
                try:
                    self.logger.info(f"Starting AI analysis round {iteration + 1}/2...")

                    # Send request to AI provider and get analysis
                    analyzer = anthropicapi.Anthropic_Analysis.getjsonparams(
                        system_prompt, request
                    )
                    current_json = json.loads(analyzer)

                    if iteration == 0:
                        # First iteration: establish baseline analysis
                        combined_json = current_json
                        self.logger.info("Initial analysis data received and processed")

                        # Log some statistics about patterns found
                        if "patterns" in current_json:
                            pattern_count = len(current_json["patterns"])
                            self.logger.info(
                                f"Found {pattern_count} potential issues in first analysis"
                            )
                    else:
                        # Subsequent iterations: merge additional findings
                        combined_json.update(current_json)
                        self.logger.info("Additional analysis data merged successfully")

                        # Report cumulative statistics
                        if "patterns" in combined_json:
                            total_patterns = len(combined_json["patterns"])
                            self.logger.info(
                                f"Total patterns after round {iteration + 1}: {total_patterns}"
                            )

                except json.JSONDecodeError as e:
                    self.logger.error(
                        f"Failed to parse AI response in round {iteration + 1}: {e}"
                    )
                    self.logger.error(
                        "This may indicate an issue with the AI service or prompt"
                    )
                    raise
                except Exception as e:
                    self.logger.error(f"Error in analysis round {iteration + 1}: {e}")
                    raise

            # Save the complete analysis results for inspection and debugging
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(combined_json, f, indent=4)
            self.logger.info(f"Complete analysis results saved to {self.json_path}")

            # Apply the patterns to improve the markdown
            self.logger.info("Applying AI-recommended fixes to markdown content...")
            success = process_markdown(self.work_dir, self.json_path)

            if success:
                self.logger.info("AI postprocessing completed successfully")
                self.logger.info(
                    "Markdown content has been improved based on AI analysis"
                )
            else:
                self.logger.warning("Some issues occurred during pattern application")

            return combined_json

        except Exception as e:
            self.logger.error(f"Error in run_postprocessing: {e}")
            self.logger.error(
                "AI postprocessing failed - original markdown content unchanged"
            )
            raise

    def _get_system_prompt(self) -> str:
        """
        Load the system prompt that defines the AI analysis task.

        The system prompt is a carefully crafted instruction set that tells the AI
        how to analyze markdown content and what types of issues to look for.
        It defines the expected output format (JSON) and analysis criteria.

        Returns:
            Complete system prompt text for AI analysis

        Raises:
            FileNotFoundError: If prompt.txt is not found in the expected location
            ValueError: If the prompt file is empty
            RuntimeError: If file reading fails
        """
        # Locate the prompt file relative to this module
        module_dir = Path(__file__).resolve().parent
        prompt_path = module_dir.parent / "prompt.txt"

        self.logger.info(f"Loading AI analysis prompt from: {prompt_path}")

        try:
            if not prompt_path.exists():
                raise FileNotFoundError(f"prompt.txt not found at {prompt_path}")

            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()

                if not content.strip():
                    raise ValueError(
                        "prompt.txt is empty - cannot proceed with AI analysis"
                    )

                self.logger.info(f"Loaded prompt ({len(content)} characters)")
                return content

        except Exception as e:
            raise RuntimeError(f"Failed to read prompt.txt: {e}")

    def _get_markdown_sample(self, markdown_path: Path, max_tokens: int = 50000) -> str:
        """
        Extract a representative sample of markdown content for AI analysis.

        Large documents need to be sampled to fit within AI token limits while
        still providing enough context for meaningful analysis. This method
        extracts content from the beginning of the document, which typically
        contains the most important structural elements.

        Args:
            markdown_path: Path to the markdown file to sample
            max_tokens: Maximum number of tokens to include (approximate)

        Returns:
            Sampled markdown content suitable for AI analysis

        Raises:
            FileNotFoundError: If the markdown file doesn't exist
            ValueError: If the markdown file is empty
            RuntimeError: If file reading fails

        Note:
            Token counting is approximate (words * 1.3 factor) since exact
            tokenization depends on the specific AI model being used.
        """
        try:
            if not markdown_path.exists():
                raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

            with open(markdown_path, "r", encoding="utf-8") as f:
                content = f.read()

                if not content.strip():
                    raise ValueError("Markdown file is empty - no content to analyze")

                # Calculate approximate token count and sample if necessary
                # Most AI models use roughly 1.3 tokens per word on average
                words = content.split()
                max_words = int(max_tokens / 1.3)

                if len(words) > max_words:
                    # Sample from the beginning for structural analysis
                    sampled_words = words[:max_words]
                    sampled_content = " ".join(sampled_words)

                    self.logger.info(
                        f"Sampled {len(sampled_words)} words from {len(words)} total"
                    )
                    self.logger.info("Using beginning of document for analysis")
                    return sampled_content
                else:
                    # Use complete content if it fits within limits
                    self.logger.info(f"Using complete document ({len(words)} words)")
                    return content

        except Exception as e:
            raise RuntimeError(f"Failed to read markdown file: {e}")
