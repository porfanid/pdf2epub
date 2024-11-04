import markdown
import os
from xml.dom import minidom
import zipfile
import sys
import json
from PIL import Image, ImageDraw, ImageFont
import textwrap
from pathlib import Path
import re

## markdown version 3.1



def process_markdown_for_images(markdown_text: str, work_dir: Path) -> tuple[str, list[str]]:
    """
    Process markdown content to find image references and ensure they are properly formatted for EPUB.
    Returns modified markdown text and list of image filenames.
    """
    print("Started processing markdown for images")
    
    image_pattern = r'!\[(.*?)\]\((.*?)\)'
    images_found = []
    modified_text = markdown_text
    
    # Find all image references in markdown
    for match in re.finditer(image_pattern, markdown_text):
        print(f"Found image: {match}")
        alt_text, image_path = match.groups()
        image_path = image_path.strip()
        print(f"Image path: {image_path}")
        # Convert path to Path object for manipulation
        img_path = Path(image_path)
        print(f"Image path: {img_path}")
        # Handle both absolute and relative paths
        if img_path.is_absolute():
            rel_path = img_path.relative_to(work_dir)
        else:
            rel_path = img_path
            
        # Ensure image exists in images directory
        full_image_path = work_dir / 'images' / img_path.name
        print(f"Full image path: {full_image_path}")
        if full_image_path.exists():
            # Add to list of found images
            images_found.append(img_path.name)
            
            # Update markdown to use EPUB-friendly path
            new_ref = f'![{alt_text}](images/{img_path.name})'
            modified_text = modified_text.replace(match.group(0), new_ref)
        else:
            print(f"Warning: Image not found: {full_image_path}")
    
    return modified_text, images_found

def copy_and_optimize_image(src_path: Path, dest_path: Path, max_dimension: int = 1800) -> None:
    """
    Copy image to destination path with optimization for EPUB.
    Resizes large images and converts to appropriate format.
    """
    from PIL import Image
    import io
    
    try:
        with Image.open(src_path) as img:
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                img = img.convert('RGB')
                
            # Calculate new dimensions while maintaining aspect ratio
            ratio = min(max_dimension / max(img.size[0], img.size[1]), 1.0)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            
            if ratio < 1.0:
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save with appropriate format and compression
            if src_path.suffix.lower() in ['.jpg', '.jpeg']:
                img.save(dest_path, 'JPEG', quality=85, optimize=True)
            elif src_path.suffix.lower() == '.png':
                img.save(dest_path, 'PNG', optimize=True)
            else:
                # Convert other formats to JPEG
                dest_path = dest_path.with_suffix('.jpg')
                img.save(dest_path, 'JPEG', quality=85, optimize=True)
                
    except Exception as e:
        print(f"Error processing image {src_path}: {e}")
        raise

def update_package_manifest(doc: minidom.Document, image_filenames: list[str], 
                          manifest: minidom.Element) -> None:
    """
    Update package manifest with image items, ensuring proper media types.
    """
    for i, image_filename in enumerate(image_filenames):
        item = doc.createElement('item')
        item.setAttribute('id', f"image-{i:05d}")
        item.setAttribute('href', f"images/{image_filename}")
        
        # Set appropriate media type based on file extension
        ext = Path(image_filename).suffix.lower()
        if ext in ['.jpg', '.jpeg']:
            media_type = 'image/jpeg'
        elif ext == '.png':
            media_type = 'image/png'
        elif ext == '.gif':
            media_type = 'image/gif'
        else:
            print(f"Warning: Unsupported image type {ext} for {image_filename}")
            continue
            
        item.setAttribute('media-type', media_type)
        manifest.appendChild(item)
        
def get_all_filenames(the_dir, extensions=[]):
    all_files = [x for x in os.listdir(the_dir)]
    all_files = [x for x in all_files if x.split(".")[-1] in extensions]
    return all_files

