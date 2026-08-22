# 🎬 Are You Not Entertained?

> A Python data engineering and analysis project for understanding movie performance.

![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active%20Development-yellow.svg)

## 🧭 Overview

**Are You Not Entertained?** builds a movie performance dataset from TMDB, OMDB, and
The Numbers. The project combines automated collection, a DuckDB database for efficient
analytics, and the engineering foundations for grounded analysis and predictive modeling.

The current milestone is the data foundation: collection, refresh, quota tracking,
validation, and analysis workflows are usable, while the agent, API, and deployment
surfaces remain planned extensions.

### 🎯 Current Features

- **Automated Data Collection**: Async provider clients with staged discovery, detail
  enrichment, refresh strategies, bounded retries, and provider-aware rate limiting
- **Database-Centric Architecture**: DuckDB source tables for movie identity, TMDB, OMDB,
  The Numbers, refresh state, and persistent daily API usage
- **Modern Python Practices**: Type hints, Pydantic settings, structured logging, a
  `src/ayne` package layout, and a Typer/Rich command-line interface
- **Analysis Ready**: Query helpers that join source tables into pandas DataFrames for
  notebooks, reports, and downstream modeling
- **Reproducible Quality Checks**: Focused unit tests, Ruff, mypy, Bandit, pip-audit,
  pre-commit, and strict documentation builds

### 🚧 Coming Next

- **Grounded Movie Analysis Agent**: Read-only, bounded query tools that return evidence
  from the movie dataset through a configurable workflow
- **Data Contracts And Quality**: Versioned schemas, stronger freshness and domain checks,
  and dataset manifests for reproducible releases
- **API And Local Kubernetes Delivery**: A small FastAPI service with health checks,
  container packaging, and a documented local deployment path
- **Predictive Modeling**: Feature engineering, model evaluation, and experiment tracking
  for box-office and movie-performance questions

## 🛠️ Tech Stack

- **Python 3.12 or 3.13** with modern async/await patterns
- **uv** for fast, locked environment and dependency management
- **httpx** for asynchronous HTTP clients, with shared retry and rate-limiting utilities
- **DuckDB** for local analytical storage and **PyArrow/Parquet** for efficient datasets
- **pandas** for analysis and **Polars** for performance-sensitive transformations
- **Pydantic Settings, YAML, and `.env`** for typed environment configuration
- **Typer and Rich** for the command-line workflow and terminal output
- **Jupyter, matplotlib, seaborn, and Plotly** for exploratory analysis and reporting
- **pytest, Ruff, mypy, Bandit, pip-audit, pre-commit, and MkDocs Material** for quality
  and documentation
- **scikit-learn, XGBoost, and MLflow** as the declared foundation for planned modeling

## 🚀 Quick Start

### 🧰 Prerequisites

