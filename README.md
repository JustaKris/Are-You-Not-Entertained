# 🎬 Are You Not Entertained?

> A modern data science project for movie box office analysis and prediction, built with production-grade Python practices.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active%20Development-yellow.svg)

## Overview

**Are You Not Entertained?** analyzes movie performance using data from multiple sources (TMDB, OMDB, The Numbers). The project features automated data collection, a DuckDB database for efficient analytics, and prepares the groundwork for predictive modeling pipelines.

### 🎯 Current Features

- **Automated Data Collection**: Async API clients with intelligent refresh strategies
- **Database-Centric Architecture**: DuckDB for fast analytical queries
- **Modern Python Practices**: Type hints, Pydantic settings, structured logging
- **Data Analysis Ready**: Query utilities for Jupyter notebooks
- **Optimized Performance**: 5-8x faster collection with rate limiting and caching

### 🚧 Coming Soon

- **Predictive Modeling**: Revenue forecasting and success prediction models
- **Analysis Notebooks**: Genre trends, director performance, temporal patterns
- **REST API**: Single movie performance metrics and analysis endpoints

## 🛠️ Tech Stack

- **Python 3.12+** with modern async/await patterns
- **DuckDB** for analytical database
- **httpx** for async HTTP requests
- **Pydantic** for configuration management
- **pandas** for data manipulation
- **Jupyter** for exploratory analysis

-## 📦 Installation

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager (recommended)
- API keys for TMDB and OMDB

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/JustaKris/Are-You-Not-Entertained.git
   cd Are-You-Not-Entertained
   ```

2. **Install dependencies with uv**

   ```bash
   uv venv
   uv pip install -e "."
   ```

3. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # TMDB_API_KEY=your_tmdb_key
   # OMDB_API_KEY=your_omdb_key
   ```

4. **Verify installation**

   ```bash
   ayne --help
   ayne version
   ```

## 🚀 Quick Start

### Initialize Database

Set up the database schema:

```bash
# Initialize database
ayne db init

# Test connectivity
ayne db test

# View database statistics
ayne db stats
```

### Data Collection

Collect movie data with the CLI:

```bash
# Discover new movies from TMDB (basic info, fast)
ayne tmdb update --max-movies 1000 --min-year 2025 --max-year 2026

# Wide year ranges work automatically (auto-splits if >500 pages)
ayne tmdb update --min-year 1950 --max-year 2024  # Handles 500-page limit automatically

# Enrich discovered movies with detailed TMDB data (slower, complete data)
ayne tmdb enrich --limit 500 --min-year 2020

# Enrich with OMDB data (ratings, box office, awards)
ayne omdb enrich --max-movies 250 --min-year 2020

# Enrich with box office/budget data from The Numbers (rate-limited scraper)
ayne numbers enrich --max-movies 50 --min-year 2020

# Daily updates: refresh recent releases only
ayne tmdb refresh --min-year 2024 --limit 1000
ayne omdb refresh --min-year 2024 --limit 300

# Run daily refresh workflow
ayne collect daily --tmdb-refresh 50 --omdb-limit 30

# Run full collection workflow
ayne collect full --max-tmdb 5000 --max-omdb 1000
```

**Command Structure:**

- **`tmdb update`** - Discover new movies (basic info: title, date, TMDB ID)
- **`tmdb enrich`** - Fetch detailed data (budget, revenue, genres, IMDb ID)
- **`tmdb refresh`** - Update existing movies that need refresh
- **`omdb enrich`** - Add OMDB data to movies with IMDb IDs
- **`omdb refresh`** - Update existing OMDB data
- **`numbers enrich`** - Add box office/budget data from The Numbers (conservatively rate-limited to avoid overloading their site)

**Features**:

- **Automatic year-range splitting** - Handles TMDB's 500-page limit transparently
- Year filtering (`--min-year`, `--max-year`) for targeted collection
- Age-based refresh intervals (5-180 days based on movie age)
- Concurrent API calls with rate limiting
- Automatic data freezing for stable movies
- Smart refresh decisions to minimize API calls
- Dry-run mode for safe previews (`--dry-run`)

### Starting From an Empty Database

If `data/db/movies.duckdb` doesn't exist yet or you're setting up a fresh environment:

