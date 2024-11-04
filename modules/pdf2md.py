import argparse
from pathlib import Path
import sys
import json
import marker 
from PIL import Image
import io

def get_default_output_dir(input_path: Path) -> Path:
    """
    Generate default output directory path based on input PDF path.
    Creates a directory with same name as PDF (without extension) next to the PDF.
    """
    return input_path.parent / input_path.stem

def get_default_input_dir() -> Path:
    """
    Get default input directory (./input) relative to current working directory.
    Creates it if it doesn't exist.
    """
    input_dir = Path.cwd() / 'input'
    input_dir.mkdir(exist_ok=True)
    return input_dir


def save_images(images: dict, image_dir: Path) -> None:
    """
    Save images with proper error handling and format detection.
    
    Args:
        images: Dictionary of images from marker-pdf conversion
        image_dir: Directory to save images to
    """
    
    if not images:
        print("No images found in document")
        return
        
    image_dir.mkdir(exist_ok=True)
    saved_count = 0
    
    for idx, image_data in enumerate(images.values()):
        try:
            # Skip if image data is None or empty
            if not image_data:
                continue
                
            image_path = image_dir / f"image_{idx}.png"
            
            # Handle different image data formats
            if isinstance(image_data, Image.Image):
                try:
                    # Save PIL Image directly
                    image_data.save(image_path)
                    saved_count += 1
                except Exception as e:
                    print(f"Error saving PIL Image {idx}: {str(e)}")
                    continue
                    
            elif isinstance(image_data, bytes):
                try:
                    img = Image.open(io.BytesIO(image_data))
                    img.save(image_path)
                    saved_count += 1
                except Exception as e:
                    print(f"Error processing bytes image {idx}: {str(e)}")
                    continue
                    
            elif isinstance(image_data, str):
                try:
                    if Path(image_data).exists():
                        img = Image.open(image_data)
                        img.save(image_path)
                        saved_count += 1
                    else:
                        print(f"Image path does not exist for image {idx}: {image_data}")
                except Exception as e:
                    print(f"Error processing string image path {idx}: {str(e)}")
                    continue
            else:
                print(f"Unsupported image data type for image {idx}: {type(image_data)}")
                continue
                
        except Exception as e:
            print(f"Error saving image {idx}: {str(e)}")
            continue
            
    if saved_count > 0:
        print(f"Successfully saved {saved_count} images to: {image_dir}")
    else:
        print("No valid images were found to save")

def convert_pdf(
    input_path: str,
    output_dir: Path,
    batch_multiplier: int = 2,
    max_pages: int = None,
    start_page: int = None,
    langs: str = None
) -> None:
    """
    Convert a single PDF file to markdown format with enhanced image handling.
    """
    try:
        # Load models
        from marker.models import load_all_models
        from marker.convert import convert_single_pdf
        
        model_lst = load_all_models()
        
        # Convert languages string to list if provided
        languages = [lang.strip() for lang in langs.split(',')] if langs else None
        
        # Convert the PDF
        full_text, images, metadata = convert_single_pdf(
            input_path,
            model_lst,
            batch_multiplier=batch_multiplier,
            max_pages=max_pages,
            start_page=start_page,
            langs=languages
        )
        
        # All output will go to the output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save markdown content
        md_output = output_dir / f"{Path(input_path).stem}.md"
        md_output.write_text(full_text, encoding='utf-8')
        print(f"Markdown saved to: {md_output}")
        
        # Save metadata as JSON
        meta_output = output_dir / f"{Path(input_path).stem}_metadata.json"
        with open(meta_output, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to: {meta_output}")
        
        # Enhanced image handling
        try:
            if images:
                image_dir = output_dir / "images"
                save_images(images, image_dir)
                
                # Cleanup PIL Images
                for img in images.values():
                    if isinstance(img, Image.Image):
                        try:
                            img.close()
                        except Exception as e:
                            print(f"Warning: Failed to close image: {e}")
                images.clear()  # Clear the dictionary to help with cleanup
        except Exception as e:
            print(f"Warning: Error during image cleanup: {e}")
            
    except Exception as e:
        print(f"Error converting {input_path}: {str(e)}", file=sys.stderr)
        sys.exit(1)

    
def add_pdfs_to_queue(input_path: Path) -> list[Path]:
    """
    Add PDF files to the processing queue.
    If input_path is a directory, add all PDFs in it.
    If input_path is a file, add just that file.
    """
    queue = []
    
    if input_path.is_dir():
        pdfs = list(input_path.glob('*.pdf'))
        if not pdfs:
            print(f"No PDF files found in directory: {input_path}", file=sys.stderr)
            sys.exit(1)
        queue.extend(pdfs)
    else:
        if not input_path.is_file():
            print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
            sys.exit(1)
        if input_path.suffix.lower() != '.pdf':
            print(f"Error: Input file must be a PDF: {input_path}", file=sys.stderr)
            sys.exit(1)
        queue.append(input_path)
        
    return queue

if __name__=="__main__":
    pass