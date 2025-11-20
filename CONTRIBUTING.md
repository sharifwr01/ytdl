# 🤝 Contributing to YouTube Telegram Bot

আমরা আপনার contributions স্বাগত জানাই! এই guide আপনাকে contribution process সম্পর্কে সাহায্য করবে।

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)

## 📜 Code of Conduct

### Our Pledge

আমরা একটি welcoming এবং inclusive environment তৈরি করতে প্রতিশ্রুতিবদ্ধ। সকল contributors কে সম্মান করুন এবং constructive feedback দিন।

### Our Standards

**✅ Positive Behavior:**
- সম্মানজনক এবং inclusive ভাষা ব্যবহার করুন
- ভিন্ন মতামত এবং অভিজ্ঞতাকে সম্মান করুন
- Constructive criticism gracefully accept করুন
- Community এর সর্বোত্তম স্বার্থে focus করুন

**❌ Unacceptable Behavior:**
- Harassment অথবা discriminatory comments
- Personal attacks
- Trolling অথবা insulting comments
- Inappropriate বা unwelcome attention

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Git
- Docker (optional)
- GitHub account

### Fork and Clone

1. **Fork the repository** GitHub এ
2. **Clone your fork:**
```bash
git clone https://github.com/YOUR_USERNAME/yt-telegram-bot.git
cd yt-telegram-bot
```

3. **Add upstream remote:**
```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/yt-telegram-bot.git
```

## 💻 Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt
```

### 3. Setup Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Start Development Services

```bash
# Using Docker
docker-compose up -d postgres redis

# Or use Makefile
make setup
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Run the Bot

```bash
python bot.py
```

## 🛠️ How to Contribute

### Types of Contributions

1. **🐛 Bug Fixes**
   - Fix bugs এবং issues
   - Tests যোগ করুন
   - Documentation update করুন

2. **✨ New Features**
   - নতুন functionality যোগ করুন
   - Comprehensive tests লিখুন
   - Documentation update করুন

3. **📚 Documentation**
   - README improve করুন
   - Code comments যোগ করুন
   - Tutorial লিখুন

4. **🧪 Tests**
   - Test coverage বাড়ান
   - Edge cases test করুন

5. **🎨 Design**
   - UI/UX improve করুন
   - Bot messages refine করুন

### Contribution Workflow

```
1. Create branch → 2. Make changes → 3. Test → 4. Commit → 5. Push → 6. Pull Request
```

## 📝 Coding Standards

### Python Style Guide

আমরা **PEP 8** follow করি:

```python
# ✅ Good
def download_video(url: str, quality: str = "720p") -> Path:
    """Download video from URL.
    
    Args:
        url: YouTube video URL
        quality: Video quality (default: 720p)
    
    Returns:
        Path to downloaded file
    """
    pass

# ❌ Bad
def downloadVideo(url,quality="720p"):
    pass
```

### Code Formatting

```bash
# Format code
black .
isort .

# Check formatting
black --check .
isort --check-only .
```

### Type Hints

Always use type hints:

```python
# ✅ Good
def process_url(url: str, user_id: int) -> Optional[Dict[str, Any]]:
    pass

# ❌ Bad
def process_url(url, user_id):
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_eta(bytes_downloaded: int, total_bytes: int, 
                  start_time: float) -> int:
    """Calculate estimated time remaining.
    
    Args:
        bytes_downloaded: Number of bytes downloaded
        total_bytes: Total file size in bytes
        start_time: Download start timestamp
    
    Returns:
        Estimated seconds remaining
        
    Raises:
        ValueError: If total_bytes is 0
    """
    pass
```

### Naming Conventions

```python
# Variables and functions: snake_case
user_count = 10
def get_user_stats(): pass

# Classes: PascalCase
class DownloadManager: pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 50

# Private: _leading_underscore
def _internal_function(): pass
```

## 🧪 Testing

### Writing Tests