def get_packageOPF_XML(md_filenames=[], image_filenames=[], css_filenames=[], description_data=None):
    doc = minidom.Document()

    package = doc.createElement('package')
    package.setAttribute('xmlns',"http://www.idpf.org/2007/opf")
    package.setAttribute('version',"3.0")
    package.setAttribute('xml:lang',"en")
    package.setAttribute("unique-identifier","pub-id")

    ## Now building the metadata

    metadata = doc.createElement('metadata')
    metadata.setAttribute('xmlns:dc', 'http://purl.org/dc/elements/1.1/')

    for k,v in description_data["metadata"].items():
        if len(v):
            x = doc.createElement(k)
            for metadata_type,id_label in [("dc:title","title"),("dc:creator","creator"),("dc:identifier","book-id")]:
                if k==metadata_type:
                    x.setAttribute('id',id_label)
            x.appendChild(doc.createTextNode(v))
            metadata.appendChild(x)


    ## Now building the manifest

    manifest = doc.createElement('manifest')

    ## TOC.xhtml file for EPUB 3
    x = doc.createElement('item')
    x.setAttribute('id',"toc")
    x.setAttribute('properties',"nav")
    x.setAttribute('href',"TOC.xhtml")
    x.setAttribute('media-type',"application/xhtml+xml")
    manifest.appendChild(x)

    ## Ensure retrocompatibility by also providing a TOC.ncx file
    x = doc.createElement('item')
    x.setAttribute('id',"ncx")
    x.setAttribute('href',"toc.ncx")
    x.setAttribute('media-type',"application/x-dtbncx+xml")
    manifest.appendChild(x)

    x = doc.createElement('item')
    x.setAttribute('id',"titlepage")
    x.setAttribute('href',"titlepage.xhtml")
    x.setAttribute('media-type',"application/xhtml+xml")
    manifest.appendChild(x)

    for i,md_filename in enumerate(md_filenames):
        x = doc.createElement('item')
        x.setAttribute('id',"s{:05d}".format(i))
        x.setAttribute('href',"s{:05d}-{}.xhtml".format(i,md_filename.split(".")[0]))
        x.setAttribute('media-type',"application/xhtml+xml")
        manifest.appendChild(x)

    for i,image_filename in enumerate(image_filenames):
        x = doc.createElement('item')
        x.setAttribute('id',"image-{:05d}".format(i))
        x.setAttribute('href',"images/{}".format(image_filename))
        if "gif" in image_filename:
            x.setAttribute('media-type',"image/gif")
        elif "jpg" in image_filename:
            x.setAttribute('media-type',"image/jpeg")
        elif "jpeg" in image_filename:
            x.setAttribute('media-type',"image/jpg")
        elif "png" in image_filename:
            x.setAttribute('media-type',"image/png")
        if image_filename==description_data["cover_image"]:
            x.setAttribute('properties',"cover-image")

            ## Ensure compatibility by also providing a meta tag in the metadata
            y = doc.createElement('meta')
            y.setAttribute('name',"cover")
            y.setAttribute('content',"image-{:05d}".format(i))
            metadata.appendChild(y)
        manifest.appendChild(x)

    for i,css_filename in enumerate(css_filenames):
        x = doc.createElement('item')
        x.setAttribute('id',"css-{:05d}".format(i))
        x.setAttribute('href',"css/{}".format(css_filename))
        x.setAttribute('media-type',"text/css")
        manifest.appendChild(x)

    ## Now building the spine

    spine = doc.createElement('spine')
    spine.setAttribute('toc', "ncx")

    x = doc.createElement('itemref')
    x.setAttribute('idref',"titlepage")
    x.setAttribute('linear',"yes")
    spine.appendChild(x)
    for i,md_filename in enumerate(md_filenames):
        x = doc.createElement('itemref')
        x.setAttribute('idref',"s{:05d}".format(i))
        x.setAttribute('linear',"yes")
        spine.appendChild(x)

    guide = doc.createElement('guide')
    x = doc.createElement('reference')
    x.setAttribute('type',"cover")
    x.setAttribute('title',"Cover image")
    x.setAttribute('href',"titlepage.xhtml")
    guide.appendChild(x)


    package.appendChild(metadata)
    package.appendChild(manifest)
    package.appendChild(spine)
    package.appendChild(guide)
    doc.appendChild(package)

    return doc.toprettyxml()


def get_container_XML():
    container_data = """<?xml version="1.0" encoding="UTF-8" ?>\n"""
    container_data += """<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n"""
    container_data += """<rootfiles>\n"""
    container_data += """<rootfile full-path="OPS/package.opf" media-type="application/oebps-package+xml"/>\n"""
    container_data += """</rootfiles>\n</container>"""
    return container_data

def get_coverpage_XML(title):
    """Generate a simple cover page with title and optional author input."""
    
    authors = input("Please enter author(s) name(s): ").strip()
    
    # Escape special characters
    safe_title = title.replace('<', '&lt;').replace('>', '&gt;')
    safe_authors = authors.replace('<', '&lt;').replace('>', '&gt;')
    
    return f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<title>Cover Page</title>
