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
   uv run python scripts/validate_notebook_setup.py
   ```

## 🚀 Quick Start

### Data Collection

Collect movie data with intelligent refresh strategies:

```bash
# Discover new movies from TMDB (2020-2024)
uv run python scripts/collect_optimized.py --discover --start-year 2020 --end-year 2024

# Refresh existing movies (updates based on age)
uv run python scripts/collect_optimized.py --refresh-only --refresh-limit 100

# Full collection workflow
uv run python scripts/collect_optimized.py
```

**Features**:
- Age-based refresh intervals (5-180 days based on movie age)
- Concurrent API calls with rate limiting
- Automatic data freezing for stable movies
- Smart refresh decisions to minimize API calls

### Working with the Database

The project uses DuckDB for analytical queries:

```python
from src.data.query_utils import load_full_dataset, get_movies_with_financials

# Load all movie data (joins all tables automatically)
df = load_full_dataset()
print(f"Loaded {len(df)} movies")

# Get movies with financial data
df_financial = get_movies_with_financials(min_budget=1_000_000)

# Custom queries
from src.data.query_utils import execute_custom_query
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

### Jupyter Notebooks

Start exploring the data:

```bash
jupyter lab notebooks/
```

**Available Notebooks**:
- `01_movies_data_full_imputation.ipynb` - Data preprocessing and imputation
- More analysis notebooks coming soon...

**Notebook Usage**:
```python
import os
from pyprojroot import here
os.chdir(here())

from src.data.query_utils import load_full_dataset, save_processed_data

# Load from database
data = load_full_dataset()

# After preprocessing
save_processed_data(df_clean, "movies_preprocessed", format="parquet")
```

## 📁 Project Structure

```
Are-You-Not-Entertained/
├── src/
│   ├── core/                 # Configuration, logging, paths
│   ├── data/                 # Data utilities and I/O
│   │   └── query_utils.py   # Database query helpers
│   ├── data_collection/      # API clients and orchestration
│   │   ├── tmdb/            # TMDB client
│   │   ├── omdb/            # OMDB client
│   │   ├── rate_limiter.py  # Shared rate limiting
│   │   ├── refresh_strategy.py  # Intelligent refresh logic
│   │   └── orchestrator.py  # Collection coordinator
│   ├── database/             # DuckDB client
│   ├── features/             # Feature engineering (coming soon)
│   └── models/               # ML models (coming soon)
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

```
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
from src.core.config import settings

print(settings.duckdb_path)        # Database location
print(settings.data_processed_dir) # Processed data directory
print(settings.tmdb_api_key)      # API keys (from .env)
```

## 📊 Database Schema

### Core Tables

**movies**
- Primary identifiers: `movie_id`, `tmdb_id`, `imdb_id`
- Basic info: `title`, `release_date`
- Refresh tracking: `last_tmdb_update`, `last_omdb_update`, `data_frozen`

**tmdb_movies**
- Financial: `budget`, `revenue`
- Ratings: `vote_average`, `vote_count`, `popularity`
- Metadata: `genres`, `production_companies`, `production_countries`, `overview`

**omdb_movies**
- Cast & Crew: `director`, `writer`, `actors`
- Ratings: `imdb_rating`, `rotten_tomatoes_rating`, `metascore`
- Details: `awards`, `genre`, `runtime`, `language`

**numbers_movies**
- Financial: `production_budget`, `domestic_box_office`, `worldwide_box_office`

## 📚 Documentation

- **[DATA_GUIDE.md](DATA_GUIDE.md)** - Comprehensive data structure guide
- **[DATA_MODERNIZATION_SUMMARY.md](DATA_MODERNIZATION_SUMMARY.md)** - Recent architecture changes
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - Code refactoring details
- **[data/README.md](data/README.md)** - Data directory quick reference

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

Run tests with pytest:
```bash
# Test database connection
uv run python scripts/test_database.py

# Test query utilities
uv run python scripts/test_query_utils.py

# Validate notebook setup
uv run python scripts/validate_notebook_setup.py
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
