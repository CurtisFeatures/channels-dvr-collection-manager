# Contributing to Channels DVR Collection Manager

Thank you for considering contributing to this project! 

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected behavior**
- **Screenshots** if applicable
- **Environment details**:
  - Docker version
  - Channels DVR version
  - Browser (if web interface issue)
  - OS (if relevant)
- **Logs** from `docker logs channels-collection-manager`

### Suggesting Features

Feature requests are welcome! Please provide:

- **Clear use case** - What problem does this solve?
- **Proposed solution** - How should it work?
- **Alternatives considered** - What other approaches did you think about?

### Pull Requests

1. Fork the repo and create your branch from `main`
2. Make your changes
3. Test your changes thoroughly
4. Update documentation if needed
5. Follow the existing code style
6. Write clear commit messages
7. Submit a pull request

#### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/channels-collection-manager.git
cd channels-collection-manager

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DVR_URL=http://your-dvr:8089
export SYNC_INTERVAL_MINUTES=60

# Run the app
python app/main.py
```

#### Code Style

- Python: Follow PEP 8
- JavaScript: Use consistent indentation and naming
- HTML/CSS: Keep it clean and organized
- Comments: Explain "why", not "what"

#### Testing

Before submitting:

1. Test with your Channels DVR setup
2. Test with different pattern types
3. Test sorting options
4. Verify Docker build works: `docker build -t test .`
5. Check for console errors in browser

### Documentation

Help improve documentation:

- Fix typos or unclear explanations
- Add examples for common use cases
- Improve installation instructions
- Create video tutorials or screenshots

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

### Our Responsibilities

Project maintainers are responsible for clarifying standards and taking appropriate action in response to any behavior that is not aligned with these standards.

## Questions?

Feel free to:
- Open an issue with the "question" label
- Start a discussion in GitHub Discussions
- Ask in the Channels DVR Community Forum

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
