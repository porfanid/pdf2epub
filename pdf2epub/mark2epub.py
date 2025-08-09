"""
Markdown to EPUB conversion module with comprehensive format support.

This module converts Markdown files and associated images into EPUB format,
following the EPUB 3.0 specification. It provides a complete pipeline from
markdown input to a valid EPUB file that can be read by most e-readers.

Key features:
- EPUB 3.0 compliance with backwards compatibility
- Interactive metadata collection
- Image optimization and format conversion
- CSS styling support
- Table of contents generation (both XHTML and NCX formats)
- Markdown extensions (code highlighting, tables, footnotes)
- Memory-efficient processing for large documents

EPUB Structure Created:
- mimetype: Required EPUB identifier
- META-INF/container.xml: Points to the package manifest
- OPS/package.opf: Main manifest with metadata, file listings, and reading order
- OPS/titlepage.xhtml: Generated cover page
- OPS/TOC.xhtml: EPUB 3.0 navigation document
- OPS/toc.ncx: EPUB 2.0 compatibility navigation
- OPS/s#####-*.xhtml: Individual chapter files
- OPS/images/: Optimized images
- OPS/css/: Stylesheets
"""

# Core dependencies
import os
from xml.dom import minidom
import zipfile
import sys
import json
from pathlib import Path
from datetime import datetime
import subprocess
from typing import Dict, Optional, Tuple

# Optional dependency: markdown for content conversion
# This is a core dependency for the package functionality
try:
    import markdown

    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    markdown = None

# Optional dependency: PIL for image processing and optimization
# If not available, images will be copied without optimization
try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

# Optional dependency: regex for enhanced pattern matching
# Falls back to standard re module if not available
try:
    import regex as re

    REGEX_AVAILABLE = True
except ImportError:
    REGEX_AVAILABLE = False
    import re


def get_user_input(prompt: str, default: str = "") -> str:
    """
    Get user input with a default value and input validation.

    Provides a consistent interface for collecting user input throughout
    the EPUB creation process, with clear indication of default values.

    Args:
        prompt: The prompt text to display to the user
        default: Default value if user presses Enter without input

    Returns:
        User input string, or default if no input provided
    """
    user_input = input(f"{prompt} [{default}]: ").strip()
    return user_input if user_input else default


