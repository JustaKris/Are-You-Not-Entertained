# VS Code Configuration & Linting Alignment

**Last Updated**: November 2024

This guide explains how VS Code linting settings should align with your `pyproject.toml` configuration and best practices for modern Python projects.

## Problem: Mismatched Linting Rules

### What Happened?

VS Code's built-in markdown linter was **more strict** than your `pyproject.toml` configuration:

- **pyproject.toml**: Disables certain rules for practical reasons (tables, code blocks, etc.)
- **VS Code**: Enforced stricter rules by default
- **Result**: False warnings on perfectly valid files

### Root Cause

Two separate linting systems were not aligned:

```
pyproject.toml (project standard)
           ↗                ↖
        ✅ pymarkdownlnt      ❌ VS Code Markdown Linter
           (passes)           (fails)
```

## Solution: `.vscode/settings.json`

Created `.vscode/settings.json` to sync VS Code with your project standards:

```json
{
  "markdownlint.config": {
    "MD013": false, // Line length (disabled for tables)
    "MD024": false, // Duplicate headings (disabled for docs)
    "MD031": false, // Blanks around code fences
    "MD033": false, // Inline HTML (disabled for badges)
    "MD036": false, // Emphasis as headings
    "MD040": false  // Language for code blocks (not required)
  }
}
```

## Modern Python Project Best Practices

### 1. Version Control Configuration Files

**Include in git**:

```bash
✅ .vscode/settings.json      # Project-wide VS Code settings
✅ .vscode/extensions.json    # Recommended extensions
✅ pyproject.toml             # Python project standards
✅ .editorconfig              # Cross-editor settings
```

**Don't include**:

```bash
❌ .vscode/launch.json        # Personal debug configs
❌ .vscode/extensions/...     # User's installed extensions
```

### 2. Linting Configuration Hierarchy

Modern projects define standards in order of precedence:

```
1. pyproject.toml             # Project-wide standards (linters, formatters)
   └─ [tool.ruff]
   └─ [tool.black]
   └─ [tool.mypy]
   └─ [tool.pymarkdown]

2. .editorconfig              # Cross-editor basics (indentation, line length)

3. .vscode/settings.json      # VS Code specific (UI, extensions)
   └─ Only tool-specific overrides needed

4. .vscode/launch.json        # Developer-specific debug configs (not versioned)
```

### 3. Configuration You Created

Here's what was set up in `.vscode/settings.json`:

```json
{
  // Python formatting
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  },

  // Markdown linting - Matches pyproject.toml
  "[markdown]": {
    "editor.defaultFormatter": "DavidAnson.vscode-markdownlint",
    "editor.formatOnSave": true
  },
  "markdownlint.config": {
    "MD013": false,  // Matches: plugins.md013.enabled = false
    "MD024": false,  // Matches: plugins.md024.enabled = false
    "MD031": false,  // Matches: plugins.md031.enabled = false
    "MD033": false,  // Matches: plugins.md033.enabled = false
    "MD036": false,  // Matches: plugins.md036.enabled = false
    "MD040": false   // Matches: plugins.md040.enabled = false
  },

  // Editor standards
  "editor.rulers": [100],           // Match pyproject.toml line-length
  "editor.trimAutoWhitespace": true,
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,

  // Exclude noise from workspace
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true
  }
}
```

## Workflow: How This Works Now

### Scenario: You edit `data-collection-workflow.md`

**Before** (misaligned):

```
Edit file in VS Code
         ↓
VS Code markdown linter (strict) ❌ Shows 10 warnings
         ↓
You run: pymarkdownlnt scan ✅ Passes (0 issues)
         ↓
Confusion! 😕
```

**After** (aligned):

```
Edit file in VS Code
         ↓
VS Code markdown linter (same as pymarkdownlnt) ✅ 0 warnings
         ↓
You run: pymarkdownlnt scan ✅ Passes (0 issues)
         ↓
Perfect alignment! ✨
```

