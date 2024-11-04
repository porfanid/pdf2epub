#!/usr/bin/env python3
import argparse
from pathlib import Path
import json
import shutil
import os
import modules.pdf2md as pdf2md
import modules.mark2epub as mark2epub



def prepare_epub_structure(markdown_dir: Path, epub_work_dir: Path) -> dict:
    """
    Prepare the directory structure required by mark2epub.
    Returns the description data required for the EPUB.
    """
    # Create work directory structure
    epub_work_dir.mkdir(parents=True, exist_ok=True)
    (epub_work_dir / 'images').mkdir(exist_ok=True)
    (epub_work_dir / 'css').mkdir(exist_ok=True)
    
    css_content = """
        @page {
            margin: 5%;
        }
        
        html {
            font-size: 100%; /* Base font size - allows user scaling */
        }
        
        body { 
            margin: 0 auto;
            max-width: 45em;
            padding: 0.5em 1em;
            text-align: justify;
            font-family: serif;
            font-size: 1rem; /* Use relative units */
            line-height: 1.5;
            color: #222;
        }
        
        h1, h2, h3, h4, h5, h6 { 
            text-align: left;
            color: #333;
            line-height: 1.2;
            margin: 1.5em 0 0.5em 0;
        }
        
        h1 { font-size: 1.5em; margin-top: 2em; }
        h2 { font-size: 1.3em; }
        h3 { font-size: 1.2em; }
        h4 { font-size: 1.1em; }
        h5, h6 { font-size: 1em; }
        
        p { 
            margin: 0.75em 0;
            line-height: 1.6;
        }
        
        img { 
            max-width: 100%; 
            height: auto;
            display: block;
            margin: 1em auto;
        }
        
        table { 
            border-collapse: collapse; 
            width: 100%;
            margin: 1em 0;
            font-size: 0.9em;
        }
        
        th, td { 
            border: 1px solid #ddd; 
            padding: 0.5em;
        }
        
        code { 
            background: #f4f4f4; 
            padding: 0.2em 0.4em;
            font-size: 0.9em;
            font-family: monospace;
            border-radius: 2px;
        }
        
        pre code {
            display: block;
            padding: 1em;
            overflow-x: auto;
            line-height: 1.4;
        }
        
        blockquote {
            margin: 1em 0;
            padding-left: 1em;
            border-left: 4px solid #ddd;
            color: #666;
        }
        
        .title { 
            font-size: 1.8em;
            font-weight: bold;
            text-align: center;
            margin: 2em 0 1em 0;
            line-height: 1.2;
        }
        
        .authors { 
            font-size: 1.1em;
            text-align: center;
            font-style: italic;
            margin-bottom: 2em;
            color: #555;
        }
        
        /* For E-readers with night mode support */
        @media (prefers-color-scheme: dark) {
            body { color: #eee; background: #222; }
            h1, h2, h3, h4, h5, h6 { color: #ddd; }
            code { background: #333; }
            blockquote { border-color: #444; color: #aaa; }
            th, td { border-color: #444; }
        }
        """
    with open(epub_work_dir / 'css' / 'style.css', 'w') as f:
        f.write(css_content)

    # Copy markdown and images
    markdown_files = list(markdown_dir.glob('*.md'))
    for md_file in markdown_files:
        shutil.copy2(md_file, epub_work_dir)
    
    image_dir = markdown_dir / 'images'
    if image_dir.exists():
        for img in image_dir.glob('*.*'):
            if img.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                shutil.copy2(img, epub_work_dir / 'images')
    
    # Get metadata with user input if needed
    metadata_file = markdown_dir / f"{markdown_dir.name}_metadata.json"
    metadata = mark2epub.get_metadata_with_user_input(metadata_file)
    
    # Generate cover page
    try:
        title = metadata.get('metadata', {}).get('dc:title', markdown_dir.stem)
        authors = metadata.get('metadata', {}).get('dc:creator', '')
        cover_image = mark2epub.generate_cover_image(title, authors, epub_work_dir)
    except Exception as e:
        print(f"Warning: Could not generate cover image: {e}")
        cover_image = None
    
    # Fallback to first image if cover generation fails
    if not cover_image:
        images = list((epub_work_dir / 'images').glob('*.*'))
        cover_image = images[0].name if images else None
        
    # Try to get metadata from the _metadata.json file if it exists
    metadata = {}
    metadata_file = markdown_dir / f"{markdown_dir.name}_metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read metadata file: {e}")

    description_data = {
        "metadata": {
            "dc:title": markdown_files[0].stem if markdown_files else "Converted Document",
            "dc:creator": metadata.get('creator', 'PDF2EPUB Converter'),
            "dc:identifier": metadata.get('identifier', 'id-1'),
            "dc:language": metadata.get('language', 'en'),
            "dc:rights": metadata.get('rights', 'Public Domain'),
            "dc:publisher": metadata.get('publisher', 'PDF2EPUB'),
            "dc:date": metadata.get('date', ''),
        },
        "cover_image": cover_image,
        "default_css": ["style.css"],
        "chapters": [
            {
                "markdown": md_file.name,
                "css": ""
            }
            for md_file in sorted(markdown_files, key=lambda x: x.stem)  # Sort files by name
        ]
    }
    
    with open(epub_work_dir / 'description.json', 'w') as f:
        json.dump(description_data, f, indent=2)
    
    return description_data