```python
import pytest

class TestDownload:
    """Test download functionality"""
    
    @pytest.mark.asyncio
    async def test_valid_url(self):
        """Test downloading with valid URL"""
        result = await download_video(
            url="https://youtube.com/watch?v=test",
            quality="720p"
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_invalid_url(self):
        """Test downloading with invalid URL"""
        with pytest.raises(ValueError):
            await download_video(url="invalid")
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_download.py

# Specific test
pytest tests/test_download.py::TestDownload::test_valid_url

# Watch mode
ptw
```

### Test Coverage

- Aim for **80%+ coverage**
- Cover edge cases
- Test error handling
- Mock external services

## 🔄 Pull Request Process

### 1. Create Branch

```bash
# Feature
git checkout -b feature/add-playlist-support

# Bug fix
git checkout -b fix/download-error

# Documentation
git checkout -b docs/update-readme
```

### 2. Make Changes

- Follow coding standards
- Write tests
- Update documentation
- Keep commits atomic

### 3. Commit Messages

Use conventional commits:

```bash
# Format
<type>(<scope>): <subject>

# Examples
feat(download): add playlist support
fix(rate-limit): correct daily limit calculation
docs(readme): update installation instructions
test(download): add edge case tests
refactor(database): optimize query performance
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `style`: Formatting
- `chore`: Maintenance

### 4. Push Changes

```bash
git push origin feature/your-feature-name
```

### 5. Create Pull Request

**PR Title:** Clear and descriptive
```
feat: Add support for downloading playlists
```

**PR Description Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Changes Made
- Added playlist parsing
- Implemented batch downloads
- Updated tests

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots]

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests added/updated
```

### 6. Code Review

- Address review comments
- Update PR as needed
- Be responsive and professional

### 7. Merge

- Squash commits if needed
- Update changelog
- Close related issues

## 🐛 Bug Reports

### Before Reporting

1. Check existing issues
2. Try latest version
3. Collect debug information

### Bug Report Template

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen

**Actual behavior**
What actually happened

**Screenshots**
If applicable

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- Bot version: [e.g., 1.0.0]

**Logs**
```
Paste relevant logs here
```

**Additional context**
Any other relevant information
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution**
How you'd like this to work

**Describe alternatives**
Other solutions you've considered

**Additional context**
Mockups, examples, etc.

**Implementation ideas**
Technical approach (optional)
```

## 📖 Documentation

### Documentation Standards

- Clear and concise
- Include examples
- Keep up to date
- Use proper markdown

### Documentation Types

1. **Code Comments**
```python
# Explain WHY, not WHAT
# Good: Check if user exceeded daily limit
if downloads_today >= MAX_DOWNLOADS:
    
# Bad: Check if downloads_today is greater than MAX_DOWNLOADS
```

2. **API Documentation**
- All public functions documented
- Include parameters and return types
- Add usage examples

3. **User Documentation**
- Installation guide
- Usage examples
- Troubleshooting
- FAQ

## 🎯 Best Practices

### Git

```bash
# Keep your fork updated
git fetch upstream
git rebase upstream/main

# Create meaningful commits
git commit -m "feat(download): add retry mechanism for failed downloads"

# Use interactive rebase for cleanup
git rebase -i HEAD~3
```

### Code Quality

```python
# ✅ Good practices
- Use type hints
- Write docstrings
- Handle errors properly
- Log important events
- Keep functions small
- Follow DRY principle

# ❌ Avoid
- Magic numbers
- Global state
- Long functions (>50 lines)
- Nested callbacks
- Commented code
```

### Security

- Never commit secrets
- Use environment variables
- Sanitize user inputs
- Follow security best practices

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

## 📞 Getting Help

- **Discord:** [Join our server](https://discord.gg/example)
- **Issues:** [GitHub Issues](https://github.com/yourusername/yt-telegram-bot/issues)
- **Email:** dev@example.com

## 📚 Resources

- [Python Style Guide](https://pep8.org/)
- [Git Best Practices](https://git-scm.com/book)
- [Pytest Documentation](https://docs.pytest.org/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

**Thank you for contributing! 🎉**

Every contribution, no matter how small, makes a difference!