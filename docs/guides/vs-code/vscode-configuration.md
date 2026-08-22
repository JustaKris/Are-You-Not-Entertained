# VS Code Configuration

The repository includes shared VS Code settings and extension recommendations for
Windows development. The files are intentionally small: project-wide behavior belongs
in `pyproject.toml`, while `.vscode/settings.json` only configures editor integration.

## Shared Files

- `.vscode/settings.json` selects the project interpreter, enables Ruff on save, and
  configures editor behavior for Python, Markdown, JSON, and YAML.
- `.vscode/extensions.json` recommends Python, Pylance, Debugpy, Ruff, Markdownlint,
  GitLens, GitHub Copilot, and Even Better TOML.
- `pyproject.toml` remains the source of truth for Ruff, mypy, pytest, and pymarkdown.

## Python Settings

The committed settings select the repository virtual environment:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "ruff.nativeServer": "on",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true
    }
}
```

Ruff provides both formatting and linting for this project.

## Markdown Settings

The Markdown extension has practical editor overrides for line length, duplicate
headings, inline HTML, and similar documentation patterns. These settings affect editor
diagnostics only. Validate documentation from PowerShell with:

```powershell
uv run pymarkdown scan docs/ README.md
uv run mkdocs build --strict
```

## Recommended Workflow

1. Open the repository root in VS Code.
2. Select `.venv\Scripts\python.exe` if VS Code has not selected it automatically.
3. Make changes with format-on-save enabled.
4. Run the focused check while editing.
5. Run the complete checks before submitting a change:

```powershell
uv run ruff format --check src/ scripts/ tests/
uv run ruff check src/ scripts/ tests/
uv run mypy
uv run pytest
uv run pymarkdown scan docs/ README.md
uv run mkdocs build --strict
```

The [Code Quality guide](../../development/code-quality.md) describes each check and
the [Pre-commit Guide](../pre-commit-guide.md) covers automatic file checks.

## Troubleshooting

### The interpreter is missing

From the repository root, run:

```powershell
uv sync --group dev
```

Then run **Python: Select Interpreter** from the Command Palette and select
`.venv\Scripts\python.exe`.

### Settings are not updating

Run **Developer: Reload Window** from the Command Palette. If the issue persists, check
that the repository folder, rather than a parent folder, is the active workspace.

### A formatter or linter disagrees with CI

Check `pyproject.toml` and run the repository commands directly. Avoid adding personal
rules to the committed settings file unless they are useful for every contributor.

## Related Documentation

- [VS Code Quickstart](vscode-quickstart.md) - Initial Windows setup
- [Code Quality](../../development/code-quality.md) - Ruff, mypy, Markdown, and CI
- [Testing](../../development/testing.md) - pytest and coverage
- [Pre-commit Guide](../pre-commit-guide.md) - Local commit hooks
