# Contributing to HeyJenna

Thank you for your interest in contributing to HeyJenna! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/HeyJenna.git
   cd HeyJenna
   ```
3. **Set up the development environment** following the README.md instructions
4. **Create a new branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

1. **Install Python 3.10.14** (required version)
2. **Create a virtual environment**:
   ```bash
   python3.10 -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Install FFmpeg** for your operating system
5. **Copy environment configuration**:
   ```bash
   cp .env.example .env
   ```

## Making Changes

### Code Style
- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small

### Testing
- Test your changes thoroughly
- Ensure the application starts without errors
- Test with different video platforms if applicable
- Verify transcription and translation features work

### Commit Messages
Use clear, descriptive commit messages:
```
Add support for new video platform
Fix transcription error handling
Update README with installation instructions
```

## Types of Contributions

### Bug Reports
When reporting bugs, please include:
- Python version and operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Error messages or logs
- Video URLs that cause issues (if applicable)

### Feature Requests
For new features, please:
- Describe the feature and its use case
- Explain why it would be valuable
- Consider implementation complexity
- Check if similar features already exist

### Code Contributions
We welcome contributions for:
- Bug fixes
- New platform support
- UI/UX improvements
- Performance optimizations
- Documentation improvements
- Test coverage

## Platform Support

When adding support for new platforms:
1. Update `SUPPORTED_PLATFORMS` in `config.py`
2. Add platform name mapping in `PLATFORM_NAMES`
3. Test download functionality thoroughly
4. Update documentation

## Pull Request Process

1. **Update documentation** if needed
2. **Test your changes** thoroughly
3. **Create a pull request** with:
   - Clear title and description
   - Reference any related issues
   - List of changes made
   - Screenshots for UI changes

4. **Respond to feedback** and make requested changes
5. **Ensure CI passes** (if applicable)

## Code Review

All contributions go through code review:
- Be open to feedback and suggestions
- Respond promptly to review comments
- Make requested changes in a timely manner
- Ask questions if feedback is unclear

## Getting Help

If you need help:
- Check existing issues and discussions
- Create a new issue with your question
- Be specific about what you're trying to achieve
- Include relevant code snippets or error messages

## License

By contributing to HeyJenna, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in the project documentation and release notes.

Thank you for helping make HeyJenna better! 🎉