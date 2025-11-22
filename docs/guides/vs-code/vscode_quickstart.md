# Getting Started with VS Code for AYNE

## First Time Setup (One-Time)

### 1. Install Recommended Extensions

When you open the project in VS Code, you'll see a notification suggesting extensions.

Or manually install:

```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension DavidAnson.vscode-markdownlint
code --install-extension eamodio.gitlens
```

### 2. Select Python Interpreter

Press `Ctrl+Shift+P` and search: **Python: Select Interpreter**

Choose: `.venv/Scripts/python.exe` (or the one from your virtual environment)

### 3. Reload VS Code

Press `Ctrl+Shift+P` → **Developer: Reload Window**

**Done!** Configuration is automatic from `.vscode/settings.json`

## How It Works

### Python Files

```python
# Auto-format on save (configured)
def hello(x,y,z):  # Poorly spaced
    return x+y+z
```

Save → Automatically formatted ✨

### Markdown Files

```markdown
```
This code block has no language specified
```
```

In VS Code: ✅ No warning (configured to allow)
In pymarkdownlnt: ✅ Passes (same config)

**No conflicts!**

## Commands You'll Use

| Command | Shortcut | Purpose |
|---------|----------|---------|
| Format Document | Alt+Shift+F | Format active file |
| Format Selection | Ctrl+K Ctrl+F | Format selected code |
| Fix All Issues | Ctrl+. | Auto-fix problems |
| Open Terminal | Ctrl+` | Integrated terminal |
| Command Palette | Ctrl+Shift+P | All commands |

## Common Tasks

### Run Tests

```bash
# Terminal (Ctrl+`)
uv run pytest tests/
```

### Format Code

```bash
# Terminal
uv run black .
uv run ruff check --fix .
```

### Check Markdown

```bash
# Terminal
uv run pymarkdownlnt scan docs/
```

### Run Linters

```bash
# Terminal - Run all checks
uv run ruff check src/
uv run mypy src/
```

## Troubleshooting

### Python IntelliSense not working?

1. Press `Ctrl+Shift+P`
2. Search: **Pylance: Restart Pylance**
3. Wait ~5 seconds

### Markdown warnings still showing?

1. Check extension installed: `Ctrl+Shift+X` → search "markdownlint"
2. Reload: `Ctrl+Shift+P` → **Developer: Reload Window**

### Code not formatting on save?

1. Check format-on-save enabled: `Ctrl+,` (Settings)
2. Search: "formatOnSave"
3. Make sure it's enabled

## Project Structure Quick Reference

```
src/ayne/              # Main package
├── core/              # Configuration & logging
├── data_collection/   # API clients
├── database/          # DuckDB operations
├── ml/                # Models & serialization
└── utils/             # I/O utilities

notebooks/             # Jupyter notebooks
├── 01_*.ipynb         # Imputation
├── 02_*.ipynb         # EDA
├── 03_*.ipynb         # Modeling
└── 04_*.ipynb         # Predictions

docs/                  # Documentation
├── reference/         # Architecture docs
└── copilot_artifacts/ # Guides

tests/                 # Unit tests
scripts/               # Utility scripts
```

## Next Steps

- Read: [`MODERN_UTILITIES_GUIDE.md`](MODERN_UTILITIES_GUIDE.md) - I/O & serialization
- Read: [`QUICK_START_NEW_PACKAGE.md`](QUICK_START_NEW_PACKAGE.md) - Package structure
- Run: `uv run pytest tests/` - Check tests pass
- Create: Your first notebook in `notebooks/`

## Getting Help

- **Python issues**: Check terminal output, check Pylance language server
- **Formatting issues**: Run `uv run black --check src/` to see what would change
- **Linting issues**: Run `uv run ruff check src/` to see detailed errors
- **Markdown issues**: Run `uv run pymarkdownlnt scan docs/` to match VS Code

## Remember

✅ All configuration synced to project (`.vscode/settings.json`, `pyproject.toml`)
✅ Team members get same experience
✅ No personal settings needed
✅ Everything version-controlled

Happy coding! 🚀
