# Contributing to Digi-Me

We welcome contributions to the Digi-Me Digital Clone Framework! This document provides guidelines for contributing.

## Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/digi-me.git
   cd digi-me
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install black flake8 mypy pytest pytest-asyncio
   ```

## Code Style

- Use [Black](https://black.readthedocs.io/) for code formatting
- Follow [PEP 8](https://pep8.org/) style guidelines
- Add type hints where possible
- Write docstrings for all public functions and classes

## Testing

- Write tests for new functionality
- Ensure all tests pass before submitting a PR
- Run tests with: `pytest`

## Pull Request Process

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes and commit them:
   ```bash
   git commit -m "Add your feature description"
   ```
3. Push to your fork and submit a pull request
4. Ensure your PR description clearly describes the problem and solution

## Areas for Contribution

- **New Platform Integrations**: Teams, Slack, Discord, etc.
- **LLM Provider Support**: OpenAI, Claude, local models
- **Plugin Development**: MCP-compatible plugins
- **Testing**: Unit tests, integration tests
- **Documentation**: Tutorials, API docs, examples
- **Performance**: Optimization and monitoring

## Questions?

Feel free to open an issue for questions or join our Discord community.
