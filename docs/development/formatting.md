# Formatting Guide

Code formatting standards for the TV-HML project using Ruff and pre-commit hooks.

## Quick Start

```powershell
# Format all code
uv run ruff format src/ tests/

# Check formatting without changes
uv run ruff format --check src/ tests/

# Format specific files
uv run ruff format src/tv_hml/config/schema.py
```

## Ruff Formatter

Ruff's formatter is compatible with Black but much faster.

### Basic Usage

```powershell
# Format source code
uv run ruff format src/

# Format tests
uv run ruff format tests/

# Format everything
uv run ruff format src/ tests/

# Check without modifying
uv run ruff format --check src/ tests/

# Show what would change
uv run ruff format --diff src/
```

### Configuration

Settings in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
indent-width = 4
target-version = "py311"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

## Formatting Rules

### Line Length

Maximum 88 characters (Black default):

```python
# Good
result = some_function(
    first_argument,
    second_argument,
    third_argument,
)

# Bad (too long)
result = some_function(first_argument, second_argument, third_argument, fourth_argument)
```

### String Quotes

Use double quotes:

```python
# Good
name = "John Doe"
message = "Hello, world!"

# Bad
name = 'John Doe'
message = 'Hello, world!'
```

Exception: Use single quotes to avoid escaping:

```python
# Good
message = 'He said "Hello"'

# Acceptable but unnecessary
message = "He said \"Hello\""
```

### Indentation

4 spaces (no tabs):

```python
# Good
def example():
    if True:
        print("Indented with 4 spaces")

# Bad
def example():
  if True:
    print("Inconsistent indentation")
```

### Trailing Commas

Use trailing commas in multi-line structures:

```python
# Good
items = [
    "apple",
    "banana",
    "cherry",
]

# Also acceptable
items = ["apple", "banana", "cherry"]

# Bad (multi-line without trailing comma)
items = [
    "apple",
    "banana",
    "cherry"
]
```

### Blank Lines

- 2 blank lines between top-level definitions
- 1 blank line between methods in a class
- 1 blank line between logical sections in functions

```python
# Good
import os
import sys


class MyClass:
    """Example class."""

    def __init__(self):
        """Initialize."""
        self.value = 0

    def method_one(self):
        """First method."""
        pass

    def method_two(self):
        """Second method."""
        pass


def standalone_function():
    """Standalone function."""
    pass
```

### Line Breaks

Break lines at logical boundaries:

```python
# Good - break at logical groupings
result = my_function(
    first_group_arg1,
    first_group_arg2,
    second_group_arg1,
    second_group_arg2,
)

# Good - chain methods on separate lines
result = (
    df.filter(condition)
    .groupby("category")
    .agg({"value": "sum"})
    .reset_index()
)
```

## Formatting Specific Constructs

### Function Definitions

```python
# Short - single line
def simple_function(x: int, y: int) -> int:
    return x + y


# Long - break at parameters
def complex_function(
    first_parameter: str,
    second_parameter: int,
    third_parameter: Optional[bool] = None,
) -> Dict[str, Any]:
    """Complex function with many parameters."""
    pass
```

### Function Calls

```python
# Short - single line
result = calculate(10, 20, 30)

# Long - vertical alignment
result = calculate_complex_value(
    base_value=100,
    multiplier=1.5,
    adjustment_factor=0.95,
    include_tax=True,
)
```

### List/Dict Comprehensions

```python
# Short - single line
squares = [x ** 2 for x in range(10)]

# Long - break for readability
squares = [
    calculate_complex_value(x)
    for x in data
    if x.is_valid()
]

# Dictionary comprehension
mapping = {
    key: transform(value)
    for key, value in items
    if is_valid(key)
}
```

### Imports

```python
# Good - grouped and sorted
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np
from pydantic import BaseModel

from tv_hml.config.schema import Settings
from tv_hml.utils.calendar import get_days_in_month

# Bad - mixed order
from tv_hml.config.schema import Settings
import pandas as pd
import os
from pydantic import BaseModel
```

Use Ruff to auto-sort:

```powershell
uv run ruff check --select I --fix src/
```

### String Formatting

Prefer f-strings for readability:

```python
# Good - f-strings
message = f"Processing {year}-{month:02d}"
path = f"data/output/{year}-{month}/results.csv"

# Acceptable - format()
message = "Processing {}-{:02d}".format(year, month)

# Avoid - % formatting
message = "Processing %d-%02d" % (year, month)
```

## IDE Integration

### VS Code

Install Ruff extension and configure:

