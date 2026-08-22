# Testing

AYNE uses pytest for focused, isolated tests around collection and refresh behavior.
Tests run against temporary data where persistence is required and do not call external
APIs.

## Quick Start

Install the test dependencies and run the configured suite:

```powershell
uv sync --group test
uv run pytest
```

The repository configuration also produces terminal, HTML, and XML coverage reports:

```powershell
# Run one test module
uv run pytest tests/unit/test_refresh_strategy.py

# Run a single test
uv run pytest tests/unit/test_api_usage.py::test_get_remaining_quota

# Inspect missing lines in the terminal
uv run pytest --cov-report=term-missing
```

The default coverage floor is 20 percent. The latest local validation covered 41 tests
at about 27.8 percent, so the floor is currently a guardrail rather than a claim of
comprehensive application coverage.

## Current Test Scope

```text
tests/
└── unit/
    ├── test_api_usage.py
    ├── test_database_foundation.py
    ├── test_refresh_strategy.py
    └── test_the_numbers.py
```

- `test_api_usage.py` checks the persistent daily provider-usage ledger with a temporary
  DuckDB database.
- `test_database_foundation.py` checks migration idempotence, relational constraints,
  contract validation, the sanitized demo fixture, and manifest registration/hashing.
- `test_refresh_strategy.py` checks meaningful-change detection and mature-movie freeze
  decisions without I/O or network calls.
- `test_the_numbers.py` checks title slug generation, candidate URLs, money parsing, and
  HTML financial-field extraction.

There is not currently a committed integration-test suite or live-provider test suite.
Those tests should be added with explicit fixtures and credentials handling rather than
making network access part of the default test run.

## Writing Tests

Use Arrange-Act-Assert structure and keep each test focused on one behavior. Prefer
descriptive test names, parametrization for related inputs, and dependency injection or
mocks for external services. Test missing values, boundaries, malformed provider data,
and failure paths as well as successful cases.

Example using the project's current refresh helpers:

```python
from ayne.data_collection.refresh_strategy import has_meaningful_change


def test_change_is_detected_for_a_changed_field():
    before = {"vote_count": 100}
    after = {"vote_count": 150}

    assert has_meaningful_change(before, after, ["vote_count"])
```

For database tests, use pytest's `tmp_path` fixture and close `DuckDBClient` instances
after the test. Keep test data small and deterministic.

## Coverage Reports

Coverage output is configured in `pyproject.toml`:

- Terminal report with missing lines
- HTML report at `reports/coverage/html/`
- XML report at `reports/coverage/coverage.xml`
- Minimum total coverage of 20 percent

Open the HTML report on Windows with:

```powershell
Start-Process reports/coverage/html/index.html
```

Do not treat the current floor as a target for new code. New behavior should have tests
that exercise its normal and failure paths, with broader coverage added as the
collection and query surfaces grow.

## CI

The `CI / Python` workflow runs the suite on Python 3.12 and 3.13. It uploads JUnit,
coverage, and test-result artifacts even when a test job fails. Coverage upload to
Codecov is informational and does not determine the job result.

Run the same basic test command locally:

```powershell
uv run pytest
```

## Troubleshooting

If `ayne` or an application import cannot be found, synchronize the relevant dependency
group from the repository root:

```powershell
uv sync --group test
```

If tests pass locally but fail in CI, check the Python version, test isolation, fixture
paths, and whether the test relies on an untracked local database or environment
variable. Keep provider credentials out of tests unless a separate, explicitly opt-in
integration workflow is introduced.

## Related Documentation

- [Code Quality](code-quality.md) - Formatting, linting, type checking, and CI checks
- [Security](security.md) - Security scans and dependency reports
- [Database](../reference/database.md) - Schema and database operations
