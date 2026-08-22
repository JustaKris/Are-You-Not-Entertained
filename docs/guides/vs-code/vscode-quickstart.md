# VS Code Quickstart

This guide covers the recommended Windows setup for working on AYNE in VS Code. The
repository uses PowerShell for terminal examples, Ruff for Python formatting and
linting, and Pylance for language support.

## Open The Project

Open the repository folder in VS Code, then open an integrated PowerShell terminal from
the Terminal menu. From the repository root, synchronize the development environment:

```powershell
uv sync --group dev
```

## Install Recommended Extensions

VS Code can prompt you to install the extensions listed in `.vscode/extensions.json`.
The same extensions can be installed from PowerShell:

```powershell
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.debugpy
code --install-extension charliermarsh.ruff
code --install-extension DavidAnson.vscode-markdownlint
code --install-extension eamodio.gitlens
code --install-extension tamasfe.even-better-toml
```

## Select The Interpreter

1. Open the Command Palette with `Ctrl+Shift+P`.
2. Run **Python: Select Interpreter**.
3. Choose `.venv\Scripts\python.exe`.

The repository already sets this path in `.vscode/settings.json`. Reload the window if
the Python or Ruff extensions do not pick up the environment immediately.

## Run Project Checks

Use the integrated terminal for the same checks used by CI:

```powershell
uv run pytest
uv run ruff format --check src/ scripts/ tests/
uv run ruff check src/ scripts/ tests/
uv run mypy
uv run pymarkdown scan docs/ README.md
```

Use `uv run mkdocs build --strict` when you need to verify the complete documentation
site. The [Code Quality guide](../../development/code-quality.md) explains the checks
and their scope.

## Editor Shortcuts

| Action | Shortcut |
| --- | --- |
| Format document | `Alt+Shift+F` |
| Format selection | `Ctrl+K`, then `Ctrl+F` |
| Quick fix | `Ctrl+.` |
| Open terminal | Terminal menu |
| Command Palette | `Ctrl+Shift+P` |

Python files format with Ruff on save. Markdown files use the configured markdownlint
extension; the command-line `pymarkdown` check remains the authoritative documentation
validation.

## Troubleshooting

### Python or Pylance cannot find the package

Confirm that `.venv\Scripts\python.exe` is selected and run:

```powershell
uv sync --group dev
```

### Formatting does not run on save

Check that the Ruff extension is installed and that **Editor: Format On Save** is
enabled. Run Ruff directly to distinguish an editor issue from a project issue:

```powershell
uv run ruff format --check src/ scripts/ tests/
uv run ruff check src/ scripts/ tests/
```

### Markdown warnings do not match CI

The repository settings align the markdownlint extension with the project’s practical
rules. Run the authoritative check from the repository root:

```powershell
uv run pymarkdown scan docs/ README.md
```

## Related Documentation

- [VS Code Configuration](vscode-configuration.md) - Committed editor settings
- [Code Quality](../../development/code-quality.md) - Python and documentation checks
- [Testing](../../development/testing.md) - pytest and coverage
- [Pre-commit Guide](../pre-commit-guide.md) - Local commit hooks