```bash
# 1. Create the schema
ayne db init

# 2. Discover movies (populates the `movies` table with basic TMDB info)
ayne tmdb update --min-year 1990 --max-year 2024

# 3. Enrich with detailed TMDB data (budget, revenue, genres, IMDb ID)
ayne tmdb enrich --limit 5000

# 4. Enrich with OMDB data (ratings, awards) - requires imdb_id from step 3
ayne omdb enrich --max-movies 5000

# 5. (Optional, slow) Enrich with box office data from The Numbers
ayne numbers enrich --max-movies 500

# 6. Confirm everything landed correctly
ayne db stats
ayne validate all
```

### Daily Commands

Keep recent releases current without re-scanning the whole catalog:

```bash
ayne tmdb refresh --min-year 2024 --limit 1000
ayne omdb refresh --min-year 2024 --limit 300
ayne numbers enrich --max-movies 50
```

Or run the equivalent orchestrated workflow in one step:

```bash
ayne collect daily --tmdb-refresh 50 --omdb-limit 30
```

### Weekly Commands

Broader refresh across a wider year range, plus discovery of anything new:

```bash
ayne tmdb update --min-year 2020 --max-year 2024
ayne tmdb refresh --min-year 2020 --limit 2000
ayne omdb refresh --min-year 2020 --limit 1000
ayne numbers enrich --max-movies 200
ayne validate all
```

### Working with the Database

The project uses DuckDB for analytical queries:

```python
from ayne.utils.query_utils import load_full_dataset, get_movies_with_financials

# Load all movie data (joins all tables automatically)
df = load_full_dataset()
print(f"Loaded {len(df)} movies")

# Get movies with financial data
df_financial = get_movies_with_financials(min_budget=1_000_000)

# Custom queries
from ayne.utils.query_utils import execute_custom_query
query = """
    SELECT genre_names, COUNT(*) as count, AVG(revenue) as avg_revenue
    FROM movies m
    INNER JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
    GROUP BY genre_names
    ORDER BY count DESC
"""
df = execute_custom_query(query)
```

**Database Tables**:

- `movies` - Core movie information with identifiers
- `tmdb_movies` - TMDB data (budget, revenue, genres, ratings)
- `omdb_movies` - OMDB data (cast, crew, reviews, awards)
- `numbers_movies` - Financial data from The Numbers

### Validate Data Quality

Run validation checks on your data:

```bash
# Validate TMDB data
ayne validate tmdb --verbose

# Validate OMDB/IMDb data
ayne validate imdb

# Run all validations
ayne validate all
```

### View Configuration

Check current settings:

```bash
# Show version and environment
ayne version

# Show all configuration settings
ayne config
```

See the [CLI Guide](docs/guides/cli-guide.md) for complete documentation.

Start exploring the data:

```bash
jupyter lab notebooks/
```

### Jupyter Notebooks

- `01_movies_data_full_imputation.ipynb` - Data preprocessing and imputation
- More analysis notebooks coming soon...

**Notebook Usage**:

```python
import os
from pyprojroot import here
os.chdir(here())

from ayne.utils.query_utils import load_full_dataset, save_processed_data

# Load from database
data = load_full_dataset()

# After preprocessing
save_processed_data(df_clean, "movies_preprocessed", format="parquet")
```

## 📁 Project Structure

```text
Are-You-Not-Entertained/
├── src/
│   └── ayne/                 # Main package
│       ├── core/             # Configuration, logging, exceptions
│       ├── utils/            # Data utilities and I/O
│       │   └── query_utils.py  # Database query helpers
│       ├── data_collection/  # API clients and orchestration
│       │   ├── tmdb/        # TMDB client
│       │   ├── omdb/        # OMDB client
│       │   ├── the_numbers/ # The Numbers scraper
│       │   ├── rate_limiter.py     # Shared rate limiting
│       │   ├── refresh_strategy.py # Intelligent refresh logic
│       │   └── orchestrator.py     # Collection coordinator
│       ├── database/         # DuckDB client
│       ├── ml/              # ML models (coming soon)
│       ├── api/             # REST API (coming soon)
│       ├── cli/             # CLI interface (coming soon)
│       └── web/             # Web interface (coming soon)
├── data/
│   ├── db/                   # DuckDB database files
│   ├── raw/                  # Immutable source data
│   ├── processed/            # Analysis-ready data
│   └── artifacts/            # Model outputs (coming soon)
├── notebooks/                # Jupyter analysis notebooks
├── scripts/                  # Utility scripts
└── configs/                  # Environment-specific configs
```

