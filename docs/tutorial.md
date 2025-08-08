# Quick Tutorial: Your First PDF Conversion

Convert your first PDF to EPUB format in just a few minutes!

## Prerequisites

Make sure you have PDF2EPUB installed:
```bash
pip install pdf2epub[full]
```

## Step 1: Prepare Your PDF

For this tutorial, you can use any PDF file. Good test files include:
- A research paper or article
- A chapter from an ebook
- A document with images and tables

Save your PDF as `test-document.pdf` in your working directory.

## Step 2: Basic Conversion

### Simple Conversion
```bash
pdf2epub test-document.pdf
```

This will:
1. Convert the PDF to Markdown format
2. Generate an EPUB file
3. Create an output directory with the same name as your PDF

### What Happens

```
test-document/
├── test-document.md          # Markdown output
├── test-document.epub        # EPUB ebook
├── test-document_metadata.json  # Conversion metadata
└── images/                   # Extracted images
    ├── image_1.png
    ├── image_2.jpg
    └── ...
```

## Step 3: Advanced Options

### Process Specific Pages
```bash
# Convert only pages 10-20
pdf2epub test-document.pdf --start-page 10 --max-pages 10
```

### Skip Certain Steps
```bash
# Generate only Markdown (no EPUB)
pdf2epub test-document.pdf --skip-epub

# Use existing Markdown to generate EPUB
pdf2epub test-document.pdf --skip-md
```

### Specify Languages
```bash
# For multilingual documents
pdf2epub test-document.pdf --langs "English,Spanish"
```

## Step 4: Using the Python API

### Basic Python Usage

```python
import pdf2epub

# Convert PDF to Markdown
pdf2epub.convert_pdf_to_markdown("test-document.pdf", "output/")

# Convert Markdown to EPUB
pdf2epub.convert_markdown_to_epub("output/", "final/")
```

### Advanced Python Usage

```python
from pathlib import Path
import pdf2epub

# Set up paths
pdf_path = Path("test-document.pdf")
output_dir = pdf2epub.get_default_output_dir(pdf_path)

# Convert with custom options
pdf2epub.convert_pdf(
    str(pdf_path),
    output_dir,
    batch_multiplier=3,    # Use more memory for speed
    max_pages=50,          # Limit pages
    langs="English"        # Specify language
)

# Generate EPUB
pdf2epub.convert_to_epub(output_dir, output_dir.parent)

print(f"Conversion complete! Files saved to: {output_dir}")
```

## Step 5: AI Enhancement (Optional)

### Set Up AI API

```bash
# Get your API key from https://console.anthropic.com
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Use AI Postprocessing

```bash
# Convert with AI enhancement
pdf2epub test-document.pdf
```

The AI will:
- Fix OCR errors
- Improve text formatting
- Enhance readability
- Correct grammatical issues

### Python API with AI

```python
import pdf2epub

# Convert PDF
output_dir = pdf2epub.convert_pdf_to_markdown("test-document.pdf", "output/")

# Apply AI postprocessing
processor = pdf2epub.AIPostprocessor(output_dir)
markdown_file = output_dir / "test-document.md"
processor.run_postprocessing(markdown_file, "anthropic")

# Generate final EPUB
pdf2epub.convert_to_epub(output_dir, "final/")
```

## Step 6: Batch Processing

### Convert Multiple PDFs

```bash
# Convert all PDFs in a directory
pdf2epub documents/
```

### Python Batch Processing

```python
import pdf2epub
from pathlib import Path

# Process all PDFs in a directory
input_dir = Path("documents/")
pdf_queue = pdf2epub.add_pdfs_to_queue(input_dir)

for pdf_path in pdf_queue:
    print(f"Processing: {pdf_path}")
    
    # Convert to markdown
    output_dir = pdf2epub.convert_pdf_to_markdown(str(pdf_path), "output/")
    
    # Generate EPUB
    pdf2epub.convert_to_epub(output_dir, "final/")
    
    print(f"✓ Completed: {pdf_path.name}")
```

## Common Options Reference

| Option | Description | Example |
|--------|-------------|---------|
| `--start-page N` | Start from page N | `--start-page 5` |
| `--max-pages N` | Process N pages max | `--max-pages 20` |
| `--langs "X,Y"` | Document languages | `--langs "English,French"` |
| `--skip-epub` | Skip EPUB generation | `--skip-epub` |
| `--skip-md` | Skip Markdown (use existing) | `--skip-md` |
| `--skip-ai` | Skip AI postprocessing | `--skip-ai` |
| `--batch-multiplier N` | Memory/speed tradeoff | `--batch-multiplier 4` |

## Quality Tips

### For Best Results

1. **Use high-quality PDFs**: Clear text and images convert better
2. **Specify languages**: Helps with text recognition accuracy
3. **Enable AI postprocessing**: Significantly improves output quality
4. **Use GPU acceleration**: Much faster for large documents
5. **Check output**: Review Markdown before generating EPUB

### When Things Go Wrong

```bash
# Increase memory allocation
pdf2epub document.pdf --batch-multiplier 1

# Process fewer pages at a time
pdf2epub document.pdf --max-pages 10

# Skip AI if it's causing issues
pdf2epub document.pdf --skip-ai

# Use CPU only
CUDA_VISIBLE_DEVICES="" pdf2epub document.pdf
```

## Next Steps

Now that you've completed your first conversion:

1. **[CLI Reference](cli.md)** - Learn all command-line options
2. **[API Reference](api.md)** - Explore the Python API
3. **[Advanced Features](guides/advanced-features.md)** - GPU acceleration, custom workflows
4. **[Configuration](guides/configuration.md)** - Set up preferences and API keys
5. **[Troubleshooting](guides/troubleshooting.md)** - Solve common issues

## Example Output

Here's what a successful conversion looks like:

```
$ pdf2epub research-paper.pdf

🔍 Processing PDF: research-paper.pdf
📄 Detected 25 pages
🖼️  Found 8 images
📝 Converting to Markdown...
✨ Applying AI postprocessing...
📚 Generating EPUB...
✅ Conversion complete!

Output files:
├── research-paper.md (125 KB)
├── research-paper.epub (2.1 MB)
└── images/ (8 files, 1.8 MB)

Conversion took 2 minutes 34 seconds
```

Congratulations! You've successfully converted your first PDF to EPUB format. 🎉