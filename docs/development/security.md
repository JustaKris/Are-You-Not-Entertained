# Security

Security checks are part of the repository's normal development workflow. They cover
Python source analysis, known dependency vulnerabilities, secret handling, and GitHub
repository protections.

## Local Checks

Run Bandit with the repository configuration:

```powershell
uv sync --group security
uv run bandit -r src/ -c pyproject.toml
```

To create a machine-readable report for local inspection:

```powershell
uv run bandit -r src/ -c pyproject.toml -f json -o bandit-report.json
```

Run the dependency audit separately:

```powershell
uv run pip-audit --skip-editable
```

`pip-audit` reports known vulnerabilities in resolved dependencies. It is advisory in
CI because upstream fixes and transitive dependency constraints can require review
before changing the lockfile. Bandit is the blocking source scan.

## CI Workflow

`.github/workflows/security-audit.yml` runs on relevant pull requests and pushes, every
Monday, and on demand. It:

- Runs Bandit against `src/` using `pyproject.toml`.
- Runs `pip-audit --skip-editable` and keeps it advisory.
- Uploads JSON reports as the `security-reports` artifact.

CodeQL and dependency review are separate GitHub workflows. Dependabot proposes updates
to supported dependencies; review those changes together with `uv.lock`.

## Secrets

Keep API keys and credentials in `.env` or the environment. Never commit them to source,
notebooks, logs, test fixtures, or generated reports. The local pre-commit hook includes
`detect-private-key`, and `.env` is ignored by Git.

If a secret is exposed:

1. Revoke or rotate it immediately with the provider.
2. Remove it from the working tree and any generated artifacts.
3. Determine whether it entered Git history and clean the history using the repository's
   approved process.
4. Check logs, CI artifacts, and forks for further exposure.

Removing a value from the latest commit does not invalidate a credential that was
already exposed.

## Secure Coding Practices

- Validate collection filters and limits before using them in provider requests or SQL.
- Use parameterized SQL for values supplied at runtime; keep table and column names on
  controlled allowlists when they cannot be parameterized.
- Do not log API keys, authorization headers, database credentials, or complete provider
  responses when they may contain sensitive data.
- Keep provider requests bounded, rate-limited, and respectful of each service's terms.
- Treat downloaded HTML, JSON, and notebook data as untrusted input.
- Prefer explicit exceptions and useful error context without including secrets.

## Handling Findings

Do not suppress a Bandit finding without understanding the data flow. When an exception
is justified, keep the narrowest possible suppression next to the affected statement
and explain the validation or boundary that makes it safe. Dependency findings should
be checked against the resolved package version in `uv.lock` before upgrading or
adding an exclusion.

## Related Documentation

- [Code Quality](code-quality.md) - Ruff, mypy, Markdown, and CI checks
- [Pre-commit Guide](../guides/pre-commit-guide.md) - Local secret and file checks
- [Logging](logging.md) - Structured logs and sensitive-data guidance
