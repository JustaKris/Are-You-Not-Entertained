# Linting Guide

Code quality checks and linting for the Are You Not Entertained (AYNE) project using Ruff and other tools.

## Quick Start

```powershell
# Run all linting checks
uv run ruff check src/ scripts/ tests/

# Auto-fix issues where possible
uv run ruff check --fix src/ scripts/ tests/

# Type checking
uv run mypy

# Security scan
uv run bandit -r src/ -c pyproject.toml
```

## Ruff Linter

Ruff is an extremely fast Python linter written in Rust, combining the functionality of multiple tools.

### Basic Usage

```powershell
# Lint all source code
uv run ruff check src/

# Lint specific files
uv run ruff check src/ayne/core/config/settings.py

# Show detailed output
uv run ruff check src/ --output-format=full

# Auto-fix safe issues
uv run ruff check --fix src/ scripts/ tests/
```

### What Ruff Checks

Ruff implements rules from multiple linters:

- **pycodestyle (E, W)** - PEP 8 style violations
- **pyflakes (F)** - Logical errors and undefined names
- **isort (I)** - Import sorting
- **pydocstyle (D)** - Docstring conventions
- **Ruff-specific (RUF)** - Ruff-specific checks
- **And many more** - See [Ruff rules](https://docs.astral.sh/ruff/rules/)

### Configuration

Settings in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "D", "UP", "N", "SIM", "RUF"]
ignore = [
    "E501",   # Line too long (handled by formatter)
    "B008",   # Function call in argument defaults
    "D203",   # 1 blank line before class (conflicts with D211)
    "D213",   # Multi-line docstring summary second line
]

[tool.ruff.lint.pydocstyle]
convention = "google"
```

## Type Checking with Mypy

Static type checking catches bugs before runtime.

### Mypy Usage

```powershell
# Type check source code
uv run mypy src/

# The repository file list is configured in pyproject.toml
uv run mypy

# Show error codes
uv run mypy src/ --show-error-codes
```

### Mypy Configuration

Settings in `pyproject.toml`:

```toml
[tool.mypy]
files = ["src", "scripts", "tests"]
python_version = "3.12"
warn_return_any = false
warn_unused_configs = true
disallow_untyped_defs = false
disallow_incomplete_defs = false
check_untyped_defs = false
no_implicit_optional = false
strict_optional = false
ignore_missing_imports = true
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
uv run bandit -r src/ -c pyproject.toml

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
exclude_dirs = [
  ".venv",
  "venv",
  "tests",
  "scripts",
  "notebooks",
]
skips = ["B101", "B104", "B108", "B110", "B608"]
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
uv run ruff check --select I --fix src/ scripts/ tests/
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
from ayne.core.config.settings import Settings
from ayne.utils.query_utils import load_full_dataset
```

## Running All Checks

### Individual Commands

```powershell
# Lint with Ruff
uv run ruff check src/ scripts/ tests/

# Format check
uv run ruff format --check src/ scripts/ tests/

# Type check
uv run mypy

# Security scan
uv run bandit -r src/ -c pyproject.toml
```

### Combined Script

Create `lint.ps1`:

```powershell
# Run all linting checks
Write-Host "Running Ruff linter..." -ForegroundColor Cyan
uv run ruff check src/ scripts/ tests/
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`nRunning type checker..." -ForegroundColor Cyan
uv run mypy
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`nRunning security scanner..." -ForegroundColor Cyan
uv run bandit -r src/ -c pyproject.toml
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`nAll checks passed!" -ForegroundColor Green
```

## CI/CD Integration

Linting runs automatically in GitHub Actions:

```yaml
- name: Run ruff linting
  run: |
    uv run ruff check src/ scripts/ tests/

- name: Run type checking
  run: |
    uv run mypy

- name: Run security scan
  run: |
    uv run bandit -r src/ -c pyproject.toml
```

  See `.github/workflows/ci.yml` and `.github/workflows/security-audit.yml` for complete workflows.

## IDE Integration

### VS Code

Install extensions:

- **Ruff** (charliermarsh.ruff)
- **Pylance** (ms-python.vscode-pylance)

Settings in `.vscode/settings.json`:

```json
{
  "ruff.nativeServer": "on",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  }
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
uv sync --group dev

# Verify installation
uv run ruff --version
```

### Type Errors with Third-Party Libraries

```powershell
# Install type stubs
uv pip install types-boto3
uv pip install pandas-stubs

# Missing third-party stubs are ignored by the repository mypy configuration.
uv run mypy
```

### Import Order Conflicts

```powershell
# Let Ruff fix automatically
uv run ruff check --select I --fix src/ scripts/ tests/
```

## Pre-commit Hooks

The local hook runs Ruff plus a few fast repository checks before commits. CI runs mypy, Bandit, and the full test suite:

```powershell
uv sync --group dev
uv run pre-commit install
uv run pre-commit run --all-files
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
- **GitHub Actions Workflows** - See `.github/workflows/` for automated quality checks

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [PEP 8 Style Guide](https://pep8.org/)
