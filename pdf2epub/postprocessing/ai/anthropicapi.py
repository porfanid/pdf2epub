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
    @staticmethod
    def getjsonparams(system_prompt: str, request: str) -> str:
        """
        Analyze markdown with Claude and return a json object.
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not available. Install with: pip install anthropic==0.39.0")
            
        # Set up logging
        logger = logging.getLogger(__name__)
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please set it with your Anthropic API key."
            )
            
        client = anthropic.Client(api_key=api_key)
        
        try:
            # Create the message for Claude
            logger.info("Sending request to Claude...")
            message = client.beta.prompt_caching.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=8192,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": request
                            }
                        ]
                    }
                ],
                system=system_prompt
            )
            
            logger.info("Received response from Claude")
            
            # Extract content from response
            try:
                content = message.content[0].text
                return content
            except (AttributeError) as e:
                logger.error(f"Failed to parse Claude response: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error during AI analysis: {e}")
            raise