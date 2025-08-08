# PDF2EPUB - PDF to EPUB Converter

PDF2EPUB is a Python-based tool that converts PDF files to EPUB format through an intelligent markdown conversion pipeline. The tool uses marker-pdf for PDF text extraction, optional AI postprocessing, and custom EPUB generation.

**ALWAYS follow these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the information here.**

## Working Effectively

### Bootstrap and Dependencies
- **REQUIRED Python version**: Python 3.9+ (tested with Python 3.12.3)
- Install Python dependencies: `pip install -r requirements.txt` 
  - **TIMING**: Takes 3-4 minutes to complete. NEVER CANCEL. Set timeout to 300+ seconds.
  - **NETWORK DEPENDENCY**: Requires internet access to download packages and ML models
  - Dependencies include: marker-pdf, transformers, torch, anthropic, markdown, PIL
- PyTorch installation with CUDA/ROCm support (optional for GPU acceleration):
  - NVIDIA GPUs: `pip install torch torchvision torchaudio` 
  - AMD GPUs: `pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2`
- Verify GPU support: `python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"`

### Basic Usage and Validation
- **Primary command**: `python3 main.py [input_path] [output_path] [options]`
- **CRITICAL LIMITATION**: Requires internet access to download HuggingFace models on first run
  - If network access is limited, PDF processing will fail with connection errors
  - Error message: "We couldn't connect to 'https://huggingface.co' to load this file"
  - **WORKAROUND**: Test EPUB generation directly using existing markdown files
- Convert single PDF: `python3 main.py input.pdf`
- Convert directory: `python3 main.py input_directory/`
- **AI Processing**: Requires ANTHROPIC_API_KEY environment variable for AI postprocessing
  - Skip AI with: `--skip-ai` flag

### Validation Scenarios
**ALWAYS test these scenarios after making changes:**

1. **EPUB Generation from Markdown** (works offline):
   ```bash
   # Create test structure
   mkdir -p test_markdown/images test_markdown/css
   echo "# Test Document\n\nThis is a test." > test_markdown/test.md
   
   # Test conversion - takes ~10 seconds
   python3 -c "import modules.mark2epub as mark2epub; mark2epub.main(['test_markdown', 'test.epub'])"
   # Provide metadata when prompted (title, author, etc.)
   
   # Verify output
   file test.epub  # Should show "EPUB document"
   ```

2. **Full PDF Conversion** (requires network access):
   ```bash
   # Only test if network access is available
   python3 main.py sample.pdf --skip-ai
   # TIMING: Variable depending on PDF size and model downloads
   # First run: 5-15 minutes (downloads models)
   # Subsequent runs: 30 seconds to 5 minutes depending on PDF size
   ```

3. **Syntax and Import Validation**:
   ```bash
   # All modules should compile without errors - takes <5 seconds
   python3 -m py_compile main.py
   find modules -name "*.py" -exec python3 -m py_compile {} \;
   
   # Test core imports - takes <10 seconds
   python3 -c "import modules.mark2epub; import modules.pdf2md; print('Core modules imported successfully')"
   ```

### Code Quality and Linting
- **Install linting tools**: `pip install --user flake8 black`
- **Run linting**: `python3 -m flake8 main.py modules/ --max-line-length=100 --ignore=E203,W503`
  - **NOTE**: Current codebase has style violations but is functional
  - **TIMING**: Linting takes <5 seconds
- **Auto-format**: `python3 -m black main.py modules/` (optional)

## Architecture and Key Components

### Main Entry Point
- **File**: `main.py` - Command-line interface and workflow orchestration
- **Key functions**: PDF queue processing, argument parsing, error handling

### Core Modules
- **`modules/pdf2md.py`**: PDF to Markdown conversion using marker-pdf
  - Handles image extraction and metadata generation
  - **DEPENDENCY**: Requires HuggingFace model downloads (network access)
