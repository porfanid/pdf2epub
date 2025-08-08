# Test Document for PDF2EPUB

This is a simple test document to validate the PDF to EPUB conversion workflow.
It contains multiple chapters with various text elements.

## Chapter 1: Introduction

This is the first chapter of our test document. It demonstrates basic text extraction capabilities of the PDF2EPUB converter.

The converter should be able to:

- Extract text from PDF files
- Convert to markdown format
- Generate EPUB files
- Handle multiple pages

## Chapter 2: Technical Details

This document tests the conversion pipeline:

**PDF → Markdown → EPUB**

The process involves:

1. PDF text extraction using marker-pdf
2. Optional AI postprocessing
3. Markdown to EPUB conversion

### Code Example

```python
import marker
# Example code block
def convert_pdf():
    return "converted"
```

### List Example

- First item
- Second item
  - Nested item
  - Another nested item
- Third item

### Table Example

| Feature | Status | Notes |
|---------|--------|-------|
| PDF Reading | Working | Uses marker-pdf |
| Markdown Output | Working | Clean formatting |
| EPUB Generation | Working | With images |

This is the end of our test document.