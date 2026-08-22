# Code Quality

The project keeps Python style, static analysis, documentation checks, and the local
pre-commit workflow deliberately small and reproducible. The `pyproject.toml` file is
the source of truth for tool configuration; this page explains how to run the checks.

## Quick Start

Install the development dependency group:

```powershell
uv sync --group dev
```

Run the checks that match CI:

```powershell
uv run ruff format --check src/ scripts/ tests/
uv run ruff check src/ scripts/ tests/
uv run mypy
uv run pymarkdown scan docs/ README.md
uv run mkdocs build --strict
```

Run `uv run pre-commit install` once to run the fast file checks automatically before
commits.

## Python Style

Python code follows the project settings in `pyproject.toml`:

- Target Python 3.12 syntax and support Python 3.12 and 3.13.
- Use four spaces for indentation and a 100-character line length.
- Prefer double-quoted strings and trailing commas in multi-line structures.
- Use type hints on public function and method signatures.
- Use Google-style docstrings for public APIs and non-obvious behavior.
- Keep imports grouped as standard library, third-party, then local application imports.
- Use `snake_case` for functions and variables, `PascalCase` for classes, and
  `UPPER_SNAKE_CASE` for constants.

Favor small functions with one responsibility, explicit error handling, and names that
make the data flow easy to follow. Add comments only when they explain a decision that
the code itself cannot make clear.

## Ruff

[Ruff](https://docs.astral.sh/ruff/) handles both linting and formatting.

### Format Python

```powershell
# Check formatting without changing files
uv run ruff format --check src/ scripts/ tests/

# Format files locally
uv run ruff format src/ scripts/ tests/

# Preview formatter changes
uv run ruff format --diff src/ scripts/ tests/
```

### Lint Python

```powershell
# Check source, maintenance scripts, and tests
uv run ruff check src/ scripts/ tests/

# Apply safe lint fixes, including import sorting
uv run ruff check --fix src/ scripts/ tests/
```

Ruff covers pycodestyle, pyflakes, import sorting, bugbear, comprehensions,
docstrings, naming, simplification, upgrade rules, and Ruff-specific checks. Formatting
and linting are separate commands so a check never changes files unexpectedly.

## Mypy

[Mypy](https://mypy.readthedocs.io/) checks the paths configured in `pyproject.toml`:
`src`, `scripts`, and `tests`.

```powershell
# Use the repository configuration
uv run mypy

# Check a narrower path while developing
uv run mypy src/ayne/core
```

The project currently uses gradual typing. Missing type information from third-party
packages is ignored, but errors in the project code should be addressed rather than
silenced. Add a targeted ignore only when the limitation is understood.

## Documentation Checks

Documentation has two checks in `.github/workflows/docs.yml`:

```powershell
# Check Markdown syntax and style
uv run pymarkdown scan docs/ README.md

# Build the site and treat warnings as errors
uv run mkdocs build --strict
```

Markdown line length is intentionally not enforced because documentation contains code,
tables, and URLs. Code fences require a language, and Markdown blocks must be separated
by blank lines. MkDocs also checks that pages listed in `mkdocs.yml` and their internal
links resolve.

## Pre-commit

Pre-commit provides quick feedback on changed files:

```powershell
uv run pre-commit install
uv run pre-commit run
uv run pre-commit run --all-files
```

The configured hooks validate file endings, TOML and YAML syntax, merge-conflict
markers, private keys, Ruff lint fixes, and Ruff formatting. The full test suite, mypy,
Bandit, pip-audit, and the documentation build remain CI checks. See the
[pre-commit guide](../guides/pre-commit-guide.md) for troubleshooting and hook details.

## CI Checks

GitHub Actions runs the same checks in clean environments:

| Workflow | Responsibility |
| --- | --- |
| `CI / Python` | Ruff linting and formatting, mypy, tests, and coverage artifacts |
| `Docs / Build` | Markdown linting and strict MkDocs build |
| `Security / Audit` | Bandit and advisory pip-audit report |

For a local pre-merge check, run the commands in [Quick Start](#quick-start), then run
the security commands in the [Security Guide](security.md).

## Related Documentation

- [Testing](testing.md) - pytest, coverage, fixtures, and test scope
- [Security](security.md) - Bandit, pip-audit, and secret handling
- [Logging](logging.md) - application logging conventions
- [Pre-commit Guide](../guides/pre-commit-guide.md) - hook setup and troubleshooting
