# Code Style Guide

Python code style guidelines for the TV-HML project.

## Style Guidelines

### PEP 8 Compliance

Follow [PEP 8](https://pep8.org/) with these specifics:

- Line length: 88 characters (Black default)
- Indentation: 4 spaces
- Use double quotes for strings
- Trailing commas in multi-line structures

### Type Hints

Always use type hints:

```python
def process_data(year: int, month: int) -> pd.DataFrame:
    """Process data for given period."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """Short description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1.
        param2: Description of param2.
        
    Returns:
        Description of return value.
        
    Raises:
        ValueError: When param2 is negative.
    """
    pass
```

### Import Order

1. Standard library
2. Third-party packages
3. Local modules

Use `ruff check --select I --fix` to auto-sort imports.

### Naming Conventions

- **Classes**: PascalCase (`WeightProcessor`)
- **Functions**: snake_case (`process_weights`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- **Private**: Prefix with underscore (`_internal_method`)

## Tools & Automation

The TV-HML project uses modern Python tooling for code quality:

- **[Ruff](linting.md)** - Fast linting and code quality checks
- **[Ruff Formatter](formatting.md)** - Consistent code formatting
- **[Mypy](linting.md#type-checking-with-mypy)** - Static type checking
- **[pytest](testing.md)** - Testing framework with coverage
- **[Pre-commit](formatting.md#pre-commit-hooks)** - Automated checks before commits

See individual guides for detailed usage:

- **[Linting Guide](linting.md)** - Ruff, Mypy, Bandit
- **[Formatting Guide](formatting.md)** - Ruff formatter, pre-commit
- **[Testing Guide](testing.md)** - pytest, coverage, fixtures

## Formatting Tools

### Ruff

Ruff is used for both linting and formatting:

```powershell
# Lint code
uv run ruff check src/ tests/

# Auto-fix issues (including import sorting)
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/

# Check formatting without changes
uv run ruff format --check src/ tests/
```

For detailed usage and configuration, see:

- **[Linting Guide](linting.md)** - Complete linting documentation
- **[Formatting Guide](formatting.md)** - Code formatting standards

## Related Documentation

- **[Testing Guide](testing.md)** - Test practices and coverage
- **[Linting Guide](linting.md)** - Code quality checks
- **[Formatting Guide](formatting.md)** - Code formatting standards
- **[CI/CD Pipeline](ci-cd.md)** - Automated quality checks

## Pre-commit Hooks

Automatically run checks before commits:

```powershell
# Install hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

## Best Practices

1. **Keep functions small** - Single responsibility principle
2. **Use descriptive names** - Self-documenting code
3. **Avoid magic numbers** - Use named constants
4. **Handle errors explicitly** - Don't hide exceptions
5. **Write testable code** - Dependency injection
6. **Document complex logic** - Add inline comments