<style type="text/css">
body {{ 
    margin: 0;
    padding: 0;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: serif;
}}
.cover {{
    padding: 3em;
    text-align: center;
    border: 1px solid #ccc;
    max-width: 80%;
}}
h1 {{
    font-size: 2em;
    margin-bottom: 1em;
    line-height: 1.2;
    color: #333;
}}
p {{
    font-size: 1.2em;
    font-style: italic;
    color: #666;
    line-height: 1.4;
}}
</style>
</head>
<body>
    <div class="cover">
        <h1>{safe_title}</h1>
        <p>{safe_authors}</p>
    </div>
</body>
</html>"""

def get_TOC_XML(default_css_filenames, markdown_filenames):
    ## Returns the XML data for the TOC.xhtml file

    toc_xhtml = """<?xml version="1.0" encoding="UTF-8"?>\n"""
    toc_xhtml += """<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">\n"""
    toc_xhtml += """<head>\n<meta http-equiv="default-style" content="text/html; charset=utf-8"/>\n"""
    toc_xhtml += """<title>Contents</title>\n"""

    for css_filename in default_css_filenames:
        toc_xhtml += """<link rel="stylesheet" href="css/{}" type="text/css"/>\n""".format(css_filename)

    toc_xhtml += """</head>\n<body>\n"""
    toc_xhtml += """<nav epub:type="toc" role="doc-toc" id="toc">\n<h2>Contents</h2>\n<ol epub:type="list">"""
    for i,md_filename in enumerate(markdown_filenames):
        toc_xhtml += """<li><a href="s{:05d}-{}.xhtml">{}</a></li>""".format(i,md_filename.split(".")[0],md_filename.split(".")[0])
    toc_xhtml += """</ol>\n</nav>\n</body>\n</html>"""

    return toc_xhtml

def get_TOCNCX_XML(markdown_filenames):
    ## Returns the XML data for the TOC.ncx file

    toc_ncx = """<?xml version="1.0" encoding="UTF-8"?>\n"""
    toc_ncx += """<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" xml:lang="fr" version="2005-1">\n"""
    toc_ncx += """<head>\n</head>\n"""
    toc_ncx += """<navMap>\n"""
    for i,md_filename in enumerate(markdown_filenames):
        toc_ncx += """<navPoint id="navpoint-{}">\n""".format(i)
        toc_ncx += """<navLabel>\n<text>{}</text>\n</navLabel>""".format(md_filename.split(".")[0])
        toc_ncx += """<content src="s{:05d}-{}.xhtml"/>""".format(i,md_filename.split(".")[0])
        toc_ncx += """ </navPoint>"""
    toc_ncx += """</navMap>\n</ncx>"""

    return toc_ncx

def get_chapter_XML(work_dir: str, md_filename: str, css_filenames: list[str]) -> tuple[str, list[str]]:
    """
    Convert markdown chapter to XHTML and process images.
    Returns tuple of (XHTML content, list of images referenced in chapter)
    """
    work_dir_path = Path(work_dir)
    
    with open(work_dir_path / md_filename, "r", encoding="utf-8") as f:
        markdown_data = f.read()
    
    # Process markdown for images and get list of referenced images
    markdown_data, chapter_images = process_markdown_for_images(markdown_data, work_dir_path)
    
    # Convert to HTML
    html_text = markdown.markdown(
        markdown_data,
        extensions=["codehilite", "tables", "fenced_code", "footnotes"],
        extension_configs={"codehilite": {"guess_lang": False}}
    )

    # Generate XHTML wrapper
    xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head>
    <meta http-equiv="default-style" content="text/html; charset=utf-8"/>
    {''.join(f'<link rel="stylesheet" href="css/{css}" type="text/css" media="all"/>' for css in css_filenames)}