## Recommended Extensions

Install these for best experience:

```bash
# Install via VS Code Extensions or:
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension DavidAnson.vscode-markdownlint
code --install-extension eamodio.gitlens
code --install-extension tamasfe.even-better-toml
```

**What each does**:

| Extension | Purpose |
|-----------|---------|
| `ms-python.python` | Python language support, linting, debugging |
| `ms-python.vscode-pylance` | Fast IntelliSense & type checking |
| `DavidAnson.vscode-markdownlint` | Markdown linting with custom rules |
| `eamodio.gitlens` | Git blame & history in editor |
| `tamasfe.even-better-toml` | TOML syntax highlighting |

## How to Fix It Yourself

### Step 1: Create `.vscode/settings.json`

```json
{
  "markdownlint.config": {
    "MD013": false,
    "MD024": false,
    "MD031": false,
    "MD033": false,
    "MD036": false,
    "MD040": false
  }
}
```

### Step 2: Verify Alignment

Run command in VS Code:

```bash
# Terminal
uv run pymarkdownlnt scan docs/

# VS Code should show 0 warnings
```

### Step 3: Reload VS Code

```
Ctrl+Shift+P → Developer: Reload Window
```

## Python-Specific: How It Works for Python

Your `pyproject.toml` also configures Python linting:

```toml
[tool.ruff]
line-length = 100
# ... other rules

[tool.black]
line-length = 100
target-version = ['py311', 'py312']
```

VS Code automatically reads `pyproject.toml` via Pylance/Python extension, so you don't need special config for Python!

The `.vscode/settings.json` **only** adds VS Code-specific overrides (like the markdown rules).

## Best Practices Summary

### ✅ DO

1. **Version control `.vscode/settings.json`**: Team consistency
2. **Define standards in `pyproject.toml`**: Single source of truth
3. **Align VS Code with project standards**: Avoid confusion
4. **Use recommended extensions**: Better UX

### ❌ DON'T

1. **Have different rules in different places**: Causes headaches
2. **Ignore VS Code warnings**: Usually catching real issues
3. **Use personal settings in global VS Code**: Breaks for teammates
4. **Commit `.vscode/launch.json`**: Personal debug configs

## When to Add `.editorconfig`

If you need cross-editor consistency (Vim, Sublime, etc.):

```ini
# .editorconfig
root = true

[*]
indent_style = space
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_size = 4
max_line_length = 100

[*.{json,yaml,yml}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false  # Markdown uses 2 spaces for line breaks
```

## Troubleshooting

### Q: Changes in `.vscode/settings.json` not taking effect

**A**: Reload VS Code:

```
Ctrl+Shift+P → Developer: Reload Window
```

### Q: Still seeing markdown warnings

**A**: Check the extension is installed:

```
Ctrl+Shift+X (Extensions)
Search: "vscode-markdownlint"
Install: DavidAnson.vscode-markdownlint
```

### Q: How to sync across team?

**A**:

1. Commit `.vscode/settings.json` to git ✅
2. Team pulls changes
3. Team reloads VS Code
4. Done!

### Q: How to override for specific file?

**A**: VS Code supports file-specific settings:

```json
{
  "[markdown]": {
    "editor.wordWrap": "on"
  },

  // Only for docs folder
  "[markdown]": {
    "editor.formatOnSave": false
  }
}
```

## Related Documentation

- [Modern Utilities Guide](../copilot_artifacts/MODERN_UTILITIES_GUIDE.md) - I/O and serialization
- [Package Structure](../copilot_artifacts/QUICK_START_NEW_PACKAGE.md) - Project organization
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [Pylance repository](https://github.com/microsoft/pylance-release)

## Files Created/Modified

- ✅ `.vscode/settings.json` - VS Code settings aligned with pyproject.toml
- ✅ `.vscode/extensions.json` - Recommended extensions list
- 📄 `pyproject.toml` - Already had correct markdown linting config

All files committed to git for team consistency.
