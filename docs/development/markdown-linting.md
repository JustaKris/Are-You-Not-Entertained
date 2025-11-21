# Markdown Linting

Documentation quality is maintained through automated markdown linting using `pymarkdownlnt`.

## Why Separate from Code Linting?

Markdown linting is **intentionally separated** from Python code linting for several reasons:

1. **Different concerns** - Documentation style vs code quality
2. **Different audiences** - Documentation maintainers vs developers
3. **Different fix workflows** - Content editing vs code refactoring
4. **Independent failures** - Docs issues shouldn't block code deployment
5. **Clearer CI feedback** - Easy to identify doc vs code problems

## About pymarkdownlnt

**pymarkdownlnt** is the recommended modern markdown linter for Python projects:

✅ **Pure Python** - No Ruby/Node.js dependencies (unlike markdownlint)
✅ **Configurable** - Flexible rule configuration via pyproject.toml
✅ **Fast** - Efficient scanning of large documentation sets
✅ **Active development** - Regular updates and improvements
✅ **CLI + Library** - Can be used standalone or integrated

### Alternatives Considered

| Tool | Pros | Cons | Verdict |
|------|------|------|---------|
| **pymarkdownlnt** | Pure Python, fast, configurable | Younger project | ✅ **Best for Python projects** |
| markdownlint-cli | Popular, mature, extensive rules | Requires Node.js | ❌ External dependency |
| mdl (Ruby) | Well-established | Requires Ruby | ❌ External dependency |
| remark-lint | Plugin ecosystem | Requires Node.js, complex setup | ❌ Too complex |

## Configuration

Markdown linting is configured in `pyproject.toml`:

```toml
[tool.pymarkdown]
plugins.md013.enabled = false  # Disable line length (tables can be long)
plugins.md033.enabled = false  # Allow inline HTML (badges, images)
plugins.md036.enabled = false  # Allow emphasis as pseudo-headings
extensions.front-matter.enabled = true  # YAML front matter support
extensions.tables.enabled = true  # Enable tables
```

### Key Rules

| Rule | Description | Status | Reason |
|------|-------------|--------|--------|
| MD013 | Line length | ❌ Disabled | Tables, code blocks, long URLs |
| MD033 | Inline HTML | ❌ Disabled | Badges, centered images, styling |
| MD036 | Emphasis as heading | ❌ Disabled | Common in step lists, examples |
| MD031 | Blank lines around code | ✅ Enabled | Improves readability |
| MD040 | Code fence language | ✅ Enabled | Enables syntax highlighting |

## Running Locally

### Scan All Documentation

```powershell
# Scan all markdown files
uv run pymarkdown --config pyproject.toml scan docs/ README.md

# Scan specific directory
uv run pymarkdown --config pyproject.toml scan docs/development/

# Scan single file
uv run pymarkdown --config pyproject.toml scan README.md
```

### Fix Issues

pymarkdownlnt doesn't auto-fix issues. Fixes must be manual:

1. Run scan to identify issues
2. Review error messages
3. Edit files to resolve issues
4. Re-run scan to verify

**Common fixes:**

### Example: MD031 - Add blank lines around code blocks

Before - text immediately adjacent to code:

```markdown
Some text
```bash
code
```markdown
More text
```

After - blank lines around code blocks:

```markdown
Some text

```bash
code
```

More text

```markdown

**Example: MD040 - Add language to code blocks**

Before - no language specified:

```text
code
```

After - language specified:

```python
code
```

## CI/CD Integration

Markdown linting runs as a **separate CI stage** from code linting.

### Pipeline Position

```text
lint (Python) → test → markdown-lint → security
```

This allows:

- ✅ Code linting to pass independently
- ✅ Documentation fixes without blocking deployments
- ✅ Clear separation of concerns

### CI Configuration

File: `.github/workflows/markdown-lint.yml`

```yaml
- name: Run markdown linting
  run: |
    uv run pymarkdown scan docs/ README.md
  continue-on-error: true  # Won't block pipeline
```

### Failure Behavior

