# Installation Guide

## Requirements

- **Python 3.9 or higher**
- **Operating System**: Windows, macOS, or Linux
- **Memory**: At least 4GB RAM (8GB+ recommended for large PDFs)
- **Storage**: 2GB free space for dependencies and processing

## Installation Methods

### 1. PyPI Installation (Recommended)

#### Basic Installation
```bash
pip install pdf2epub
```

This installs the core package with minimal dependencies. Great for:
- Simple PDF to Markdown conversions
- When you have limited storage or bandwidth
- Container deployments with size constraints

#### Full Installation
```bash
pip install pdf2epub[full]
```

This includes all optional dependencies for:
- PDF processing with marker-pdf
- AI postprocessing with Anthropic Claude
- GPU acceleration support
- Advanced image processing

#### Development Installation
```bash
pip install pdf2epub[dev]
```

Includes development tools:
- Testing framework (pytest)
- Code formatting (black)
- Linting (flake8)
- Type checking (mypy)

### 2. From Source

#### For Users
```bash
git clone https://github.com/porfanid/pdf2epub.git
cd pdf2epub
pip install .
```

#### For Developers
```bash
git clone https://github.com/porfanid/pdf2epub.git
cd pdf2epub
pip install -e .[dev,full]
```

The `-e` flag installs in "editable" mode, so changes to the code take effect immediately.

## GPU Support

### NVIDIA GPUs (CUDA)

If you have an NVIDIA GPU, install PyTorch with CUDA support:

```bash
# Install PDF2EPUB first
pip install pdf2epub[full]

# Then upgrade PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### AMD GPUs (ROCm)

For AMD GPUs with ROCm support:

```bash
# Install PDF2EPUB first
pip install pdf2epub[full]

# Then install PyTorch with ROCm
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2
```

### Verify GPU Setup

```python
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU device: {torch.cuda.get_device_name(0)}")
```

## Virtual Environment Setup

### Using venv (Recommended)

```bash
# Create virtual environment
python -m venv pdf2epub-env

# Activate (Linux/Mac)
source pdf2epub-env/bin/activate

# Activate (Windows)
pdf2epub-env\Scripts\activate

# Install PDF2EPUB
pip install pdf2epub[full]
```

### Using conda

```bash
# Create environment
conda create -n pdf2epub python=3.11

# Activate environment
conda activate pdf2epub

# Install PDF2EPUB
pip install pdf2epub[full]
```

## Docker Installation

### Quick Start with Docker

```bash
# Pull and run
docker run --rm -v $(pwd):/workspace pdf2epub:latest document.pdf
```

### Build from Source

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install PDF2EPUB
RUN pip install pdf2epub[full]

WORKDIR /workspace
ENTRYPOINT ["pdf2epub"]
```

## Troubleshooting

### Common Issues

#### ImportError: marker-pdf not found
```bash
# Install full dependencies
pip install pdf2epub[full]
```

#### CUDA out of memory
```bash
# Use CPU-only mode
export CUDA_VISIBLE_DEVICES=""
```

#### Permission denied on Linux
```bash
# Install to user directory
pip install --user pdf2epub[full]
```

### System-Specific Issues

#### macOS ARM (M1/M2)
```bash
# Use conda for better ARM support
conda install -c conda-forge python=3.11
pip install pdf2epub[full]
```

#### Windows Long Path Issues
```bash
# Enable long paths in Windows
# Run as administrator:
# reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1
```

#### Linux Dependencies
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev build-essential

# CentOS/RHEL
sudo yum install python3-devel gcc
```

## Verification

Test your installation:

```bash
# Check installation
pdf2epub --help

# Verify dependencies
python -c "import pdf2epub; print('Installation successful!')"

# Test with a sample PDF
pdf2epub sample.pdf --skip-ai
```

## Upgrading

```bash
# Upgrade to latest version
pip install --upgrade pdf2epub

# Upgrade with all dependencies
pip install --upgrade pdf2epub[full]
```

## Uninstalling

```bash
# Remove PDF2EPUB
pip uninstall pdf2epub

# Remove all dependencies (if installed separately)
pip uninstall marker-pdf transformers anthropic torch pillow
```

## Next Steps

After installation:

1. **[Quick Tutorial](tutorial.md)** - Convert your first PDF
2. **[CLI Reference](cli.md)** - Learn command-line options
3. **[Configuration](guides/configuration.md)** - Set up API keys and preferences
4. **[Basic Usage](guides/basic-usage.md)** - Common workflows