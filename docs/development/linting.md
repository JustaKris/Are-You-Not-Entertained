# Linting Guide

Code quality checks and linting for the TV-HML project using Ruff and other tools.

## Quick Start

```powershell
# Run all linting checks
uv run ruff check src/ tests/

# Auto-fix issues where possible
uv run ruff check --fix src/ tests/

# Type checking
uv run mypy src/ tests/ --ignore-missing-imports

# Security scan
uv run bandit -r src/
```

## Ruff Linter

Ruff is an extremely fast Python linter written in Rust, combining the functionality of multiple tools.

### Basic Usage

```powershell
# Lint all source code
uv run ruff check src/

# Lint specific files
uv run ruff check src/tv_hml/config/schema.py

# Show detailed output
uv run ruff check src/ --output-format=full

# Auto-fix safe issues
uv run ruff check --fix src/ tests/
```

### What Ruff Checks

Ruff implements rules from multiple linters:

- **pycodestyle (E, W)** - PEP 8 style violations
- **pyflakes (F)** - Logical errors and undefined names
- **isort (I)** - Import sorting
- **pydocstyle (D)** - Docstring conventions
- **pylint (PL)** - Advanced code analysis
- **And many more** - See [Ruff rules](https://docs.astral.sh/ruff/rules/)

### Configuration

Settings in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
]
ignore = [
    "E501",  # Line too long (handled by formatter)
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["D"]  # Don't require docstrings in tests
```

## Type Checking with Mypy

Static type checking catches bugs before runtime.

### Mypy Usage

```powershell
# Type check source code
uv run mypy src/

# Include tests
uv run mypy src/ tests/

# Ignore missing imports
uv run mypy src/ --ignore-missing-imports

# Show error codes
uv run mypy src/ --show-error-codes
```

### Mypy Configuration

Settings in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### Type Hint Guidelines

Always use type hints for function signatures:

```python
# Good
def process_data(year: int, month: int) -> pd.DataFrame:
    """Process data for period."""
    pass

# Bad
def process_data(year, month):
    """Process data for period."""
    pass
```

Use `typing` module for complex types:

```python
from typing import Optional, List, Dict, Tuple
from pathlib import Path

def load_files(
    directory: Path,
    patterns: List[str],
    limit: Optional[int] = None
) -> Dict[str, pd.DataFrame]:
    """Load files matching patterns."""
    pass
```

## Security Scanning with Bandit

Bandit finds common security issues in Python code.

### Bandit Usage

```powershell
# Scan source code
uv run bandit -r src/

# Exclude test files
uv run bandit -r src/ -x tests/

# Show only high severity
uv run bandit -r src/ -ll

# Generate detailed report
uv run bandit -r src/ -f html -o reports/security.html
```

### Bandit Configuration

Settings in `pyproject.toml`:

```toml
[tool.bandit]
exclude_dirs = ["tests", "scripts"]
skips = [
    "B101",  # assert_used (OK in tests)
]
```

### Common Security Issues

**Hardcoded passwords:**

```python
# Bad
password = "hardcoded_value"

# Good
password = os.environ.get("DB_PASSWORD")
```

**SQL injection:**

```python
# Bad
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

## Import Sorting

Ruff handles import sorting automatically.

### Manual Import Sorting

```powershell
# Sort imports with Ruff
uv run ruff check --select I --fix src/ tests/
```

### Import Order

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import pandas as pd
import numpy as np
from pydantic import BaseModel

# Local
from tv_hml.config.schema import Settings
from tv_hml.utils.calendar import get_days_in_month
```

## Running All Checks

### Individual Commands

```powershell
# Lint with Ruff
uv run ruff check src/ tests/

# Format check
uv run ruff format --check src/ tests/

# Type check
uv run mypy src/ tests/ --ignore-missing-imports

# Security scan
uv run bandit -r src/
```

### Combined Script

Create `lint.ps1`:

```powershell
# Run all linting checks
Write-Host "Running Ruff linter..." -ForegroundColor Cyan
uv run ruff check src/ tests/
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`nRunning type checker..." -ForegroundColor Cyan
uv run mypy src/ tests/ --ignore-missing-imports
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`nRunning security scanner..." -ForegroundColor Cyan
uv run bandit -r src/ -ll
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`nAll checks passed!" -ForegroundColor Green
```

## CI/CD Integration

Linting runs automatically in GitLab CI:

```yaml
lint:
  stage: quality
  script:
    - uv run ruff check src/ tests/
    - uv run mypy src/ tests/ --ignore-missing-imports
    - uv run bandit -r src/
  allow_failure: false
```

See [CI/CD Documentation](ci-cd.md) for complete pipeline.

## IDE Integration

### VS Code

Install extensions:

- **Ruff** (charliermarsh.ruff)
- **Pylance** (ms-python.vscode-pylance)

Settings in `.vscode/settings.json`:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "ruff.lint.enable": true,
  "ruff.format.enable": true,
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true
}
```

### PyCharm

1. Install Ruff plugin from marketplace
2. Enable Mypy in Settings → Tools → Python Integrated Tools
3. Configure to run on save

## Common Issues

### Ruff Not Found

```powershell
# Install dev dependencies
uv sync

# Verify installation
uv run ruff --version
```

### Type Errors with Third-Party Libraries

```powershell
# Install type stubs
uv pip install types-boto3
uv pip install pandas-stubs

# Or ignore missing imports
uv run mypy src/ --ignore-missing-imports
```

### Import Order Conflicts

```powershell
# Let Ruff fix automatically
uv run ruff check --select I --fix src/
```

## Pre-commit Hooks

Automatically lint before commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

Install hooks:

```powershell
uv run pre-commit install
```

## Best Practices

1. **Lint early and often** - Run checks before committing
2. **Fix issues immediately** - Don't accumulate technical debt
3. **Use auto-fix** - Let tools handle simple fixes
4. **Understand warnings** - Don't blindly ignore issues
5. **Configure appropriately** - Adjust rules for your project
6. **Integrate with IDE** - Get real-time feedback

## Related Documentation

- **[Testing Guide](testing.md)** - Test practices and coverage
- **[Formatting Guide](formatting.md)** - Code formatting standards
- **[Security Guide](security.md)** - Security scanning and best practices
- **[Code Style](code-style.md)** - General style guidelines
- **[CI/CD Pipeline](ci-cd.md)** - Automated quality checks

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [PEP 8 Style Guide](https://pep8.org/)