</head>
<body>
{html_text}
</body>
</html>"""

    return xhtml, chapter_images

def generate_cover_image(title: str, authors: str, output_path: Path) -> str:
    """
    Generate a high-quality cover image with title and authors.
    Returns the filename of the generated cover image.
    """
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    # Create a high-resolution image with a white background
    width = 1800  # Increased resolution
    height = 2700 # 2:3 aspect ratio (typical book cover)
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    try:
        # Try to load a system font with larger sizes for higher resolution
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 160)
        author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 120)
    except OSError:
        try:
            # Try alternate font paths
            title_font = ImageFont.truetype("/Library/Fonts/Georgia Bold.ttf", 160)
            author_font = ImageFont.truetype("/Library/Fonts/Georgia.ttf", 120)
        except OSError:
            # Fallback to default font if system font not available
            print("Warning: System fonts not found, using default font. Cover quality may be reduced.")
            title_font = ImageFont.load_default()
            author_font = ImageFont.load_default()

    # Draw a subtle gradient border
    border_width = 100
    for i in range(border_width):
        # Create a subtle gradient from dark gray to light gray
        color = (200 + i//2, 200 + i//2, 200 + i//2)
        draw.rectangle(
            [i, i, width-1-i, height-1-i], 
            outline=color, 
            width=1
        )

    # Calculate text positions with better margins
    margin = width // 6  # Larger margins for better aesthetics
    text_width = width - (2 * margin)
    title_lines = textwrap.wrap(title, width=25)  # Fewer characters per line for better readability
    author_lines = textwrap.wrap(authors, width=30)

    # Draw title
    y = height // 3
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        
        # Draw text shadow for depth
        shadow_offset = 3
        draw.text((x+shadow_offset, y+shadow_offset), line, fill=(100, 100, 100), font=title_font)
        draw.text((x, y), line, fill='black', font=title_font)
        
        y += title_font.size + 20

    # Draw authors
    y += 200  # More space between title and authors
    for line in author_lines:
        bbox = draw.textbbox((0, 0), line, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y), line, fill=(80, 80, 80), font=author_font)  # Darker gray for better contrast
        y += author_font.size + 20

    # Save the image with high quality
    cover_path = output_path / 'images' / 'cover.png'
    img.save(cover_path, "PNG", quality=95, dpi=(300, 300))
    return 'cover.png'

def get_metadata_with_user_input(metadata_file: Path) -> dict:
    """
    Read metadata from file and prompt for missing information.
    """
    metadata = {}
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read metadata file: {e}")
    
    # Get title and authors
    title = metadata.get('metadata', {}).get('dc:title', '')
    authors = metadata.get('metadata', {}).get('dc:creator', '')
    
    # If authors is missing or unknown, prompt user
    if not authors or authors == "Unknown Author" or authors == "PDF2EPUB Converter":
        print("\nNo author information found in metadata.")
        authors = input("Please enter the author(s) of the document: ").strip()
        
        # Update metadata with user input
        if 'metadata' not in metadata:
            metadata['metadata'] = {}
        metadata['metadata']['dc:creator'] = authors
        
        # Save updated metadata
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save updated metadata: {e}")
    
    return metadata

def main(args):
    if len(args) < 2:
        print("\nUsage:\n    python md2epub.py <markdown_directory> <output_file.epub>")
        exit(1)

    work_dir = args[0]
    output_path = args[1]

    images_dir = os.path.join(work_dir, 'images/')
    css_dir = os.path.join(work_dir, 'css/')

    try:
        # Reading the JSON file containing the description of the eBook
        description_path = os.path.join(work_dir, "description.json")
        if not os.path.exists(description_path):
            json_data = {
                "metadata": {
                    "dc:title": os.path.basename(work_dir),
                    "dc:creator": "Unknown Author",
                    "dc:identifier": "id-1",
                    "dc:language": "en",
                    "dc:rights": "All rights reserved",
                    "dc:publisher": "PDF2EPUB",
                    "dc:date": ""
                },
                "default_css": ["style.css"],
                "chapters": [],
                "cover_image": None
            }
            
            # Find all markdown files
            markdown_files = [f for f in os.listdir(work_dir) if f.endswith('.md')]
            for md_file in sorted(markdown_files):
                json_data["chapters"].append({
                    "markdown": md_file,
                    "css": ""
                })
            
            # Save the generated description.json
            with open(description_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2)
        else:
            with open(description_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

        # Get title and author
        title = json_data["metadata"].get("dc:title", "Untitled Document")
        authors = json_data["metadata"].get("dc:creator", None)
        
        # Create cover page HTML
        coverpage_data = get_coverpage_XML(title)

        # Compile list of files
        all_md_filenames = []
        all_css_filenames = json_data["default_css"][:]
        for chapter in json_data["chapters"]:
            if chapter["markdown"] not in all_md_filenames:
                all_md_filenames.append(chapter["markdown"])
            if len(chapter["css"]) and (chapter["css"] not in all_css_filenames):
                all_css_filenames.append(chapter["css"])
        
        all_image_filenames = get_all_filenames(images_dir, extensions=["gif", "jpg", "jpeg", "png"])

        # Create the EPUB file
        with zipfile.ZipFile(output_path, "w") as epub:
            # Write mimetype (must be first and uncompressed)
            epub.writestr("mimetype", "application/epub+zip")

            # Write container.xml
            epub.writestr("META-INF/container.xml", get_container_XML(), zipfile.ZIP_DEFLATED)

            # Write package.opf
            epub.writestr("OPS/package.opf", 
                get_packageOPF_XML(
                    md_filenames=all_md_filenames,
                    image_filenames=all_image_filenames,
                    css_filenames=all_css_filenames,
                    description_data=json_data
                ), 
                zipfile.ZIP_DEFLATED
            )

            # Write cover page
            epub.writestr("OPS/titlepage.xhtml", coverpage_data.encode('utf-8'), zipfile.ZIP_DEFLATED)

            all_referenced_images = set()

            # Write chapters
            for i, chapter in enumerate(json_data["chapters"]):
                css_files = json_data["default_css"][:]
                if chapter["css"]:
                    css_files.append(chapter["css"])
                    
                chapter_data, chapter_images = get_chapter_XML(work_dir, chapter["markdown"], css_files)
                all_referenced_images.update(chapter_images)
                
                epub.writestr(
                    f"OPS/s{i:05d}-{chapter['markdown'].split('.')[0]}.xhtml",
                    chapter_data.encode('utf-8'),
                    zipfile.ZIP_DEFLATED
                )

            # Process and copy images
            images_dir = Path(work_dir) / 'images'
            if images_dir.exists():
                epub_images_dir = Path(work_dir) / 'epub_images'
                epub_images_dir.mkdir(exist_ok=True)
                
                for image in all_referenced_images:
                    src_path = images_dir / image
                    if src_path.exists():
                        try:
                            dest_path = epub_images_dir / image
                            copy_and_optimize_image(src_path, dest_path)
                            
                            # Add optimized image to EPUB
                            with open(dest_path, "rb") as f:
                                epub.writestr(f"OPS/images/{image}", f.read(), zipfile.ZIP_DEFLATED)
                        except Exception as e:
                            print(f"Warning: Failed to process image {image}: {e}")
                    else:
                        print(f"Warning: Referenced image not found: {src_path}")
                
                # Cleanup temporary directory
                import shutil
                shutil.rmtree(epub_images_dir, ignore_errors=True)

            # Write TOC files
            epub.writestr("OPS/TOC.xhtml", 
                get_TOC_XML(json_data["default_css"], all_md_filenames),
                zipfile.ZIP_DEFLATED
            )
            
            epub.writestr("OPS/toc.ncx",
                get_TOCNCX_XML(all_md_filenames),
                zipfile.ZIP_DEFLATED
            )

            # Copy images
            if os.path.exists(images_dir):
                for image in all_image_filenames:
                    with open(os.path.join(images_dir, image), "rb") as f:
                        epub.writestr(f"OPS/images/{image}", f.read(), zipfile.ZIP_DEFLATED)

            # Copy CSS files
            if os.path.exists(css_dir):
                for css in all_css_filenames:
                    css_path = os.path.join(css_dir, css)
                    if os.path.exists(css_path):
                        with open(css_path, "rb") as f:
                            epub.writestr(f"OPS/css/{css}", f.read(), zipfile.ZIP_DEFLATED)
                    else:
                        # Create default CSS if file doesn't exist
                            default_css = """
                            @page { margin: 5%; }
                            html { font-size: 100%; }
                            body { 
                                margin: 0 auto;
                                max-width: 45em;
                                padding: 0.5em 1em;
                                text-align: justify;
                                font-family: serif;
                                font-size: 1rem;
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
                            .title { 
                                font-size: 1.8em;
                                font-weight: bold;
                                text-align: center;
                                margin: 2em 0 1em 0;
                            }
                            .authors { 
                                font-size: 1.1em;
                                text-align: center;
                                font-style: italic;
                                margin-bottom: 2em;
                                color: #555;
                            }
                        """
                            epub.writestr(f"OPS/css/{css}", default_css.encode('utf-8'), zipfile.ZIP_DEFLATED)

        print(f"EPUB creation complete: {output_path}")
        
    except Exception as e:
        import traceback
        print(f"Error processing {work_dir}:")
        print(traceback.format_exc())
        raise

if __name__ == "__main__":
    main(sys.argv[1:])