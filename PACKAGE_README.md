# PDF2EPUB Python Package

[![CI/CD Pipeline](https://github.com/porfanid/pdf2epub/actions/workflows/ci.yml/badge.svg)](https://github.com/porfanid/pdf2epub/actions/workflows/ci.yml)

A Python package for converting PDF files to EPUB format via Markdown with intelligent layout detection and AI-powered postprocessing.

## Installation

### Basic Installation
```bash
pip install pdf2epub
```

### Full Installation (with all dependencies)
```bash
pip install pdf2epub[full]
```

### Development Installation
```bash
git clone https://github.com/porfanid/pdf2epub.git
cd pdf2epub
pip install -e .[dev]
```

## Usage

### Command Line Interface

After installation, you can use the `pdf2epub` command:

```bash
# Convert a single PDF
pdf2epub document.pdf

# Convert all PDFs in a directory
pdf2epub input_directory/

# Advanced options
pdf2epub book.pdf --start-page 10 --max-pages 50 --langs "English,German"

# Skip EPUB generation (markdown only)
pdf2epub thesis.pdf --skip-epub

# Skip AI postprocessing
pdf2epub document.pdf --skip-ai
```

### Python API

#### Basic Usage

```python
import pdf2epub

# Convert PDF to Markdown
pdf2epub.convert_pdf_to_markdown("document.pdf", "output_directory")

# Convert Markdown to EPUB
pdf2epub.convert_markdown_to_epub("output_directory", "final_output")
```

#### Advanced Usage

```python
from pathlib import Path
import pdf2epub

# Get list of PDFs to process
input_dir = Path("./pdfs")
pdf_queue = pdf2epub.add_pdfs_to_queue(input_dir)

# Process each PDF with custom options
for pdf_path in pdf_queue:
    output_dir = pdf2epub.get_default_output_dir(pdf_path)
    
    # Convert with custom settings
    pdf2epub.convert_pdf(
        str(pdf_path),
        output_dir,
        batch_multiplier=3,  # Use more memory for speed
        max_pages=100,       # Limit pages
        langs="English"      # Specify language
    )
    
    # AI postprocessing
    processor = pdf2epub.AIPostprocessor(output_dir)
    markdown_file = output_dir / f"{pdf_path.stem}.md"
    processor.run_postprocessing(markdown_file, "anthropic")
    
    # Generate EPUB
    pdf2epub.convert_to_epub(output_dir, output_dir.parent)
```

### Plugin Development

The package supports custom AI postprocessing plugins:

```python
from pdf2epub.postprocessing.ai import AIPostprocessor

class CustomAIProvider:
    @staticmethod
    def getjsonparams(system_prompt: str, request: str) -> str:
        # Your custom AI implementation
        return json_response

# Register your provider
# (Implementation details in the plugin documentation)
```

## Dependencies

### Core Dependencies (always installed)
- `markdown>=3.7`

### Full Dependencies (install with `[full]`)
- `marker-pdf==0.3.10` - PDF processing
- `transformers==4.45.2` - AI text processing
- `anthropic==0.39.0` - Anthropic AI API
- `torch` - GPU acceleration
- `pillow` - Image processing
- `regex` - Advanced text processing

### Development Dependencies (install with `[dev]`)
- `pytest>=7.0` - Testing framework
- `pytest-cov>=4.0` - Coverage reporting
- `black>=23.0` - Code formatting
- `flake8>=6.0` - Linting
- `mypy>=1.0` - Type checking

## Configuration

### Environment Variables

```bash
# Required for AI postprocessing
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### GPU Support

The package automatically detects and uses GPU acceleration when available:

For NVIDIA GPUs:
```bash
pip install torch torchvision torchaudio
```

For AMD GPUs:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2
```

## API Reference

### Main Functions

#### `convert_pdf_to_markdown(pdf_path, output_dir, **kwargs)`
Convert a PDF file to Markdown format.

**Parameters:**
- `pdf_path` (str): Path to input PDF file
- `output_dir` (str): Directory to save markdown output
- `batch_multiplier` (int): Memory/speed tradeoff (default: 2)
- `max_pages` (int): Maximum pages to process
- `start_page` (int): Starting page number
- `langs` (str): Comma-separated language list

#### `convert_markdown_to_epub(markdown_dir, output_path)`
Convert Markdown files to EPUB format.

**Parameters:**
- `markdown_dir` (str): Directory containing markdown files
- `output_path` (str): Output directory for EPUB file

#### `AIPostprocessor(work_dir)`
AI-powered postprocessing for improving conversion quality.

**Parameters:**
- `work_dir` (Path): Working directory containing markdown files

**Methods:**
- `run_postprocessing(markdown_path, ai_provider)`: Process markdown with AI

### Utility Functions

#### `add_pdfs_to_queue(input_path)`
Get list of PDF files to process from a file or directory.

#### `get_default_output_dir(input_path)`
Generate default output directory for a PDF file.

#### `get_default_input_dir()`
Get default input directory (./input), creating if needed.

## Testing

Run tests with:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=pdf2epub --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests: `pytest`
5. Format code: `black .`
6. Lint code: `flake8 .`
7. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

### v0.1.0 (2024-08-08)
- Initial package release
- Core PDF to EPUB conversion functionality
- AI postprocessing support
- Command-line interface
- Comprehensive test suite
- CI/CD pipeline