- Python 3.12 or 3.13
- [uv](https://docs.astral.sh/uv/) for environment and dependency management
- API keys for [TMDB](https://www.themoviedb.org/settings/api) and
  [OMDB](https://www.omdbapi.com/apikey.aspx)

### 📦 Install

```powershell
git clone https://github.com/JustaKris/Are-You-Not-Entertained.git
cd Are-You-Not-Entertained
uv sync --group dev
```

Copy `.env.example` to `.env` and add the TMDB and OMDB keys:

```powershell
Copy-Item .env.example .env
```

Verify the installation:

```powershell
uv run ayne --help
uv run ayne version
```

Commands below are shown as `uv run ayne ...` so they work without manually activating
the virtual environment.

## 🗄️ Database And Data Workflow

The default database is `data/db/movies.duckdb`. Initialize it before collecting data:

```powershell
uv run ayne db init
uv run ayne db test
uv run ayne db stats
```

### 🌱 Start With An Empty Database

Collection is intentionally staged. Discovery stores basic movie identities first;
enrichment then fills source-specific details.

```powershell
# Discover a bounded set of movies
uv run ayne tmdb update --min-year 1990 --max-year 2024 --max-movies 1000

# Add detailed TMDB data and IMDb identifiers
uv run ayne tmdb enrich --limit 1000

# Add ratings, awards, and other OMDB data
uv run ayne omdb enrich --max-movies 1000

# Optionally add The Numbers financial data
uv run ayne numbers enrich --max-movies 250

# Check database and source-level data quality
uv run ayne db stats
uv run ayne validate all
```

Use `--dry-run` before a larger collection, and keep limits aligned with the providers'
request quotas. TMDB year ranges are split automatically when a query would exceed its
page limit. The [CLI Guide](docs/guides/cli-guide.md) documents every command and option.

### 🔄 Maintain Existing Data

For routine updates, refresh recent records or use the combined workflow:

```powershell
uv run ayne tmdb refresh --min-year 2024 --limit 100
uv run ayne omdb refresh --min-year 2024 --limit 100
uv run ayne collect daily --tmdb-refresh 50 --omdb-limit 30
```

### 🔎 Query The Database

The query helpers join the source tables and return pandas DataFrames:

```python
from ayne.utils.query_utils import (
    execute_custom_query,
    get_movies_with_financials,
    load_full_dataset,
)

movies = load_full_dataset(include_nulls=True)
financial_movies = get_movies_with_financials(min_budget=1_000_000)

popular_genres = execute_custom_query(
    """
    SELECT genre_names, COUNT(*) AS movie_count, AVG(revenue) AS average_revenue
    FROM movies m
    INNER JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
    GROUP BY genre_names
    ORDER BY movie_count DESC
    """
)
```

The main tables are `movies`, `tmdb_movies`, `omdb_movies`, `numbers_movies`, and
`movie_refresh_state`/refresh tracking columns. See the [database reference](docs/reference/database.md)
and [data directory guide](data/README.md) for storage details.

### 📓 Notebooks And Processed Data

Install the notebook dependency group and start Jupyter from the repository root:

```powershell
uv sync --group notebooks
uv run jupyter lab notebooks/
```

Notebooks read from DuckDB through the same query helpers. Persist derived datasets in
`data/processed/`, preferably as Parquet, and keep raw provider responses in
`data/raw/` immutable. The repository ignores database, raw, and generated data files.

## 🧑‍💻 Development Workflow

Install the complete development environment with `uv sync --group dev`. The canonical
local checks are:

```powershell
uv run ruff format --check src/ scripts/ tests/
uv run ruff check src/ scripts/ tests/
uv run mypy
uv run pytest
uv run bandit -r src/ -c pyproject.toml
uv run pymarkdown scan docs/ README.md
uv run mkdocs build --strict
```

Run `uv run pre-commit install` once to enable the fast file checks before commits. CI
runs the full test, type-checking, documentation, and security workflows on supported
Python versions. The development guides explain the purpose and scope of each check:

- [Code quality](docs/development/code-quality.md)
- [Testing](docs/development/testing.md)
- [Security](docs/development/security.md)
- [Pre-commit](docs/guides/pre-commit-guide.md)
- [Git workflow](docs/guides/git-guide.md)

## 🗂️ Project Structure

```text
Are-You-Not-Entertained/
├── src/ayne/              # Installable application package
│   ├── core/              # Settings, logging, and shared concerns
│   ├── data_collection/   # Provider clients, rate limiting, and orchestration
│   ├── database/          # DuckDB access and schema operations
│   ├── utils/             # Query, I/O, and data utilities
│   ├── cli/               # Typer command groups
│   ├── api/               # API extension point
│   ├── ml/                # Modeling extension point
│   └── web/               # Web extension point
├── tests/unit/            # Focused tests for collection and refresh behavior
├── data/                  # Database, raw, processed, and generated artifacts
├── notebooks/             # Exploratory analysis and modeling notebooks
├── scripts/               # Maintenance and audit utilities
├── configs/               # Development, staging, and production settings
└── docs/                  # MkDocs project documentation
```

## ⚙️ Configuration

Runtime settings come from `.env` and the selected environment configuration. The
available YAML examples are in `configs/`:

```text
configs/
├── development.yaml
├── staging.yaml
└── production.yaml
```

Set the environment with `ENVIRONMENT=development` (or `staging` or `production`).
Settings are defined in `ayne.core.config.settings`; do not commit `.env` or API keys.

## 📚 Documentation

The [documentation site](docs/index.md) is built with MkDocs Material. Useful starting
points are:

- [CLI Guide](docs/guides/cli-guide.md) for commands and collection options
- [Architecture](docs/explanation/architecture.md) for component boundaries
- [Data Collection Workflow](docs/guides/data-collection-workflow.md) for ingestion
- [Refresh Strategy](docs/reference/refresh-strategy.md) for update decisions
- [Technical Decisions](docs/explanation/technical-decisions.md) for project trade-offs
- [Database Monitoring](docs/guides/database-monitoring.md) for health checks

## 🗺️ Roadmap

The current phase is the data foundation. The next phase is analysis and modeling,
including feature engineering, evaluation, and reproducible experiment tracking. Later
work may add API endpoints, model serving, monitoring, and container deployment.

The [roadmap](docs/ROADMAP.md) is the detailed planning document; this README describes
the current state rather than promising a completed platform.

## License

MIT License. See [LICENSE](LICENSE) for details.
