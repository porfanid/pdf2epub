"""
Anthropic Claude API integration for markdown content analysis.

This module provides a concrete implementation of AI-powered text analysis using
Anthropic's Claude API. It handles API authentication, request formatting,
response parsing, and error management for reliable AI service integration.

Features:
- Secure API key management through environment variables
- Optimized model selection for content analysis tasks
- Comprehensive error handling and logging
- Token-efficient prompt caching for better performance
- Response validation and parsing

The module is designed to be part of a larger plugin architecture, allowing
for easy integration of additional AI providers in the future.
"""

# Optional dependency: Anthropic SDK for Claude API access
# This allows graceful degradation when the service is not available
try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

import os
from typing import Optional, Tuple
import json
import logging


class Anthropic_Analysis:
    """
    Interface for Anthropic Claude API-based markdown content analysis.

    This class provides a clean interface for sending markdown content to
    Claude for analysis and receiving structured recommendations for improvements.
    It handles all the complexities of API communication, error management,
    and response validation.
    """

    @staticmethod
    def getjsonparams(system_prompt: str, request: str) -> str:
        """
        Analyze markdown content using Claude and return structured analysis results.

        This method sends markdown content to Claude for comprehensive analysis,
        requesting identification of formatting issues, OCR errors, structural
        problems, and other quality issues that can be programmatically fixed.

        Args:
            system_prompt: Detailed instructions defining the analysis task and
                          expected output format
            request: Markdown content to analyze

        Returns:
            JSON string containing structured analysis results with patterns
            and recommendations for fixes

        Raises:
            ImportError: If anthropic package is not installed
            RuntimeError: If API key is not configured
            Exception: If API communication fails or response is invalid

        Note:
            Uses Claude 3.5 Haiku model optimized for analysis tasks with
            prompt caching for improved performance on repeated requests.
        """
        # Verify Anthropic SDK is available
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not available. Install with: pip install anthropic==0.39.0"
            )

        # Set up logging for API operations
        logger = logging.getLogger(__name__)

        # Validate API key configuration
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please set it with your Anthropic API key. "
                "Get one at: https://console.anthropic.com/"
            )

        # Initialize the API client with authentication
        client = anthropic.Client(api_key=api_key)

        try:
            # Send analysis request to Claude
            logger.info("Sending markdown analysis request to Claude...")
            logger.info(f"Content length: ~{len(request.split())} words")

            # Use beta prompt caching API for improved performance
            # This caches the system prompt to reduce costs on repeated requests
            message = client.beta.prompt_caching.messages.create(
                model="claude-3-5-haiku-20241022",  # Optimized for analysis tasks
                max_tokens=8192,  # Sufficient for detailed JSON responses
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": request}]}
                ],
                system=system_prompt,  # Cached for efficiency
            )

            logger.info("Received response from Claude")
            logger.info(
                f"Response tokens: {message.usage.output_tokens if hasattr(message, 'usage') else 'unknown'}"
            )

            # Extract and validate response content
            try:
                content = message.content[0].text

                # Basic validation that response looks like JSON
                if not content.strip().startswith("{"):
                    logger.warning("Response doesn't appear to be JSON format")
                    logger.warning(f"Response preview: {content[:200]}...")

                return content

            except (AttributeError, IndexError) as e:
                logger.error(f"Failed to parse Claude response structure: {e}")
                logger.error("This may indicate an API format change")
                raise

        except Exception as e:
            logger.error(f"Error during AI analysis: {e}")
            logger.error(
                "This could be due to network issues, API limits, or service problems"
            )
            raise