- **Status**: `continue-on-error: true` (warnings only)
- **When**: Runs on pushes/PRs with doc changes
- **Impact**: Non-blocking - won't prevent merges
- **Visibility**: Shows warning in GitHub Actions

## Best Practices

### When Writing Docs

1. **Use proper heading hierarchy** - Don't skip levels (H1 → H2 → H3)
2. **Add language to code blocks** - Enables syntax highlighting
3. **Blank lines around blocks** - Code, lists, quotes need spacing
4. **Consistent list markers** - Use `-` for unordered, `1.` for ordered
5. **No trailing whitespace** - Clean up line endings

### Common Pitfalls

**❌ Avoid:**

```markdown
# Heading
## Subheading
#### Sub-sub-heading  # Skipped H3!

code without blank line above (missing blank line and language)

List without spacing:
- Item 1
- Item 2
Next paragraph (no blank line before)
```

**✅ Prefer:**

```markdown
# Heading

## Subheading

### Sub-sub-heading

Text before code.

```python
code_with_spacing()
```

List with proper spacing:

- Item 1
- Item 2

Next paragraph with blank line.

```markdown

### Long Lines

Since MD013 is disabled, be reasonable:

- ✅ **OK**: URLs, table content, code blocks
- ✅ **OK**: Short overruns (85-100 chars)
- ❌ **Avoid**: Very long prose paragraphs (>120 chars)

Break long paragraphs naturally:

**Bad:**

```text
This is a really long paragraph that goes on and on...
```

**Good:**

```text
This is a paragraph that is broken into reasonable line lengths.
It improves readability and makes diffs clearer.
```

## Troubleshooting

### No Output from Scan

If pymarkdown runs but shows no output:

```powershell
# Verify installation
uv run pymarkdown --version

# Check config
uv run pymarkdown plugins list

# Try with verbose output
uv run pymarkdown scan docs/ --verbose
```

### Too Many Errors

If overwhelming number of errors:

1. **Fix incrementally** - Start with one directory
2. **Disable strict rules** - Update `pyproject.toml`
3. **Focus on critical** - MD040, MD031 are most important
4. **Batch similar fixes** - Fix all MD040s at once

### False Positives

If a rule incorrectly flags valid markdown:

1. **Check if it's actually valid** - Validate markdown spec
2. **Disable the rule** - Add to `pyproject.toml` ignore list
3. **Use inline ignore** - `<!-- markdownlint-disable MD### -->`

## Integration with Editors

### VS Code

Install extension: **Markdown Lint** (davidanson.vscode-markdownlint)

Settings (`.vscode/settings.json`):

```json
{
  "markdownlint.config": {
    "MD013": false,
    "MD033": false,
    "MD036": false
  }
}
```

### Pre-commit Hook (Optional)

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pymarkdown
        name: Markdown Linting
        entry: uv run pymarkdown scan
        language: system
        files: \\.md$
        pass_filenames: true
```

## Maintenance

### Updating Rules

To enable/disable rules:

1. Edit `pyproject.toml` under `[tool.pymarkdown]`
2. Test locally: `uv run pymarkdown scan docs/`
3. Commit and push
4. Verify in CI pipeline

### Batch Fixes

When adding new rules or fixing legacy docs:

```powershell
# Scan and save results
uv run pymarkdown scan docs/ > markdown-issues.txt

# Fix by category
# 1. Fix all MD040 (code block languages)
# 2. Fix all MD031 (blank lines)
# 3. Fix remaining issues

# Verify
uv run pymarkdown scan docs/
```

## Resources

- [pymarkdownlnt GitHub](https://github.com/jackdewinter/pymarkdown)
- [pymarkdownlnt Documentation](https://pypi.org/project/pymarkdownlnt/)
- [Markdown Guide](https://www.markdownguide.org/)
- [CommonMark Spec](https://spec.commonmark.org/)

## Summary

**Key Takeaways:**

✅ pymarkdownlnt is the best pure-Python markdown linter
✅ Separate markdown linting from code linting in CI
✅ Configure sensibly - disable overly strict rules
✅ Non-blocking in CI - won't prevent deployments
✅ Manual fixes required - no auto-format available
✅ Focus on readability and correctness, not perfection