- **`modules/mark2epub.py`**: Markdown to EPUB conversion 
  - Interactive metadata collection
  - Image optimization and CSS handling
  - **WORKS OFFLINE**: No network dependencies
- **`modules/postprocessing/ai/`**: AI-powered markdown postprocessing
  - **DEPENDENCY**: Requires ANTHROPIC_API_KEY environment variable
  - Can be skipped with `--skip-ai` flag

### Directory Structure
```
pdf2epub/
├── main.py                    # Main CLI entry point
├── requirements.txt           # Python dependencies
├── modules/
│   ├── pdf2md.py             # PDF extraction module
│   ├── mark2epub.py          # EPUB generation module
│   └── postprocessing/       # AI postprocessing modules
├── docs/                     # Documentation
├── input/                    # Default input directory (auto-created)
└── test_markdown/            # Example markdown structure
    ├── test_document.md      # Markdown content
    ├── images/               # Image assets
    └── css/                  # Style sheets
```

### Output Structure
```
output_directory/
├── document_name/
│   ├── document_name.md         # Extracted markdown
│   ├── document_name.epub       # Generated EPUB
│   ├── document_name_metadata.json  # PDF metadata
│   └── images/                  # Extracted images
│       ├── image1.png
│       └── ...
```

## Command Reference

### Essential Commands
- **Help**: `python3 main.py --help`
- **Convert PDF**: `python3 main.py input.pdf`
- **Convert directory**: `python3 main.py input_dir/`
- **Skip AI processing**: `python3 main.py input.pdf --skip-ai`
- **Skip EPUB generation**: `python3 main.py input.pdf --skip-epub`
- **Process page range**: `python3 main.py book.pdf --start-page 10 --max-pages 50`
- **Multi-language**: `python3 main.py paper.pdf --langs "English,German"`

### Development Commands
- **Syntax check**: `python3 -m py_compile main.py`
- **Import test**: `python3 -c "import modules.mark2epub; print('Success')"`
- **Lint code**: `python3 -m flake8 main.py modules/ --max-line-length=100`
- **GPU check**: `python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"`

## Known Limitations and Workarounds

### Network Dependencies
- **Issue**: Requires internet access for HuggingFace model downloads
- **Symptoms**: "Failed to resolve 'huggingface.co'" errors
- **Workaround**: Test EPUB generation component independently using existing markdown files
- **Solution**: Run in environment with internet access for initial model downloads

### AI Processing
- **Issue**: Requires ANTHROPIC_API_KEY for AI postprocessing
- **Workaround**: Always use `--skip-ai` flag when API key is not available
- **Testing**: AI component can be imported but will fail without valid API key

### GPU Acceleration
- **Issue**: CUDA may not be available in some environments
- **Behavior**: Tool automatically falls back to CPU processing
- **Performance**: CPU processing is slower but functional

## Common Tasks

### Repository Files Quick Reference
```bash
# Main files
ls -la  # Shows: main.py, requirements.txt, modules/, docs/, README.md

# Module structure  
find modules -name "*.py"  # Shows all Python modules

# Test if dependencies are installed
python3 -c "import marker, transformers, markdown; print('Dependencies OK')"
```

### Troubleshooting Steps
1. **Import errors**: Verify `pip install -r requirements.txt` completed successfully
2. **Network errors**: Check internet connectivity or use offline components only
3. **GPU errors**: Verify PyTorch installation or use CPU-only mode
4. **EPUB errors**: Ensure markdown directory has required `images/` and `css/` subdirectories
5. **AI processing errors**: Check ANTHROPIC_API_KEY or use `--skip-ai` flag

## Testing and Validation Notes
- **EPUB generation**: Tested and working offline (~10 seconds)
- **PDF processing**: Requires network access (timing varies)
- **Code quality**: Functional but has linting violations  
- **Dependencies**: Install successfully with network access (~3-4 minutes)
- **Cross-platform**: Python 3.9+ compatible

**NEVER CANCEL long-running operations**. Model downloads and PDF processing may take 5-15 minutes on first run.