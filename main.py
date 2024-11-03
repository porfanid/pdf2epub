import argparse
import os
import sys
import yaml
from wisup_e2m import E2MParser

def setup_argparser():
    parser = argparse.ArgumentParser(description='Convert PDF files to Markdown using e2m')
    parser.add_argument('pdf_files', nargs='+', help='One or more PDF files to convert')
    parser.add_argument('--output-dir', '-o', default='output',
                       help='Output directory for markdown files (default: output)')
    parser.add_argument('--config', '-c', default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    return parser

def create_default_config():
    """Create a default configuration file if it doesn't exist."""
    config = {
        'parsers': {
            'pdf_parser': {
                'engine': 'marker',  # Using marker engine as it directly converts to markdown
                'langs': ['en', 'zh']
            }
        },
        'converters': {
            'text_converter': {
                'engine': 'litellm',
                'model': 'claude-3-haiku-20240307',
                'api_key': 'YOUR_API_KEY_HERE',
                'base_url': 'https://api.anthropic.com/v1'
            }
        }
    }
    
    with open('config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print("Created default config.yaml. Please edit it with your API key and settings.")
    sys.exit(1)

def main():
    parser = setup_argparser()
    args = parser.parse_args()
    
    # Check if config file exists, if not create default
    if not os.path.exists(args.config):
        create_default_config()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize E2MParser with config
    try:
        parser = E2MParser.from_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Process each PDF file
    for pdf_file in args.pdf_files:
        if not os.path.exists(pdf_file):
            print(f"Warning: File not found: {pdf_file}")
            continue
            
        print(f"Processing: {pdf_file}")
        try:
            # Parse the PDF
            data = parser.parse(pdf_file)
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(pdf_file))[0]
            output_file = os.path.join(args.output_dir, f"{base_name}.md")
            
            # Write the markdown output
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(data.text)
            
            print(f"Successfully converted {pdf_file} to {output_file}")
            
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

if __name__ == '__main__':
    main()