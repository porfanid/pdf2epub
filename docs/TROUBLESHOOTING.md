# PDF2EPUB Troubleshooting Guide

This guide helps resolve common issues when converting PDF files to EPUB format.

## Error: KeyError 'encoder'

**Symptoms:**
- Error occurs after models load successfully
- Message shows: `Error converting <filename>.pdf: 'encoder'`

**Common Causes:**
1. Model version incompatibility between marker-pdf and dependencies
2. Incomplete or corrupted model download from HuggingFace
3. Network interruption during initial model download
4. Insufficient disk space for model cache

**Solutions:**

### Quick Fix
```bash
# Clear model cache and retry
python3 main.py --clear-cache
python3 main.py your_file.pdf
```

### Manual Steps
```bash
# 1. Clear HuggingFace cache
rm -rf ~/.cache/huggingface/

# 2. Reinstall marker-pdf
pip uninstall marker-pdf
pip install marker-pdf==0.3.10

# 3. Retry conversion
python3 main.py your_file.pdf
```

### Check Disk Space
```bash
# Ensure you have at least 5GB free space
df -h ~/.cache
```

## Memory Issues

**Symptoms:**
- "CUDA out of memory" errors
- "RuntimeError: out of memory" 
- System becomes unresponsive

**Solutions:**
```bash
# Reduce memory usage
python3 main.py your_file.pdf --batch-multiplier 1

# Process fewer pages at once
python3 main.py your_file.pdf --max-pages 10

# Use CPU only (if GPU memory is limited)
# This is automatic if CUDA is not available
```

## Network Connection Issues

**Symptoms:**
- "Failed to connect to huggingface.co"
- "Connection timeout" errors
- "Network unreachable" messages

**Solutions:**
1. Check internet connection
2. Models need to download on first run (2-5GB)
3. Try again when connection is stable
4. Use offline mode after initial download

## GPU/CUDA Issues

**Symptoms:**
- CUDA driver errors
- "No CUDA-capable device found"
- GPU memory allocation errors

**Solutions:**
```bash
# Check CUDA availability
python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# The tool automatically falls back to CPU if CUDA is unavailable
# CPU processing is slower but functional
```

## File Access Issues

**Symptoms:**
- "Permission denied" errors
- "File not found" errors
- "Cannot read PDF" messages

**Solutions:**
```bash
# Check file permissions
ls -la your_file.pdf

# Ensure file is not corrupted
file your_file.pdf

# Try with a different PDF file
```

## Getting Help

If issues persist:

1. **Enable detailed logging:**
   ```bash
   python3 main.py your_file.pdf --skip-ai --max-pages 1
   ```

2. **Check system requirements:**
   - Python 3.9+
   - 4GB+ RAM
   - 5GB+ free disk space
   - Internet connection (first run)

3. **Report bugs:**
   - Include the full error message
   - Mention your OS and Python version
   - Describe the PDF file (size, pages, source)

4. **Alternative approach:**
   ```bash
   # Skip problematic components
   python3 main.py your_file.pdf --skip-ai --max-pages 5
   ```

## Prevention

- Keep internet connection stable during first run
- Ensure adequate disk space before processing large PDFs
- Process large files in smaller chunks using `--max-pages`
- Regular cleanup: `python3 main.py --clear-cache` if issues persist