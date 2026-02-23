# Contributing to keyof

Thank you for your interest in contributing to keyof! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We're all here to build something useful together.

## Getting Started

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/eyusd/keyof.git
   cd keyof
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev,test]"
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=keyof --cov-report=term-missing

# Run specific test file
pytest tests/test_keyof.py

# Run specific test
pytest tests/test_keyof.py::test_user_access_name
```

### Type Checking

```bash
mypy src/keyof
```

### Linting and Formatting

```bash
# Check for issues
ruff check src tests

# Fix auto-fixable issues
ruff check --fix src tests

# Format code
ruff format src tests
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run them manually:

```bash
pre-commit run --all-files
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(keyof): add to_url_path() serialization method
fix(keyof): handle None values in nested paths
docs: update README with new examples
```

### Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** with appropriate tests
3. **Ensure all checks pass**:
   - Tests: `pytest`
   - Type checking: `mypy src/keyof`
   - Linting: `ruff check src tests`
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated (for user-facing changes)
- [ ] Commit messages follow conventions

## Testing Guidelines

### Writing Tests

- Place tests in `tests/` directory
- Use descriptive test names: `test_<what>_<condition>_<expected>`
- Include docstrings for complex tests
- Test both success and failure cases
- Use fixtures for common test data

### Test Structure

```python
def test_feature_when_condition_then_expected():
    """Description of what this test verifies."""
    # Arrange
    path = KeyOf(lambda u: u.name)
    user = User(name="Alice")
    
    # Act
    result = path.from_(user)
    
    # Assert
    assert result == "Alice"
```

## Code Style

### General Guidelines

- Follow PEP 8
- Use type hints for all public APIs
- Write docstrings for public classes and methods
- Keep functions focused and small
- Prefer explicit over implicit

### Type Hints

```python
from typing import Any, TypeVar

T = TypeVar("T")

def example(value: str, items: list[int]) -> dict[str, Any]:
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def from_(self, obj: T, default: Any = _MISSING) -> Any:
    """Retrieve the value at this path from obj.
    
    Args:
        obj: An instance of T to navigate.
        default: Value to return if path cannot be resolved.
    
    Returns:
        The value at the path, or default if provided.
    
    Raises:
        AttributeError: If path cannot be resolved and no default provided.
    """
```

## Releasing (Maintainers)

1. Update version in `src/keyof/keyof.py` and `pyproject.toml`
2. Update `CHANGELOG.md` with release date
3. Create a git tag: `git tag vX.Y.Z`
4. Push tag: `git push origin vX.Y.Z`
5. GitHub Actions will publish to PyPI

## Questions?

Feel free to open an issue for questions or discussion!