`.vscode/settings.json`:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "ruff.format.args": ["--line-length", "88"],
  "editor.rulers": [88]
}
```

### PyCharm

1. Install Ruff plugin from marketplace
2. Enable in Settings → Tools → Ruff
3. Configure format on save:
   - Settings → Tools → Actions on Save
   - Enable "Reformat code"

### Neovim/Vim

Use `null-ls` or `conform.nvim`:

```lua
require("conform").setup({
  formatters_by_ft = {
    python = { "ruff_format" },
  },
  format_on_save = {
    timeout_ms = 500,
    lsp_fallback = true,
  },
})
```

## Pre-commit Hooks

Automatically format code before commits.

### Setup

Install pre-commit:

```powershell
uv pip install pre-commit
uv run pre-commit install
```

Configuration in `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      # Run linter
      - id: ruff
        args: [--fix]
      
      # Run formatter
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### Usage

```powershell
# Run manually on all files
uv run pre-commit run --all-files

# Run on staged files (happens automatically on commit)
uv run pre-commit run

# Update hook versions
uv run pre-commit autoupdate
```

## CI/CD Integration

Format checking in GitLab CI:

```yaml
format-check:
  stage: quality
  script:
    - uv sync
    - uv run ruff format --check src/ tests/
  allow_failure: false
```

This ensures code is properly formatted before merging.

## Common Formatting Patterns

### Long Function Signatures

```python
# Break at each parameter
def process_television_data(
    year: int,
    month: int,
    input_directory: Path,
    output_directory: Path,
    weight_file: Optional[Path] = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """Process television viewing data."""
    pass
```

### Method Chaining

```python
# Each method on new line
result = (
    df.filter(pl.col("age") > 18)
    .groupby("region")
    .agg([
        pl.col("duration").sum().alias("total_duration"),
        pl.col("pnr").n_unique().alias("unique_panelists"),
    ])
    .sort("total_duration", descending=True)
)
```

### Complex Conditionals

```python
# Break at logical operators
if (
    year >= 2020
    and month in range(1, 13)
    and has_required_files
    and not is_legacy_mode
):
    process_data()

# Or use variables for clarity
is_valid_period = year >= 2020 and month in range(1, 13)
has_requirements = has_required_files and not is_legacy_mode

if is_valid_period and has_requirements:
    process_data()
```

### Type Hints

```python
# Long type hints
from typing import Dict, List, Optional, Union

def complex_function(
    data: Dict[str, List[int]],
    options: Optional[Dict[str, Union[str, int]]] = None,
) -> List[Dict[str, Any]]:
    """Complex function with detailed types."""
    pass

# Use TypeAlias for complex types
from typing import TypeAlias

PersonData: TypeAlias = Dict[str, Union[str, int, List[str]]]

def process_person(data: PersonData) -> PersonData:
    """Process person data."""
    pass
```

## Troubleshooting

### Formatter Not Running

```powershell
# Verify Ruff installed
uv run ruff --version

# Re-sync dependencies
uv sync

# Check for syntax errors first
uv run ruff check src/
```

### Conflicts with Linter

Formatter and linter should work together. If conflicts occur:

```powershell
# Run in correct order: lint then format
uv run ruff check --fix src/
uv run ruff format src/
```

### IDE Not Formatting

**VS Code:**

- Verify Ruff extension installed
- Check default formatter: `Ctrl+Shift+P` → "Format Document With..."
- Ensure `.vscode/settings.json` configured

**PyCharm:**

- Reinstall Ruff plugin
- Clear caches: File → Invalidate Caches
- Verify enabled in Settings

### Pre-commit Hook Fails

```powershell
# Update hooks
uv run pre-commit autoupdate

# Clear cache
uv run pre-commit clean

# Re-install
uv run pre-commit uninstall
uv run pre-commit install
```

## Checking Formatting

Before committing:

```powershell
# Check if formatting needed
uv run ruff format --check src/ tests/

# See what would change
uv run ruff format --diff src/ tests/

# Apply formatting
uv run ruff format src/ tests/
```

Exit codes:

- `0` - Already formatted correctly
- `1` - Would reformat files

## Best Practices

1. **Format early and often** - Don't accumulate formatting issues
2. **Use auto-format on save** - IDE integration makes it effortless
3. **Run pre-commit hooks** - Catch issues before pushing
4. **Don't fight the formatter** - Accept opinionated defaults
5. **Format before linting** - Formatting fixes some lint issues
6. **Keep configuration minimal** - Use defaults when possible

## Related Documentation

- **[Linting Guide](linting.md)** - Code quality checks
- **[Testing Guide](testing.md)** - Test practices and coverage
- **[Code Style](code-style.md)** - General style guidelines
- **[CI/CD Pipeline](ci-cd.md)** - Automated quality checks

## Resources

- [Ruff Formatter Documentation](https://docs.astral.sh/ruff/formatter/)
- [Black Documentation](https://black.readthedocs.io/) (compatible style)
- [PEP 8 Style Guide](https://pep8.org/)
- [Pre-commit Documentation](https://pre-commit.com/)
