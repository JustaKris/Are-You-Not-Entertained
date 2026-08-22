# Pre-commit Hooks Setup Guide

## Overview

This project uses [pre-commit](https://pre-commit.com/) for fast, deterministic checks before every commit. The hook is a convenience layer; GitHub Actions remains authoritative for tests, type checking, security scans, and documentation checks.

## What Are Pre-commit Hooks?

Pre-commit hooks are automated checks that run before you commit code. They:

- **Catch simple mistakes early**: Validate files and detect secrets before they enter the repository
- **Keep Python consistent**: Run Ruff linting and formatting on changed Python files
- **Stay quick**: Leave slower checks to CI, where they run in a clean environment

## Installation

### First-Time Setup

```powershell
# 1. Sync the development dependencies (includes pre-commit)
uv sync --group dev

# 2. Install the git hooks
uv run pre-commit install

# 3. (Optional) Run on all files to test
uv run pre-commit run --all-files
```

### Verification

After installation, pre-commit will run automatically on every `git commit`. You'll see output like:

```
end of file fixer....................................Passed
check yaml..........................................Passed
ruff................................................Passed
ruff-format.........................................Passed
```

## Configured Hooks

The local hook configuration includes:

### File Checks

- **end-of-file-fixer**: Ensure tracked files end with a newline
- **check-toml**: Validate TOML syntax
- **check-yaml**: Validate YAML syntax
- **check-merge-conflict**: Detect merge conflict markers
- **detect-private-key**: Prevent committing private keys

### Python Checks

- **ruff**: Lint Python files and apply safe fixes
- **ruff-format**: Format Python files

The hooks do not rewrite line endings, YAML formatting, notebook outputs, or Markdown. Those changes should be deliberate and reviewable.

## What CI Handles

GitHub Actions runs the slower or broader checks in a clean environment:

- Full test suite on Python 3.12 and 3.13, with coverage and JUnit artifacts
- Mypy type checking on Python 3.12 and 3.13
- Bandit code scanning and an advisory pip-audit report
- Markdown linting and MkDocs documentation builds

Each workflow publishes a summary in the GitHub Actions job page. Security and Markdown reports are uploaded as artifacts when available.

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
uv run pre-commit run ruff-format --all-files
```

### Skip Hooks (Use Sparingly)

If you need to bypass hooks (not recommended):

```powershell
git commit --no-verify -m "Your message"
```

**Warning**: Skipping hooks means issues will be caught in CI/CD instead.

### Disable/Enable Hooks

If you need to temporarily or permanently disable pre-commit hooks:

**Disable hooks** (removes git hook):

```powershell
uv run pre-commit uninstall
```

After uninstalling, commits will proceed without running any hooks.

**Re-enable hooks** (reinstalls git hook):

```powershell
uv run pre-commit install
```

**Use cases for disabling:**

- Working on a large refactoring where you want to commit in stages
- Running formatters/linters manually before committing
- Troubleshooting hook issues
- Temporarily bypassing hooks during rapid iteration

**Note**: Even with hooks disabled, it's best practice to run formatters and linters manually before committing:

```powershell
# Run the same code checks locally
uv run ruff format src/ scripts/ tests/
uv run ruff check src/ scripts/ tests/

# Run the broader CI checks locally when needed
uv run mypy src/ scripts/ tests/ --ignore-missing-imports
uv run bandit -r src/ -c pyproject.toml
uv run pymarkdown scan docs/ README.md
```

## Common Issues

### Hook Fails on Commit

**Problem**: Pre-commit found issues in your code.

**Solution**:

1. Read the error message carefully
2. Fix the reported issues
3. Stage the fixes: `git add .`
4. Commit again

### Ruff Formatting Issues

**Problem**: Code doesn't match `ruff` style.

**Solution**:
```powershell
# Auto-fix most issues
uv run ruff check --fix src
uv run ruff format src
```

### Slow First Run

**Problem**: Hooks take a long time.

**Solution**:

- Pre-commit caches environments, first run is slower
- Run `pre-commit gc` to clean up old environments
- The first run downloads isolated hook environments; later runs reuse them

## Configuration

Pre-commit is configured in `.pre-commit-config.yaml`. You can:

### Update Hook Versions

```powershell
# Update all hooks to latest versions
uv run pre-commit autoupdate
```

### Disable Specific Hooks

Edit `.pre-commit-config.yaml` only when the local hook policy changes, then validate it with `uv run pre-commit validate-config`.

## Integration with VS Code

Pre-commit works alongside VS Code extensions:

1. **Pre-commit runs on git commit**: Catches fast, local issues before commit
2. **VS Code extensions run on save**: Immediate feedback while coding
3. **CI/CD runs on push**: Final verification

This layered approach keeps local feedback fast while CI provides the complete quality gate.

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

Pre-commit overlaps with the fast checks in GitHub Actions; the workflows also run broader checks:

| Hook | CI/CD Workflow |
| ------ | ---------------- |
| Ruff | `.github/workflows/ci.yml` |
| File checks | `.github/workflows/ci.yml` and `.github/workflows/docs.yml` |
| Mypy and pytest | `.github/workflows/ci.yml` |
| Bandit and pip-audit | `.github/workflows/security-audit.yml` |
| Markdown and docs | `.github/workflows/docs.yml` |

Running pre-commit locally catches common issues early, but it does not replace CI.

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
