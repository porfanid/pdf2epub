# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release preparation
- Comprehensive documentation improvements

## [0.1.0] - 2024-08-08

### Added
- **Package Structure**: Transformed repository into a distributable Python package
- **CLI Interface**: Added `pdf2epub` command-line tool with comprehensive options
- **Public API**: Clean, importable API for library usage
- **Dependency Management**: Conditional dependencies with graceful fallbacks
- **Testing Suite**: 41 comprehensive tests with 100% pass rate and 49% code coverage
- **CI/CD Pipeline**: GitHub Actions workflow for automated testing across Python 3.9-3.12
- **Plugin Architecture**: Extensible AI postprocessing system with Anthropic Claude support
- **Documentation**: Comprehensive code documentation and inline comments
- **Quality Assurance**: Black formatting, flake8 linting, and mypy type checking

### Features
- **PDF to Markdown Conversion**: Intelligent layout detection for books and academic papers
- **EPUB Generation**: High-quality EPUB 3.0 output with customizable styling
- **AI Postprocessing**: Optional AI-powered text enhancement and correction
- **Multi-language Support**: Process documents in multiple languages
- **GPU Acceleration**: Support for NVIDIA CUDA and AMD ROCm
- **Image Processing**: Extract and optimize images during conversion
- **Table Detection**: Preserve table structure in output
- **Equation Support**: Convert mathematical equations to LaTeX

### Technical
- **Python 3.9+** compatibility
- **Core Dependencies**: Only `markdown>=3.7` for basic installation
- **Optional Dependencies**: Heavy ML dependencies only when needed
- **Installation Options**: Basic, full, and development installation modes
- **Environment Variables**: Configuration via environment variables
- **Error Handling**: Graceful degradation when optional dependencies missing

### Package Distribution
- **PyPI Ready**: Builds wheel and source distributions
- **Entry Points**: CLI command properly configured
- **Metadata**: Complete package metadata in pyproject.toml
- **License**: MIT License for open-source use

### Backwards Compatibility
- **Zero Breaking Changes**: All existing functionality preserved
- **Legacy Support**: Original `main.py` script still functional
- **API Compatibility**: New API extends rather than replaces existing functions

[Unreleased]: https://github.com/porfanid/pdf2epub/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/porfanid/pdf2epub/releases/tag/v0.1.0