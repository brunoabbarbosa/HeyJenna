# Contributing to HeyJenna

Thank you for your interest in contributing to HeyJenna! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.10.14 (recommended)
- FFmpeg installed and in PATH
- Git

### Setup Development Environment

1. **Fork and clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/HeyJenna.git
cd HeyJenna
```

2. **Create a virtual environment**
```bash
python3.10 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp env.example .env
# Edit .env file with your preferred settings
```

5. **Run the application**
```bash
python heyjenna.py
```

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small

### Testing

Before submitting a pull request:

1. **Test the feature** thoroughly
2. **Test on different platforms** (Windows, Linux, macOS)
3. **Test with different video sources** (YouTube, TikTok, etc.)
4. **Check for memory leaks** with large files
5. **Verify error handling** works correctly

### File Structure

- Keep the existing file structure
- Add new templates to `templates/` directory
- Add new static files to `static/` directory
- Update `requirements.txt` if adding new dependencies

## Common Development Tasks

### Adding a New Platform

1. **Update platform detection** in `heyjenna.py`
2. **Add cookie file mapping** in `config.py`
3. **Test with sample URLs**
4. **Update documentation**

### Adding a New Feature

1. **Create a feature branch**
2. **Implement the feature**
3. **Add tests if applicable**
4. **Update documentation**
5. **Test thoroughly**

### Bug Fixes

1. **Reproduce the bug**
2. **Identify the root cause**
3. **Fix the issue**
4. **Test the fix**
5. **Add regression tests if needed**

## Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes**
3. **Test thoroughly**
4. **Update documentation** if needed
5. **Submit a pull request**

### Pull Request Guidelines

- **Clear title** describing the change
- **Detailed description** of what was changed and why
- **Screenshots** for UI changes
- **Test instructions** for reviewers
- **Link to related issues** if applicable

## Code Review

All contributions require code review. Reviewers will check:

- **Code quality** and style
- **Functionality** and edge cases
- **Security** implications
- **Performance** impact
- **Documentation** updates

## Reporting Issues

When reporting issues:

1. **Use the issue template**
2. **Provide detailed steps** to reproduce
3. **Include system information** (OS, Python version, etc.)
4. **Add error messages** and logs
5. **Include sample URLs** if relevant

## Getting Help

- **Check existing issues** for similar problems
- **Search documentation** for solutions
- **Ask in discussions** for general questions
- **Create an issue** for bugs or feature requests

## License

By contributing to HeyJenna, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to HeyJenna! 🚀