# Security Policy

## Supported Versions

We actively support and provide security updates for the following versions of PDF2EPUB:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

The PDF2EPUB team takes security issues seriously. We appreciate your efforts to responsibly disclose your findings, and will make every effort to acknowledge your contributions.

### How to Report Security Issues

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **Email**: Send details to the repository owner (contact information available on GitHub profile)
2. **GitHub Security Advisories**: Use the "Security" tab in the repository to report privately
3. **Private Issue**: Contact maintainers directly before public disclosure

### What to Include

When reporting a security vulnerability, please include:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact and attack scenarios
- **Reproduction**: Step-by-step instructions to reproduce the issue
- **Environment**: Python version, operating system, package version
- **Proof of Concept**: If possible, a minimal example demonstrating the issue

### Response Timeline

- **Initial Response**: Within 48 hours of receiving the report
- **Status Update**: Within 1 week with preliminary assessment
- **Resolution**: Security fixes prioritized and released as soon as possible

### Security Considerations

#### Dependencies

PDF2EPUB relies on several external dependencies:

- **marker-pdf**: PDF processing engine
- **transformers**: AI/ML models and tokenizers
- **anthropic**: AI API client
- **torch**: Machine learning framework
- **pillow**: Image processing

We monitor these dependencies for security vulnerabilities and update them promptly when security patches are available.

#### AI/API Security

When using AI postprocessing features:

- **API Keys**: Store API keys securely using environment variables
- **Data Privacy**: Be aware that document content may be sent to AI providers
- **Rate Limiting**: API calls are subject to provider rate limits
- **Error Handling**: AI providers may return unexpected responses

#### File Processing Security

PDF processing involves:

- **File Validation**: Input files are validated before processing
- **Resource Limits**: Processing limits prevent resource exhaustion
- **Temporary Files**: Temporary files are cleaned up after processing
- **Path Traversal**: Output paths are sanitized to prevent directory traversal

### Best Practices for Users

1. **Keep Updated**: Always use the latest version with security patches
2. **Validate Inputs**: Only process trusted PDF files
3. **Secure API Keys**: Use environment variables, never hardcode keys
4. **Monitor Usage**: Review AI provider usage and billing
5. **Isolate Processing**: Consider running in containers or isolated environments

### Security Updates

Security updates will be:

- Released as patch versions (e.g., 0.1.1)
- Documented in the changelog with security advisories
- Announced through GitHub security advisories
- Tagged with appropriate CVE identifiers when applicable

### Responsible Disclosure

We request that you:

- Give us reasonable time to fix the issue before public disclosure
- Avoid accessing or modifying user data beyond what's necessary to demonstrate the vulnerability
- Avoid degrading the service for other users
- Only test against your own systems or with explicit permission

### Security Hall of Fame

We maintain a list of security researchers who have helped improve PDF2EPUB security:

*No security issues have been reported yet.*

### Contact

For security-related questions or concerns that are not vulnerabilities:

- Open a GitHub issue with the "security" label
- Review our security practices in the codebase
- Contribute security improvements via pull requests

---

**Thank you for helping keep PDF2EPUB and our users safe!**