def get_metadata_from_user(
    existing_metadata: Optional[Dict] = None, batch_mode: bool = False
) -> Dict:
    """
    Interactively collect EPUB metadata from user with intelligent defaults.

    This function guides the user through providing essential EPUB metadata
    required by the EPUB specification. It uses existing metadata as defaults
    when available, making it suitable for updating existing projects.

    Args:
        existing_metadata: Optional dictionary containing previously saved metadata
        batch_mode: If True, use defaults without prompting for user input

    Returns:
        Complete metadata dictionary with all required EPUB fields

    EPUB Metadata Fields Collected:
        - dc:title: Book title (required)
        - dc:creator: Author name(s) (required)
        - dc:identifier: Unique book identifier (required)
        - dc:language: Language code (required)
        - dc:rights: Copyright information
        - dc:publisher: Publisher name
        - dc:date: Publication date
    """
    if existing_metadata is None:
        existing_metadata = {}

    # Extract existing metadata or use empty dict
    metadata = existing_metadata.get("metadata", {})

    # In batch mode, use defaults without prompting
    if batch_mode:
        print("Running in batch mode - using default metadata values")
        fields = {
            "dc:title": metadata.get("dc:title", "Untitled Document"),
            "dc:creator": metadata.get("dc:creator", "Unknown Author"),
            "dc:identifier": metadata.get(
                "dc:identifier", f"id-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            ),
            "dc:language": metadata.get("dc:language", "en"),
            "dc:rights": metadata.get("dc:rights", "All rights reserved"),
            "dc:publisher": metadata.get("dc:publisher", "PDF2EPUB"),
            "dc:date": metadata.get("dc:date", datetime.now().strftime("%Y-%m-%d")),
        }
        updated_metadata = fields
    else:
        print(
            "\nPlease provide the following metadata for your EPUB (press Enter to use default value):"
        )
        print(
            "This information will be embedded in the EPUB file and shown by e-readers.\n"
        )

        # Define all metadata fields with their prompts and intelligent defaults
        fields = {
            "dc:title": ("Title", metadata.get("dc:title", "Untitled Document")),
            "dc:creator": ("Author(s)", metadata.get("dc:creator", "Unknown Author")),
            "dc:identifier": (
                "Unique Identifier",
                metadata.get(
                    "dc:identifier", f"id-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                ),
            ),
            "dc:language": (
                "Language (e.g., en, de, fr)",
                metadata.get("dc:language", "en"),
            ),
            "dc:rights": ("Rights", metadata.get("dc:rights", "All rights reserved")),
            "dc:publisher": ("Publisher", metadata.get("dc:publisher", "PDF2EPUB")),
            "dc:date": (
                "Publication Date (YYYY-MM-DD)",
                metadata.get("dc:date", datetime.now().strftime("%Y-%m-%d")),
            ),
        }

        # Collect input for each field
        updated_metadata = {}
        for key, (prompt, default) in fields.items():
            value = get_user_input(prompt, default)
            updated_metadata[key] = value

    # Return complete metadata structure with defaults for optional fields
    return {
        "metadata": updated_metadata,
        "default_css": existing_metadata.get("default_css", ["style.css"]),
        "chapters": existing_metadata.get("chapters", []),
        "cover_image": existing_metadata.get("cover_image", None),
    }


def review_markdown(markdown_path: Path, batch_mode: bool = False) -> tuple[bool, str]:
    """
    Allow user to review and edit markdown content before EPUB conversion.

    This function provides an opportunity for users to make final edits to
    their markdown content before it's converted to EPUB format. It attempts
    to open the file in the system's default editor and waits for confirmation.

    Args:
        markdown_path: Path to the markdown file to review
        batch_mode: If True, skip review and use content as-is

    Returns:
        Tuple of (should_continue: bool, content: str)
        - should_continue: False if user wants to abort conversion
        - content: Updated markdown content after any edits

    Note:
        Uses system default application for .md files. On Linux uses xdg-open,
        on Windows uses start command. Falls back gracefully if opening fails.
    """
    # Read the current content
    content = markdown_path.read_text(encoding="utf-8")

    # In batch mode, skip review and proceed with current content
    if batch_mode:
        print(
            f"Batch mode: Using markdown content from {markdown_path.name} without review"
        )
        return True, content

    while True:
        response = input(
            "\nWould you like to review the markdown file before conversion? (y/n): "
        ).lower()

        if response in ["y", "yes"]:
            try:
                # Try to open file with system default editor
                # This allows users to make final edits before conversion
                print(f"Opening {markdown_path.name} in default editor...")
                command = "xdg-open" if os.name == "posix" else "start"
                subprocess.run([command, str(markdown_path)], check=True)

                # Wait for user to finish editing
                while True:
                    proceed = input(
                        "\nPress Enter when you're done editing (or 'q' to abort): "
                    ).lower()
                    if proceed == "q":
                        print("Conversion aborted by user.")
                        return False, content
                    elif proceed == "":
                        # Reload content after editing
                        updated_content = markdown_path.read_text(encoding="utf-8")
                        print("Using updated content for conversion.")
                        return True, updated_content

            except Exception as e:
                print(f"\nError opening markdown file: {e}")
                print(
                    "This might happen if no default editor is configured for .md files."
                )
                print("Proceeding with conversion using current content...")
                return True, content

        elif response in ["n", "no"]:
            print("Proceeding with conversion without review.")
            return True, content
        else:
            print("Please enter 'y' or 'n'")


def process_markdown_for_images(
    markdown_text: str, work_dir: Path
) -> tuple[str, list[str]]:
    """
    Process markdown content to find and normalize image references.

    This function scans markdown content for image references and updates them
    to use relative paths suitable for EPUB format. It also collects a list
    of all referenced images for processing.

    Args:
        markdown_text: Raw markdown content to process
        work_dir: Working directory containing the markdown and images

    Returns:
        Tuple of (modified_text: str, images_found: list[str])
        - modified_text: Markdown with normalized image paths
        - images_found: List of image filenames referenced in the markdown

    Image Path Processing:
        - Converts absolute paths to relative paths
        - Normalizes all image references to images/ directory
        - Warns about missing images but continues processing

    Example:
        Input:  ![Chart](/absolute/path/chart.png)
        Output: ![Chart](images/chart.png)
    """
    # Regex pattern to match markdown image syntax: ![alt text](path)
    image_pattern = r"!\[(.*?)\]\((.*?)\)"
    images_found = []
    modified_text = markdown_text

    # Find all image references in the markdown
    for match in re.finditer(image_pattern, markdown_text):
        alt_text, image_path = match.groups()
        image_path = image_path.strip()

        # Convert to Path object for easier manipulation
        img_path = Path(image_path)

        # Handle absolute vs relative paths
        if img_path.is_absolute():
            # Convert absolute path to relative from work directory
            try:
                rel_path = img_path.relative_to(work_dir)
            except ValueError:
                # Path is not relative to work_dir, just use filename
                rel_path = img_path
        else:
            rel_path = img_path

        # Check if the actual image file exists
        full_image_path = work_dir / "images" / img_path.name
        if full_image_path.exists():
            # Add to list of found images
            images_found.append(img_path.name)

            # Update the markdown to use standardized path
            new_ref = f"![{alt_text}](images/{img_path.name})"
            modified_text = modified_text.replace(match.group(0), new_ref)
        else:
            # Warn about missing images but don't fail conversion
            print(f"Warning: Image not found: {full_image_path}")

    return modified_text, images_found


def copy_and_optimize_image(
    src_path: Path, dest_path: Path, max_dimension: int = 1800
) -> None:
    """
    Copy and optimize images for EPUB format with size and quality constraints.

    This function optimizes images for e-reader compatibility by:
    - Converting RGBA to RGB (removing transparency)
    - Resizing large images to reasonable dimensions
    - Compressing with appropriate quality settings
    - Converting to standard formats (JPEG/PNG)

    Args:
        src_path: Source image file path
        dest_path: Destination image file path
        max_dimension: Maximum width or height in pixels (default: 1800)

    Note:
        If PIL is not available, performs simple file copy without optimization.
        Most e-readers handle images better when they're under 2MB and 1800px.
    """
    if not PIL_AVAILABLE:
        # Fallback: simple file copy without optimization
        import shutil

        shutil.copy2(src_path, dest_path)
        return

    try:
        with Image.open(src_path) as img:
            # Convert RGBA to RGB to remove transparency
            # Many e-readers don't handle transparency well
            if img.mode == "RGBA":
                # Create white background for transparency
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                img = background

            # Calculate resize ratio if image is too large
            # Keeps aspect ratio while ensuring both dimensions fit within max_dimension
            ratio = min(max_dimension / max(img.size[0], img.size[1]), 1.0)

            if ratio < 1.0:
                # Resize image using high-quality resampling
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                print(f"Resized {src_path.name} from {img.size} to {new_size}")

            # Save with format-appropriate settings
            if src_path.suffix.lower() in [".jpg", ".jpeg"]:
                # JPEG: Use quality=85 for good compression with minimal quality loss
                img.save(dest_path, "JPEG", quality=85, optimize=True)
            elif src_path.suffix.lower() == ".png":
                # PNG: Use optimization to reduce file size
                img.save(dest_path, "PNG", optimize=True)
            else:
                # Unknown format: convert to JPEG with .jpg extension
                dest_path = dest_path.with_suffix(".jpg")
                img.save(dest_path, "JPEG", quality=85, optimize=True)

    except Exception as e:
        print(f"Error processing image {src_path}: {e}")
        raise


def update_package_manifest(
    doc: minidom.Document, image_filenames: list[str], manifest: minidom.Element
) -> None:
    """
    Update package manifest with image items, ensuring proper media types.
    """
    for i, image_filename in enumerate(image_filenames):
        item = doc.createElement("item")
        item.setAttribute("id", f"image-{i:05d}")
        item.setAttribute("href", f"images/{image_filename}")

        # Set appropriate media type based on file extension
        ext = Path(image_filename).suffix.lower()
        if ext in [".jpg", ".jpeg"]:
            media_type = "image/jpeg"
        elif ext == ".png":
            media_type = "image/png"
        elif ext == ".gif":
            media_type = "image/gif"
        else:
            print(f"Warning: Unsupported image type {ext} for {image_filename}")
            continue

        item.setAttribute("media-type", media_type)
        manifest.appendChild(item)


def get_all_filenames(the_dir, extensions=[]):
    all_files = [x for x in os.listdir(the_dir)]
    all_files = [x for x in all_files if x.split(".")[-1] in extensions]
    return all_files


def get_packageOPF_XML(
    md_filenames=[], image_filenames=[], css_filenames=[], description_data=None
):
    """
    Generate the EPUB package manifest (OPF file) according to EPUB 3.0 specification.

    The OPF file is the heart of an EPUB - it defines:
    - Metadata about the publication
    - Manifest of all files in the EPUB
    - Spine defining the reading order
    - Guide for special pages (cover, etc.)

    Args:
        md_filenames: List of markdown/chapter filenames
        image_filenames: List of image filenames in the EPUB
        css_filenames: List of CSS stylesheet filenames
        description_data: Dictionary containing metadata and configuration

    Returns:
        XML string containing the complete OPF package document

    EPUB Structure Created:
        - Package element with namespaces and version info
        - Metadata section with Dublin Core elements
        - Manifest listing all files with proper media types
        - Spine defining reading order
        - Guide for backwards compatibility
    """
    # Create XML document with proper structure
    doc = minidom.Document()

    # Root package element with EPUB 3.0 namespaces
    package = doc.createElement("package")
    package.setAttribute("xmlns", "http://www.idpf.org/2007/opf")
    package.setAttribute("version", "3.0")  # EPUB 3.0 specification
    package.setAttribute("xml:lang", "en")
    package.setAttribute("unique-identifier", "pub-id")

    ## Build metadata section using Dublin Core elements
    metadata = doc.createElement("metadata")
    metadata.setAttribute("xmlns:dc", "http://purl.org/dc/elements/1.1/")

    # Add each metadata field from user input
    for k, v in description_data["metadata"].items():
        if len(v):  # Only add non-empty metadata
            x = doc.createElement(k)
            # Add special id attributes for key metadata elements
            for metadata_type, id_label in [
                ("dc:title", "title"),
                ("dc:creator", "creator"),
                ("dc:identifier", "book-id"),
            ]:
                if k == metadata_type:
                    x.setAttribute("id", id_label)
            x.appendChild(doc.createTextNode(v))
            metadata.appendChild(x)

    ## Build manifest section - lists all files in the EPUB
    manifest = doc.createElement("manifest")

    # Navigation document (TOC.xhtml) - required for EPUB 3
    x = doc.createElement("item")
    x.setAttribute("id", "toc")
    x.setAttribute("properties", "nav")  # EPUB 3 navigation properties
    x.setAttribute("href", "TOC.xhtml")
    x.setAttribute("media-type", "application/xhtml+xml")
    manifest.appendChild(x)

    # NCX file for EPUB 2 backwards compatibility
    x = doc.createElement("item")
    x.setAttribute("id", "ncx")
    x.setAttribute("href", "toc.ncx")
    x.setAttribute("media-type", "application/x-dtbncx+xml")
    manifest.appendChild(x)

    # Title/cover page
    x = doc.createElement("item")
    x.setAttribute("id", "titlepage")
    x.setAttribute("href", "titlepage.xhtml")
    x.setAttribute("media-type", "application/xhtml+xml")
    manifest.appendChild(x)

    # Add each chapter/markdown file as XHTML
    for i, md_filename in enumerate(md_filenames):
        x = doc.createElement("item")
        x.setAttribute("id", "s{:05d}".format(i))  # Sequential IDs for chapters
        x.setAttribute("href", "s{:05d}-{}.xhtml".format(i, md_filename.split(".")[0]))
        x.setAttribute("media-type", "application/xhtml+xml")
        manifest.appendChild(x)

    # Add images with proper media types
    for i, image_filename in enumerate(image_filenames):
        x = doc.createElement("item")
        x.setAttribute("id", "image-{:05d}".format(i))
        x.setAttribute("href", "images/{}".format(image_filename))

        # Set media type based on file extension
        if "gif" in image_filename:
            x.setAttribute("media-type", "image/gif")
        elif "jpg" in image_filename:
            x.setAttribute("media-type", "image/jpeg")
        elif "jpeg" in image_filename:
            x.setAttribute("media-type", "image/jpg")
        elif "png" in image_filename:
            x.setAttribute("media-type", "image/png")

        # Mark cover image if specified
        if image_filename == description_data["cover_image"]:
            x.setAttribute("properties", "cover-image")

            # Add compatibility meta tag for EPUB 2 readers
            y = doc.createElement("meta")
            y.setAttribute("name", "cover")
            y.setAttribute("content", "image-{:05d}".format(i))
            metadata.appendChild(y)
        manifest.appendChild(x)

    # Add CSS stylesheets
    for i, css_filename in enumerate(css_filenames):
        x = doc.createElement("item")
        x.setAttribute("id", "css-{:05d}".format(i))
        x.setAttribute("href", "css/{}".format(css_filename))
        x.setAttribute("media-type", "text/css")
        manifest.appendChild(x)

    ## Build spine section - defines reading order
    spine = doc.createElement("spine")
    spine.setAttribute("toc", "ncx")  # Reference to NCX for EPUB 2 compatibility

    # Cover page first
    x = doc.createElement("itemref")
    x.setAttribute("idref", "titlepage")
    x.setAttribute("linear", "yes")
    spine.appendChild(x)

    # Then all chapters in order
    for i, md_filename in enumerate(md_filenames):
        x = doc.createElement("itemref")
        x.setAttribute("idref", "s{:05d}".format(i))
        x.setAttribute("linear", "yes")
        spine.appendChild(x)

    # Guide section for special pages (EPUB 2 compatibility)
    guide = doc.createElement("guide")
    x = doc.createElement("reference")
    x.setAttribute("type", "cover")
    x.setAttribute("title", "Cover image")
    x.setAttribute("href", "titlepage.xhtml")
    guide.appendChild(x)

    # Assemble the complete package
    package.appendChild(metadata)
    package.appendChild(manifest)
    package.appendChild(spine)
    package.appendChild(guide)
    doc.appendChild(package)

    return doc.toprettyxml()


def get_container_XML():
    """
    Generate the EPUB container.xml file that tells readers where to find the OPF file.

    This is a required file in every EPUB that must be located at META-INF/container.xml.
    It's the entry point that e-readers use to locate the main package document (OPF).

    Returns:
        XML string for the container.xml file

    Note:
        This follows the EPUB specification exactly and should not be modified.
    """
    container_data = """<?xml version="1.0" encoding="UTF-8" ?>\n"""
    container_data += """<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n"""
    container_data += """<rootfiles>\n"""
    container_data += """<rootfile full-path="OPS/package.opf" media-type="application/oebps-package+xml"/>\n"""
    container_data += """</rootfiles>\n</container>"""
    return container_data


def get_coverpage_XML(title, authors):
    """
    Generate a professional cover page in XHTML format for the EPUB.

    Creates a clean, readable cover page that works well across different
    e-readers and screen sizes. The design is responsive and uses web-safe
    fonts for maximum compatibility.

    Args:
        title: Book title to display prominently
        authors: Author name(s) to display below the title

    Returns:
        XHTML string for the cover page

    Design Features:
        - Responsive layout that works on various screen sizes
        - Professional typography with proper hierarchy
        - Centered design with elegant spacing
        - Cross-platform font compatibility
    """
    return f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<title>Cover Page</title>
<style type="text/css">
/* Cover page styling optimized for e-readers */
body {{ 
    margin: 0;
    padding: 0;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: serif;  /* Better readability for books */
    background-color: #fafafa;
}}

.cover {{
    padding: 3em;
    text-align: center;
    border: 1px solid #ccc;
    max-width: 80%;
    background-color: white;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}

/* Main title styling */
h1 {{
    font-size: 2em;
    margin-bottom: 1em;
    line-height: 1.2;
    color: #333;
    font-weight: bold;
}}

/* Author styling */
p {{
    font-size: 1.2em;
    font-style: italic;
    color: #666;
    line-height: 1.4;
    margin-top: 2em;
}}
</style>
</head>
<body>
    <div class="cover">
        <h1>{title}</h1>
        <p>{authors}</p>
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
        toc_xhtml += (
            """<link rel="stylesheet" href="css/{}" type="text/css"/>\n""".format(
                css_filename
            )
        )

    toc_xhtml += """</head>\n<body>\n"""
    toc_xhtml += """<nav epub:type="toc" role="doc-toc" id="toc">\n<h2>Contents</h2>\n<ol epub:type="list">"""
    for i, md_filename in enumerate(markdown_filenames):
        toc_xhtml += """<li><a href="s{:05d}-{}.xhtml">{}</a></li>""".format(
            i, md_filename.split(".")[0], md_filename.split(".")[0]
        )
    toc_xhtml += """</ol>\n</nav>\n</body>\n</html>"""

    return toc_xhtml


def get_TOCNCX_XML(markdown_filenames):
    ## Returns the XML data for the TOC.ncx file

    toc_ncx = """<?xml version="1.0" encoding="UTF-8"?>\n"""
    toc_ncx += """<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" xml:lang="fr" version="2005-1">\n"""
    toc_ncx += """<head>\n</head>\n"""
    toc_ncx += """<navMap>\n"""
    for i, md_filename in enumerate(markdown_filenames):
        toc_ncx += """<navPoint id="navpoint-{}">\n""".format(i)
        toc_ncx += """<navLabel>\n<text>{}</text>\n</navLabel>""".format(
            md_filename.split(".")[0]
        )
        toc_ncx += """<content src="s{:05d}-{}.xhtml"/>""".format(
            i, md_filename.split(".")[0]
        )
        toc_ncx += """ </navPoint>"""
    toc_ncx += """</navMap>\n</ncx>"""

    return toc_ncx


def get_chapter_XML(
    work_dir: str,
    md_filename: str,
    css_filenames: list[str],
    content: Optional[str] = None,
) -> tuple[str, list[str]]:
    """
    Convert markdown chapter to XHTML and process images.
    Returns tuple of (XHTML content, list of images referenced in chapter)

    Args:
        work_dir: Working directory containing markdown files
        md_filename: Name of markdown file
        css_filenames: List of CSS files to include
        content: Optional pre-loaded markdown content. If None, content is read from file
    """
    work_dir_path = Path(work_dir)

    if content is None:
        with open(work_dir_path / md_filename, "r", encoding="utf-8") as f:
            markdown_data = f.read()
    else:
        markdown_data = content

    # Process markdown for images and get list of referenced images
    markdown_data, chapter_images = process_markdown_for_images(
        markdown_data, work_dir_path
    )

    # Convert to HTML
    html_text = markdown.markdown(
        markdown_data,
        extensions=["codehilite", "tables", "fenced_code", "footnotes"],
        extension_configs={"codehilite": {"guess_lang": False}},
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


def convert_to_epub(
    markdown_dir: Path, output_path: Path, batch_mode: bool = False
) -> None:
    """
    Convert markdown files and images to EPUB format.

    Args:
        markdown_dir: Directory containing markdown files and images
        output_path: Directory where EPUB file will be created
        batch_mode: If True, run without interactive prompts
    """
    if not markdown_dir.exists():
        raise FileNotFoundError(f"Markdown directory not found: {markdown_dir}")

    if not list(markdown_dir.glob("*.md")):
        raise ValueError(f"No markdown files found in: {markdown_dir}")

    # Set up mark2epub's working directory
    work_dir = str(markdown_dir)

    # Generate EPUB file
    epub_path = markdown_dir / f"{markdown_dir.name}.epub"
    main([str(markdown_dir), str(epub_path)], batch_mode=batch_mode)


def main(args, batch_mode: bool = False):
    if len(args) < 2:
        print("\nUsage:\n    python md2epub.py <markdown_directory> <output_file.epub>")
        exit(1)

    work_dir = args[0]
    output_path = args[1]

    images_dir = os.path.join(work_dir, "images/")
    css_dir = os.path.join(work_dir, "css/")

    try:
        # Reading/Creating the JSON file containing the description of the eBook
        description_path = os.path.join(work_dir, "description.json")
        existing_metadata = {}

        if os.path.exists(description_path):
            with open(description_path, "r", encoding="utf-8") as f:
                existing_metadata = json.load(f)

        # Get metadata from user
        json_data = get_metadata_from_user(existing_metadata, batch_mode=batch_mode)

        # Find all markdown files if not already in metadata
        if not json_data["chapters"]:
            markdown_files = [f for f in os.listdir(work_dir) if f.endswith(".md")]
            for md_file in sorted(markdown_files):
                json_data["chapters"].append({"markdown": md_file, "css": ""})

        # Save the updated description.json
        with open(description_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        # Review markdown files and store updated content
        chapter_contents = {}
        for chapter in json_data["chapters"]:
            md_path = Path(work_dir) / chapter["markdown"]
            should_continue, content = review_markdown(md_path, batch_mode=batch_mode)
            if not should_continue:
                print("\nConversion aborted by user.")
                return
            chapter_contents[chapter["markdown"]] = content

        # Get title and author
        title = json_data["metadata"].get("dc:title", "Untitled Document")
        authors = json_data["metadata"].get("dc:creator", None)

        # Compile list of files
        all_md_filenames = []
        all_css_filenames = json_data["default_css"][:]
        for chapter in json_data["chapters"]:
            if chapter["markdown"] not in all_md_filenames:
                all_md_filenames.append(chapter["markdown"])
            if len(chapter["css"]) and (chapter["css"] not in all_css_filenames):
                all_css_filenames.append(chapter["css"])

        all_image_filenames = get_all_filenames(
            images_dir, extensions=["gif", "jpg", "jpeg", "png"]
        )

        # First process all chapters and images
        images_dir = Path(work_dir) / "images"
        epub_images_dir = Path(work_dir) / "epub_images"
        processed_images = {}  # Store processed image data
        all_referenced_images = set()
        chapter_data = {}  # Store processed chapter data

        # First pass: Process chapters and collect image references
        print("\nProcessing chapters and collecting image references...")
        for i, chapter in enumerate(json_data["chapters"]):
            css_files = json_data["default_css"][:]
            if chapter["css"]:
                css_files.append(chapter["css"])

            # Process chapter content
            chapter_xhtml, chapter_images = get_chapter_XML(
                work_dir,
                chapter["markdown"],
                css_files,
                content=chapter_contents[chapter["markdown"]],
            )
            chapter_data[chapter["markdown"]] = chapter_xhtml
            all_referenced_images.update(chapter_images)

        # Process and optimize images
        print("\nProcessing and optimizing images...")
        if images_dir.exists() and all_referenced_images:
            epub_images_dir.mkdir(exist_ok=True)

            for image in all_referenced_images:
                src_path = images_dir / image
                if src_path.exists():
                    try:
                        dest_path = epub_images_dir / image
                        copy_and_optimize_image(src_path, dest_path)

                        # Store processed image data
                        with open(dest_path, "rb") as f:
                            processed_images[image] = f.read()
                    except Exception as e:
                        print(f"Warning: Failed to process image {image}: {e}")
                else:
                    print(f"Warning: Referenced image not found: {src_path}")

            # Cleanup temporary directory
            import shutil

            shutil.rmtree(epub_images_dir, ignore_errors=True)

        # Now create the EPUB file with all prepared content
        print("\nCreating EPUB file...")
        with zipfile.ZipFile(output_path, "w") as epub:
            # Write mimetype (must be first and uncompressed)
            epub.writestr("mimetype", "application/epub+zip")

            # Write container.xml
            epub.writestr(
                "META-INF/container.xml", get_container_XML(), zipfile.ZIP_DEFLATED
            )

            # Write package.opf
            epub.writestr(
                "OPS/package.opf",
                get_packageOPF_XML(
                    md_filenames=all_md_filenames,
                    image_filenames=all_image_filenames,
                    css_filenames=all_css_filenames,
                    description_data=json_data,
                ),
                zipfile.ZIP_DEFLATED,
            )

            # Write cover page
            coverpage_data = get_coverpage_XML(title, authors)
            epub.writestr(
                "OPS/titlepage.xhtml",
                coverpage_data.encode("utf-8"),
                zipfile.ZIP_DEFLATED,
            )

            # Write processed chapters
            print("Writing chapters...")
            for i, chapter in enumerate(json_data["chapters"]):
                print(
                    f"  Writing chapter {i+1}/{len(json_data['chapters'])}: {chapter['markdown']}"
                )
                epub.writestr(
                    f"OPS/s{i:05d}-{chapter['markdown'].split('.')[0]}.xhtml",
                    chapter_data[chapter["markdown"]].encode("utf-8"),
                    zipfile.ZIP_DEFLATED,
                )

            # Write processed images
            if processed_images:
                print(f"Writing {len(processed_images)} processed images...")
                for image_name, image_data in processed_images.items():
                    epub.writestr(
                        f"OPS/images/{image_name}", image_data, zipfile.ZIP_DEFLATED
                    )

            # Write TOC files
            print("Writing table of contents...")
            epub.writestr(
                "OPS/TOC.xhtml",
                get_TOC_XML(json_data["default_css"], all_md_filenames),
                zipfile.ZIP_DEFLATED,
            )

            epub.writestr(
                "OPS/toc.ncx", get_TOCNCX_XML(all_md_filenames), zipfile.ZIP_DEFLATED
            )

            # Copy remaining images that weren't referenced in markdown
            remaining_images = set(all_image_filenames) - set(processed_images.keys())
            if remaining_images and os.path.exists(images_dir):
                print(f"Writing {len(remaining_images)} additional images...")
                for image in remaining_images:
                    with open(os.path.join(images_dir, image), "rb") as f:
                        epub.writestr(
                            f"OPS/images/{image}", f.read(), zipfile.ZIP_DEFLATED
                        )

            # Copy CSS files
            if os.path.exists(css_dir):
                print(f"Writing {len(all_css_filenames)} CSS files...")
                for css in all_css_filenames:
                    css_path = os.path.join(css_dir, css)
                    if os.path.exists(css_path):
                        with open(css_path, "rb") as f:
                            epub.writestr(
                                f"OPS/css/{css}", f.read(), zipfile.ZIP_DEFLATED
                            )

        print(f"\nEPUB creation complete: {output_path}")

    except Exception as e:
        import traceback

        print(f"Error processing {work_dir}:")
        print(traceback.format_exc())
        raise


if __name__ == "__main__":
    main(sys.argv[1:], batch_mode=False)