def convert_to_epub(markdown_dir: Path, output_path: Path) -> None:
    """
    Convert markdown files and images to EPUB format.
    """
    if not markdown_dir.exists():
        raise FileNotFoundError(f"Markdown directory not found: {markdown_dir}")
        
    if not list(markdown_dir.glob('*.md')):
        raise ValueError(f"No markdown files found in: {markdown_dir}")
    
    # Create temporary working directory for EPUB generation
    epub_work_dir = markdown_dir
    if epub_work_dir.exists():
        shutil.rmtree(epub_work_dir)
        
    try:
        # Prepare directory structure and get description data
        description_data = prepare_epub_structure(markdown_dir, epub_work_dir)
        
        # Set up mark2epub's working directory
        mark2epub.work_dir = str(epub_work_dir)
        
        # Generate EPUB file
        epub_path = markdown_dir / f"{markdown_dir.name}.epub"
        mark2epub.main([str(epub_work_dir), str(epub_path)])
                
    finally:
        # Cleanup temporary directory
        #if epub_work_dir.exists():
        #    shutil.rmtree(epub_work_dir)
        pass

def main():
    parser = argparse.ArgumentParser(
        description='Convert PDF files to EPUB format via Markdown'
    )
    parser.add_argument(
        'input_path',
        nargs='?',
        type=str,
        help='Path to input PDF file or directory (default: ./input/*.pdf)'
    )
    parser.add_argument(
        'output_path',
        nargs='?',
        type=str,
        help='Path to output directory (default: directory named after PDF)'
    )
    parser.add_argument(
        '--batch-multiplier',
        type=int,
        default=2,
        help='Multiplier for batch size (higher uses more memory but processes faster)'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help='Maximum number of pages to process'
    )
    parser.add_argument(
        '--start-page',
        type=int,
        default=None,
        help='Page number to start from'
    )
    parser.add_argument(
        '--langs',
        type=str,
        default=None,
        help='Comma-separated list of languages in the document'
    )
    parser.add_argument(
        '--skip-epub',
        action='store_true',
        help='Skip EPUB generation, only create markdown'
    )
    parser.add_argument(
        '--skip-md',
        action='store_true',
        help='Skip markdown generation, use existing markdown files'
    )
    
    args = parser.parse_args()
    
    # Get input path
    input_path = Path(args.input_path) if args.input_path else pdf2md.get_default_input_dir()
    
    # Get queue of PDFs to process
    queue = pdf2md.add_pdfs_to_queue(input_path)
    print(f"Found {len(queue)} PDF files to process")
    
    # Process each PDF
    for pdf_path in queue:
        print(f"\nProcessing: {pdf_path.name}")
        
        # Get output directory for this PDF
        if args.output_path:
            output_path = Path(args.output_path)
            markdown_dir = output_path / pdf_path.stem
        else:
            markdown_dir = pdf2md.get_default_output_dir(pdf_path)
            output_path = markdown_dir.parent
            
        try:
            # Check if markdown directory exists when skipping MD generation
            if args.skip_md:
                if not markdown_dir.exists():
                    print(f"Error: Markdown directory not found: {markdown_dir}")
                    continue
                print(f"Using existing markdown files from: {markdown_dir}")
                
            # Convert PDF to Markdown unless skipped
            if not args.skip_md:
                print("Converting PDF to Markdown...")
                pdf2md.convert_pdf(
                    str(pdf_path),
                    markdown_dir,
                    args.batch_multiplier,
                    args.max_pages,
                    args.start_page,
                    args.langs
                )
            
            # Convert Markdown to EPUB unless skipped
            if not args.skip_epub:
                print("Converting Markdown to EPUB...")
                convert_to_epub(markdown_dir, output_path)
                
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {str(e)}")
            continue

if __name__ == '__main__':
    main()