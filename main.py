import argparse
import os
import sys
import yaml
import json
from wisup_e2m import E2MParser, TextConverter
import logging
from datetime import datetime
from pathlib import Path
import litellm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_anthropic_key(api_key):
    """Test if the Anthropic API key is valid by making a minimal test request"""
    try:
        # Create minimal test message to validate auth
        messages = [{"role": "user", "content": "test"}]
        completion = litellm.completion(
            model="claude-3-haiku-20240307",
            messages=messages,
            api_key=api_key,
            max_tokens=1  # Minimize token usage for validation
        )
        return True
    except litellm.exceptions.AuthenticationError as e:
        logger.error(f"Authentication failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        return False

def resolve_api_key(config_api_key):
    """Resolve API key from config or environment with proper variable substitution"""
    if not config_api_key:
        return os.getenv('ANTHROPIC_API_KEY')
    
    if config_api_key.startswith('${') and config_api_key.endswith('}'):
        env_var = config_api_key[2:-1]  # Remove ${ and }
        return os.getenv(env_var)
    
    return config_api_key

def setup_argparser():
    parser = argparse.ArgumentParser(description='Convert PDF files to Markdown using e2m')
    parser.add_argument('pdf_files', nargs='+', help='One or more PDF files to convert')
    parser.add_argument('--output-dir', '-o', default='output',
                       help='Output directory for markdown files (default: output)')
    parser.add_argument('--intermediate-dir', '-t', default='intermediate',
                       help='Directory for intermediate parsed content (default: intermediate)')
    parser.add_argument('--config', '-c', default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    parser.add_argument('--image-dir', '-i', default='figures',
                       help='Directory for extracted images (default: figures)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    return parser

class PDF2Markdown:
    def __init__(self, pdf_files, output_dir, intermediate_dir, config, image_dir, debug):
        self.pdf_files = pdf_files
        self.output_dir = output_dir if output_dir else 'output'
        self.intermediate_dir = intermediate_dir if intermediate_dir else 'intermediate'
        self.config = config if config else Path(__file__).parent / 'config.yaml'
        self.image_dir = image_dir if image_dir else 'figures'
        self.debug = debug if debug else False
        
        # Load config first
        with open(self.config, 'r') as f:
            self.config_data = yaml.safe_load(f)

        # Get converter config
        converter_config = self.config_data.get('converters', {}).get('text_converter', {})
        
        # Resolve API key
        self.api_key = resolve_api_key(converter_config.get('api_key'))
        if not self.api_key:
            raise ValueError("No API key found. Set ANTHROPIC_API_KEY environment variable or configure in config.yaml")

        # Validate API key before proceeding
        if not validate_anthropic_key(self.api_key):
            raise ValueError("Invalid Anthropic API key. Please check your configuration.")
        
        
        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.intermediate_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

        # Initialize parser
        self.parser = E2MParser.from_config(self.config)
        
        # Initialize text converter
        self.text_converter = TextConverter(
            engine=converter_config.get('engine'),
            model=converter_config.get('model'),
            api_key=self.api_key,
            base_url=converter_config.get('base_url', ''),
            caching=False
        )

    def parse_pdf_files(self):
        for pdf_file in self.pdf_files:
            logger.info(f'Processing file: {pdf_file}')
            try:
                # Parse PDF
                parsed_data = self.parser.parse(
                    pdf_file,
                    work_dir=os.getcwd(),
                    image_dir=self.image_dir
                )
                
                # Convert the parsed content
                pdf_name = Path(pdf_file).stem
                output_file = Path(self.output_dir) / f"{pdf_name}.md"
                
                # Convert text content using TextConverter
                if parsed_data.text:
                    markdown_content = self.text_converter.convert(parsed_data.text)
                    
                    # Save the markdown content
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    logger.info(f'Successfully converted {pdf_file} to {output_file}')
                
                # Save intermediate content if in debug mode
                if self.debug:
                    intermediate_dir = Path(self.intermediate_dir) / f"{pdf_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    os.makedirs(intermediate_dir, exist_ok=True)
                    
                    with open(intermediate_dir / "raw_text.txt", 'w', encoding='utf-8') as f:
                        f.write(parsed_data.text)
                    
                    with open(intermediate_dir / "metadata.json", 'w', encoding='utf-8') as f:
                        json.dump(parsed_data.metadata, f, indent=4)
                
            except Exception as e:
                logger.error(f'Error processing {pdf_file}: {str(e)}')
                if self.debug:
                    raise

def main():
    parser = setup_argparser()
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        
    try:
        pdf2md = PDF2Markdown(
            args.pdf_files,
            args.output_dir,
            args.intermediate_dir,
            args.config,
            args.image_dir,
            args.debug
        )
        pdf2md.parse_pdf_files()
        logger.info('Conversion completed successfully!')
        
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f'Fatal error: {str(e)}')
        if args.debug:
            raise
        sys.exit(1)

if __name__ == '__main__':
    main()