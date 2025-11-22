# Pre-commit Hooks Setup Guide

## Overview

This project uses [pre-commit](https://pre-commit.com/) to automatically run code quality checks before every commit. This ensures code consistency, catches errors early, and maintains high code quality standards.

## What Are Pre-commit Hooks?

Pre-commit hooks are automated checks that run before you commit code. They:

- **Prevent bad commits**: Catch issues before they enter the codebase
- **Enforce standards**: Automatically format code and check for errors
- **Save time**: Find problems immediately instead of in CI/CD
- **Improve quality**: Maintain consistent code style across the team

## Installation

### First-Time Setup

```powershell
# 1. Sync dependencies (includes pre-commit)
uv sync

# 2. Install the git hooks
uv run pre-commit install

# 3. (Optional) Run on all files to test
uv run pre-commit run --all-files
```

### Verification

After installation, pre-commit will run automatically on every `git commit`. You'll see output like:

```
trailing whitespace...................................Passed
end of file fixer....................................Passed
check yaml..........................................Passed
ruff.................................................Passed
mypy.................................................Passed
```

## Configured Hooks

Our pre-commit configuration includes:

### General File Checks

- **trailing-whitespace**: Remove trailing spaces (except in markdown)
- **end-of-file-fixer**: Ensure files end with a newline
- **check-yaml**: Validate YAML syntax
- **check-json**: Validate JSON syntax
- **check-toml**: Validate TOML syntax
- **check-added-large-files**: Prevent files >1MB from being committed
- **check-merge-conflict**: Detect merge conflict markers
- **detect-private-key**: Prevent committing private keys

### Python Checks

- **check-ast**: Validate Python syntax
- **check-builtin-literals**: Require literal syntax (e.g., `[]` not `list()`)
- **debug-statements**: Prevent debug statements like `breakpoint()`

### Linting and Formatting

- **ruff**: Fast Python linter (replaces flake8, isort, etc.)
- **ruff-format**: Python code formatter
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning

### Markdown and YAML

- **markdownlint**: Markdown file formatting
- **pretty-format-yaml**: YAML formatting

### Notebook Cleaning

- **nbstripout**: Remove notebook outputs before commit

### Security

- **detect-secrets**: Scan for accidentally committed secrets

## Usage

### Automatic (Recommended)

Pre-commit runs automatically when you commit:

```powershell
git add .
git commit -m "Your commit message"
# Hooks run automatically!
```

If a hook fails:

1. Fix the reported issues
2. Stage the fixes: `git add .`
3. Commit again: `git commit -m "Your message"`

### Manual Run

Run hooks manually on specific files:

```powershell
# Run on staged files
uv run pre-commit run

# Run on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff --all-files
uv run pre-commit run mypy --all-files
```

### Skip Hooks (Use Sparingly)

If you need to bypass hooks (not recommended):

```powershell
git commit --no-verify -m "Your message"
```

**Warning**: Skipping hooks means issues will be caught in CI/CD instead.

## Common Issues

### Hook Fails on Commit

**Problem**: Pre-commit found issues in your code.

**Solution**:

1. Read the error message carefully
2. Fix the reported issues
3. Stage the fixes: `git add .`
4. Commit again

### Mypy Type Errors

**Problem**: `mypy` reports type errors.

**Solution**:
```powershell
# Run mypy to see full output
uv run mypy src

# Fix type annotations
# Add type hints, use type: ignore if needed
```

### Ruff Formatting Issues

**Problem**: Code doesn't match `ruff` style.

**Solution**:
```powershell
# Auto-fix most issues
uv run ruff check --fix src
uv run ruff format src
```

### Large Files

**Problem**: Trying to commit files >1MB.

**Solution**:

- Add to `.gitignore` if it shouldn't be committed
- Use Git LFS for large files
- Or adjust the limit in `.pre-commit-config.yaml`

### Slow Hook Runs

**Problem**: Hooks take a long time.

**Solution**:

- Pre-commit caches environments, first run is slower
- Run `pre-commit gc` to clean up old environments
- Consider disabling heavy hooks locally (edit `.pre-commit-config.yaml`)

## Configuration

Pre-commit is configured in `.pre-commit-config.yaml`. You can:

### Update Hook Versions

```powershell
# Update all hooks to latest versions
uv run pre-commit autoupdate
```

### Disable Specific Hooks

Edit `.pre-commit-config.yaml` and comment out unwanted hooks:

```yaml
# - repo: https://github.com/pre-commit/mirrors-mypy
#   rev: v1.13.0
#   hooks:
#     - id: mypy
```

### Adjust Hook Settings

Example - change file size limit:

```yaml
- id: check-added-large-files
  args: ['--maxkb=2000']  # Change from 1000 to 2000
```

## Integration with VS Code

Pre-commit works alongside VS Code extensions:

1. **Pre-commit runs on git commit**: Catches everything before commit
2. **VS Code extensions run on save**: Immediate feedback while coding
3. **CI/CD runs on push**: Final verification

This multi-layered approach ensures code quality at every step.

## Best Practices

### DO

✅ Run `pre-commit run --all-files` after updating hooks
✅ Commit frequently with small changesets
✅ Fix issues as they arise (don't accumulate)
✅ Keep `.pre-commit-config.yaml` in sync with `pyproject.toml`
✅ Update hooks regularly: `pre-commit autoupdate`

### DON'T

❌ Skip hooks without good reason
❌ Commit large batches of changes
❌ Ignore type errors (fix or add `# type: ignore`)
❌ Commit debugging code
❌ Commit secrets or API keys

## CI/CD Integration

Pre-commit hooks match our GitHub Actions workflows:

| Hook | CI/CD Workflow |
|------|----------------|
| ruff | `.github/workflows/python-lint.yml` |
| mypy | `.github/workflows/python-typecheck.yml` |
| pytest | `.github/workflows/python-tests.yml` |
| bandit | `.github/workflows/python-security.yml` |
| markdownlint | `.github/workflows/markdown-lint.yml` |

Running pre-commit locally ensures CI/CD passes.

## Troubleshooting

### Hooks Not Running

```powershell
# Reinstall hooks
uv run pre-commit uninstall
uv run pre-commit install

# Verify installation
uv run pre-commit run --all-files
```

### Environment Issues

```powershell
# Clean pre-commit cache
uv run pre-commit clean
uv run pre-commit gc

# Reinstall environments
uv run pre-commit install --install-hooks
```

### Hook Version Conflicts

```powershell
# Update to latest versions
uv run pre-commit autoupdate

# Or manually edit .pre-commit-config.yaml
```

## Additional Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Quick Reference

```powershell
# Installation
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files

# Update hooks
uv run pre-commit autoupdate

# Clean cache
uv run pre-commit clean

# Uninstall
uv run pre-commit uninstall

# Skip hooks (not recommended)
git commit --no-verify
```

## Summary

Pre-commit hooks are a powerful tool for maintaining code quality. They:

1. **Catch issues early** - Before they enter the codebase
2. **Save time** - Automated checks instead of manual review
3. **Enforce standards** - Consistent code style across the team
4. **Integrate with CI/CD** - Match GitHub Actions workflows

Follow this guide to use pre-commit effectively in the AYNE project!
