# Contributing to PDF2EPUB

Thank you for your interest in contributing to PDF2EPUB! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)
- [Community](#community)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Basic understanding of PDF processing, Markdown, and EPUB formats

### Ways to Contribute

- **Bug Reports**: Report bugs using GitHub issues
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit bug fixes, new features, or improvements
- **Documentation**: Improve documentation, examples, or tutorials
- **Testing**: Add tests or improve test coverage
- **AI Plugins**: Develop new AI postprocessing providers

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/pdf2epub.git
   cd pdf2epub
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e .[dev,full]
   ```

4. **Verify Installation**
   ```bash
   pytest
   pdf2epub --help
   ```

## Making Changes

### Branching Strategy

- `main`: Stable production branch
- `develop`: Integration branch for new features
- `feature/*`: Feature development branches
- `bugfix/*`: Bug fix branches
- `hotfix/*`: Critical production fixes

### Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow the [code style guidelines](#code-style)
   - Add or update tests for your changes
   - Update documentation as needed

3. **Test Changes**
   ```bash
   pytest
   black .
   flake8 .
   mypy pdf2epub/
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/changes
   - `refactor:` for code refactoring
   - `style:` for formatting changes
   - `ci:` for CI/CD changes

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pdf2epub --cov-report=html

# Run specific test file
pytest tests/test_pdf2md.py

# Run specific test
pytest tests/test_pdf2md.py::test_convert_pdf_basic
```

### Test Types

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Mock Tests**: Test with external dependencies mocked

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Use descriptive test function names
- Include docstrings for complex tests
- Mock external dependencies appropriately
- Aim for high test coverage

### Test Guidelines

```python
def test_function_name_should_describe_expected_behavior():
    """Test that function handles specific scenario correctly."""
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result.expected_property == expected_value
```

## Code Style

### Python Style

- **Formatter**: Black (line length: 88)
- **Linter**: flake8
- **Type Checker**: mypy
- **Import Sorting**: isort (if used)

### Formatting Commands

```bash
# Format code
black .

# Check formatting
black --check .

# Lint code
flake8 .

# Type checking
mypy pdf2epub/
```

### Style Guidelines

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write clear, descriptive docstrings
- Keep functions focused and small
- Use meaningful variable and function names
- Add inline comments for complex logic

### Documentation Style

```python
def convert_pdf(
    pdf_path: str,
    output_dir: str,
    batch_multiplier: int = 2,
    max_pages: Optional[int] = None
) -> Dict[str, Any]:
    """Convert PDF file to markdown format.
    
    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory to save output files
        batch_multiplier: Memory/speed tradeoff multiplier
        max_pages: Maximum number of pages to process
        
    Returns:
        Dictionary containing conversion metadata and statistics
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If output directory is invalid
        
    Example:
        >>> result = convert_pdf("document.pdf", "output/")
        >>> print(result["pages_processed"])
    """
```

## Pull Request Process

### Before Submitting

1. **Run Tests**: Ensure all tests pass
2. **Check Style**: Run formatting and linting tools
3. **Update Documentation**: Update relevant documentation
4. **Add Tests**: Include tests for new functionality
5. **Check Coverage**: Ensure test coverage doesn't decrease

### PR Guidelines

1. **Clear Title**: Use descriptive title following conventional commits
2. **Detailed Description**: Explain what, why, and how
3. **Link Issues**: Reference related issues using `Fixes #123`
4. **Small Changes**: Keep PRs focused and manageable
5. **Documentation**: Include documentation updates

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: Maintainer reviews code and provides feedback
3. **Address Feedback**: Make requested changes
4. **Approval**: PR approved by maintainer
5. **Merge**: PR merged into appropriate branch

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

### Release Steps

1. **Update Version**: Update version in `pyproject.toml`
2. **Update Changelog**: Add release notes to `CHANGELOG.md`
3. **Create Tag**: Tag release with version number
4. **Build Package**: Build wheel and source distributions
5. **Upload to PyPI**: Publish to Python Package Index

## AI Plugin Development

### Creating a New AI Provider

1. **Implement Interface**
   ```python
   class CustomAIProvider:
       @staticmethod
       def getjsonparams(system_prompt: str, request: str) -> str:
           # Implement your AI API call
           return json_response
   ```

2. **Register Provider**
   - Add to provider registry
   - Include configuration options
   - Add documentation

3. **Test Integration**
   - Add unit tests
   - Test with sample documents
   - Verify error handling

### Plugin Guidelines

- Follow existing provider patterns
- Handle API errors gracefully
- Support configuration via environment variables
- Include comprehensive documentation
- Add example usage

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Requests**: Code contributions and reviews

### Getting Help

- Check existing issues and documentation first
- Provide clear, reproducible examples
- Include relevant system information
- Be respectful and patient

### Recognition

Contributors are recognized in:
- `AUTHORS.md` file
- Release notes
- GitHub contributors list

Thank you for contributing to PDF2EPUB! Your efforts help make this tool better for everyone.