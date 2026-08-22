# Are You Not Entertained? { .ayne-hero-title }

<div class="ayne-hero">
<p class="ayne-kicker">MOVIE DATA ENGINEERING / ANALYSIS FOUNDATION</p>
<p class="ayne-lede">A reproducible movie data pipeline built around asynchronous provider integration, deliberate quota controls, staged enrichment, and analytical storage.</p>
<p class="ayne-detail">AYNE makes the work behind a dataset visible: collection boundaries are explicit, failures can be recovered, and the same data can be queried again tomorrow.</p>
<div class="ayne-actions">
<a class="md-button md-button--primary" href="guides/data-collection-workflow/">Start with the workflow</a>
<a class="md-button" href="explanation/architecture/">Read the architecture</a>
</div>
</div>

## What This Project Shows

AYNE is a working data foundation before it is a product shell. It combines public movie
sources with engineering practices that make a growing dataset easier to trust and extend.

<div class="grid cards" markdown>

- :material-source-branch: **Explicit pipeline boundaries**

  Discovery, detail enrichment, refresh decisions, and analysis are separate stages with
  inspectable inputs and outputs.

- :material-timer-outline: **Responsible provider integration**

  Async HTTP clients share pacing, bounded retries, and persistent usage tracking so quota
  behavior remains part of the design.

- :material-database-outline: **Analysis-ready storage**

  DuckDB keeps source tables, identity, and refresh state queryable without requiring a
  database server.

- :material-test-tube: **Reproducible development**

  Typed Python, focused tests, notebooks, validation commands, and locked dependencies make
  the project straightforward to inspect and rerun.

</div>

## Daily Use

The normal workflow is deliberately bounded. Initialize the database, collect a small
sample, inspect the result, then increase limits only when the data looks right.

```powershell
uv sync --group dev
Copy-Item .env.example .env
uv run ayne db init
uv run ayne tmdb update --min-year 2020 --max-year 2024 --max-movies 100
uv run ayne tmdb enrich --limit 100
uv run ayne omdb enrich --max-movies 100
uv run ayne db stats
uv run ayne validate database
uv run ayne db manifest
uv run ayne validate all
```

Use `ayne collect daily` for routine refreshes and `--dry-run` to preview supported
operations. The [CLI Guide](guides/cli-guide.md) covers command options, while the
[Data Collection Workflow](guides/data-collection-workflow.md) explains the stages and
their dependencies.

!!! note "Windows-first examples"
    Commands in this site use Windows PowerShell syntax because that is the supported local
    workflow for this project. The Python package and `uv` commands remain cross-platform.

## Development

The contributor path is intentionally close to the daily path: make a focused change, run
its narrow check, then run the complete quality set before sharing it.

- [Code Quality](development/code-quality.md) - Ruff, mypy, Markdown checks, and CI
- [Testing](development/testing.md) - pytest, coverage, and the current test scope
- [Security](development/security.md) - Bandit, pip-audit, and secret handling
- [Logging](development/logging.md) - Console and JSON logging conventions
- [Pre-Commit Guide](guides/pre-commit-guide.md) - Local hook setup and troubleshooting
- [Git Workflow](guides/git-guide.md) - Branching, commits, pull requests, and recovery
- [VS Code Quickstart](guides/vs-code/vscode-quickstart.md) - Windows editor setup

Run the complete local quality set from the repository root:

```powershell
uv run ruff format --check src/ scripts/ tests/
uv run ruff check src/ scripts/ tests/
uv run mypy
uv run pytest
uv run pymarkdown scan docs/ README.md
uv run mkdocs build --strict
```

## Explore The System

- [Architecture](explanation/architecture.md) - Package boundaries and runtime flow
- [Database](reference/database.md) - DuckDB schema and table responsibilities
- [Data Collection Filtering](reference/data-collection-filtering.md) - Filters, limits, and overrides
- [Rate Limiting](reference/rate-limiting.md) - Pacing, retries, and provider constraints
- [Utilities Guide](guides/utilities-guide.md) - Query and I/O helpers for analysis
- [Technical Decisions](explanation/technical-decisions.md) - The reasoning behind major choices

## Project Status

The data collection and database workflow is the active, supported surface. The `ml`,
`api`, and `web` packages provide room for future work described in the
[roadmap](ROADMAP.md); their presence should not be read as a claim that those services are
complete.
