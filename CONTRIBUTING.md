# Contributing to JobHunt Pro

Thank you for considering contributing to JobHunt Pro! 🎉

## Development Setup

```bash
git clone https://github.com/sam-salameh/jobhunt-pro.git
cd jobhunt-pro
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Running Tests

All PRs must pass the full test suite:

```bash
python -m pytest tests/ -q
# Expected: 403 passed, 0 failed
```

## Code Standards

- **Python**: Follow PEP 8. All new functions must have type hints and docstrings.
- **CSS**: Use CSS Logical Properties exclusively (`margin-inline-start` not `margin-left`).
- **Arabic Support**: All UI text must support RTL via `dir="auto"` on inputs.
- **Security**: Never commit secrets. Use environment variables via `.env`.

## Pull Request Process

1. Fork the repo and create a feature branch: `git checkout -b feature/your-feature`
2. Write tests for your changes
3. Ensure `pytest tests/ -q` passes with 0 failures
4. Submit PR with a clear description of what changed and why

## Reporting Bugs

Open an issue with:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Python version and OS