## 🔧 Configuration

The project uses environment-specific YAML configs and `.env` for sensitive data:

```text
configs/
├── development.yaml          # Local development
├── staging.yaml             # Testing environment
└── production.yaml          # Production settings
```

Set environment with:

```bash
export ENVIRONMENT=development  # or staging, production
```

Configuration is managed via Pydantic:

```python
from ayne.core.config import settings

print(settings.duckdb_path)        # Database location
print(settings.data_processed_dir) # Processed data directory
print(settings.tmdb_api_key)      # API keys (from .env)
```

## 📊 Database Schema

### Core Tables

#### Movies

- Primary identifiers: `movie_id`, `tmdb_id`, `imdb_id`
- Basic info: `title`, `release_date`
- Refresh tracking: `last_tmdb_update`, `last_omdb_update`, `data_frozen`

#### TMDB Movies

- Financial: `budget`, `revenue`
- Ratings: `vote_average`, `vote_count`, `popularity`
- Metadata: `genres`, `production_companies`, `production_countries`, `overview`

#### OMDB Movies

- Cast & Crew: `director`, `writer`, `actors`
- Ratings: `imdb_rating`, `rotten_tomatoes_rating`, `metascore`
- Details: `awards`, `genre`, `runtime`, `language`

#### Numbers Movies

- Financial: `production_budget`, `domestic_box_office`, `worldwide_box_office`

## 📚 Documentation

Full documentation lives under [docs/](docs/) (built with MkDocs) - see [Architecture](docs/reference/architecture.md), [CLI Guide](docs/guides/cli-guide.md), and [Technical Decisions](docs/reference/technical-decisions.md) to start. Also see [data/README.md](data/README.md) for a data directory quick reference.

## 🎯 Roadmap

### Current Phase: Data Foundation ✅

- [x] Automated data collection with refresh strategies
- [x] DuckDB database with normalized schema
- [x] Query utilities for analysis
- [x] Modern Python project structure

### Next Phase: Analysis & Modeling 🚧

- [ ] Feature engineering pipeline
- [ ] Exploratory data analysis notebooks
- [ ] Revenue prediction models (XGBoost, Random Forest)
- [ ] Model evaluation and comparison
- [ ] Cross-validation and hyperparameter tuning

### Future Phase: API & Deployment 📋

- [ ] REST API for movie metrics
- [ ] Model serving endpoints
- [ ] Performance monitoring dashboard
- [ ] Automated model retraining
- [ ] Docker deployment setup

## 🧪 Testing

The project has a minimal but meaningful unit test suite (pure-function tests for refresh logic, parsing, and API usage tracking), run automatically in CI:

```bash
# Run unit tests with coverage
uv run pytest

# Test database connection
ayne db test

# Validate data quality
ayne validate all
```

## 📈 Performance

**Data Collection**:

- 5-8x faster than previous sync approach
- 50 movies: ~5 seconds (async) vs ~30-40 seconds (sync)
- Rate limiting prevents API blocks
- Intelligent refresh reduces unnecessary calls

**Database Queries**:

- DuckDB ~10x faster than CSV loading for analytics
- Columnar storage optimized for aggregations
- Automatic indexing on primary keys

**Storage**:

- Parquet format: 70% smaller than CSV
- Efficient compression and type preservation

## 🔑 API Keys

Get free API keys from:

- **TMDB**: [TMDB API](https://www.themoviedb.org/settings/api)
- **OMDB**: [OMDB API](https://www.omdbapi.com/)

Add to `.env`:

```bash
TMDB_API_KEY=your_tmdb_api_key_here
OMDB_API_KEY=your_omdb_api_key_here
```

## 🤝 Contributing

This is a personal portfolio project, but suggestions and feedback are welcome! Feel free to open issues or fork for your own learning.

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

## 🎓 Learning Outcomes

This project demonstrates:

- ✨ Modern async Python patterns and best practices
- ✨ Database-centric data architecture with DuckDB
- ✨ Type-safe configuration with Pydantic
- ✨ Efficient API integration with rate limiting
- ✨ Clean code organization and documentation
- ✨ Production-ready project structure

---

**Last Updated**: November 2024 | **Status**: 🚀 Active Development
