import argparse
import os
import sys
import yaml
from wisup_e2m import E2MParser, E2MConverter

def setup_argparser():
    parser = argparse.ArgumentParser(description='Convert PDF files to Markdown using e2m')
    parser.add_argument('pdf_files', nargs='+', help='One or more PDF files to convert')
    parser.add_argument('--output-dir', '-o', default='output',
                       help='Output directory for markdown files (default: output)')
    parser.add_argument('--config', '-c', default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    parser.add_argument('--image-dir', '-i', default='figures',
                       help='Directory for extracted images (default: figures)')
    return parser

def create_default_config():
    """Create a default configuration file if it doesn't exist."""
    config = {
        'parsers': {
            'pdf_parser': {
                'engine': 'unstructured',
                'langs': ['en', 'de'],
                'ocr_languages': ['deu']
            }
        },
        'converters': {
            'text_converter': {
                'engine': 'litellm',
                'model': 'claude-3-haiku-20240307',
                'api_key': 'YOUR_API_KEY_HERE',
                'base_url': 'https://api.anthropic.com/v1',
                'cache_type': 'disk-cache'
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
    
    # Create output, image, and cache directories if they don't exist
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.image_dir, exist_ok=True)
    os.makedirs(".litellm_cache", exist_ok=True)
    
    # Initialize E2MParser and E2MConverter with config
    try:
        parser = E2MParser.from_config(args.config)
        converter = E2MConverter.from_config(args.config)
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
            # First pass: Extract raw content and images
            parsed_data = parser.parse(pdf_file)
            
            if not parsed_data:
                print(f"Error: Parser returned no data for {pdf_file}")
                continue
            
            if not hasattr(parsed_data, 'text'):
                print(f"Error: Parsed data has no text attribute for {pdf_file}")
                print(f"Returned data type: {type(parsed_data)}")
                print(f"Available attributes: {dir(parsed_data)}")
                continue
            
            if not parsed_data.text:
                print(f"Warning: Parsed text is empty for {pdf_file}")
                continue
                
            # Second pass: Use AI to convert to proper markdown structure
            print("Converting to structured markdown...")
            conversion_args = {
                'text': parsed_data.text
            }
            if hasattr(parsed_data, 'images') and parsed_data.images:
                conversion_args['images'] = parsed_data.images
                conversion_args['work_dir'] = os.path.abspath(args.image_dir)
                
            converted_text = converter.convert_to_md(**conversion_args)
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(pdf_file))[0]
            output_file = os.path.join(args.output_dir, f"{base_name}.md")
            
            # Write the markdown output
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(converted_text)
            
            print(f"Successfully converted {pdf_file} to {output_file}")
            if hasattr(parsed_data, 'images') and parsed_data.images:
                print(f"Images saved in: {args.image_dir}")
            
        except Exception as e:
            print(f"Error processing {pdf_file}:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            import traceback
            print("Full traceback:")
            print(traceback.format_exc())

if __name__ == '__main__':
    main()