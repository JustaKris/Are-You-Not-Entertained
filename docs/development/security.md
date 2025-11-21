# Security Guide

Security practices and vulnerability scanning for the TV-HML project.

## Overview

Security best practices include:

- **Static security scanning** with Bandit
- **Dependency vulnerability scanning** with pip-audit  
- **Secret scanning** via GitLab Cycode
- **Secure coding practices**
- **CI/CD security gates**

## Bandit Security Scanning

### Running Locally

```powershell
# Scan source code
uv run bandit -r src/

# Generate JSON report for CI
uv run bandit -r src/ -f json -o bandit-report.json

# Show only high severity
uv run bandit -r src/ -ll
```

### Common Issues & Fixes

**SQL Injection (B608):**

Our Athena queries use f-strings safely because year/month are validated integers from Pydantic models and table names come from configuration.

```python
# Add nosec when inputs are validated
query = f"""SELECT * FROM {table} WHERE year='{year}'""".strip()  # nosec B608
```

**Assert in Production (B101):**

Replace asserts with proper exceptions:

```python
# Bad
assert isinstance(df, pd.DataFrame)

# Good  
if not isinstance(df, pd.DataFrame):
    raise TypeError("Expected DataFrame")
```

**Hardcoded Secrets (B105-B107):**

Use environment variables:

```python
# Bad
password = "example_value"

# Good
import os
password = os.getenv("DB_PASSWORD")
```

## Dependency Scanning

```powershell
# Scan for vulnerabilities
uv run pip-audit

# Update dependencies
uv lock --upgrade
```

## Secret Scanning (GitLab Cycode)

Cycode scans on every push. If blocked:

1. Remove the secret from code
2. Rewrite git history
3. Force push with `--force-with-lease`
4. Rotate the exposed secret

## CI/CD Integration

Security scans run automatically:

```yaml
security-scan:
  stage: security
  script:
    - uv run bandit -r src/ -f json -o bandit-report.json
    - uv run pip-audit
  allow_failure: false
```

## Related Documentation

- **[Linting Guide](linting.md)** - Code quality checks
- **[CI/CD Pipeline](ci-cd.md)** - Automated security scanning
