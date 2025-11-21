# Are You Not Entertained?

> A modern data science project for movie box office analysis and prediction, built with production-grade Python practices.

## Overview

**Are You Not Entertained?** (AYNE) analyzes movie performance using data from multiple sources (TMDB, OMDB, The Numbers). The project features automated data collection, a DuckDB database for efficient analytics, and prepares the groundwork for predictive modeling pipelines.

## Key Features

### ✅ Current Features

- **Automated Data Collection**: Async API clients with intelligent refresh strategies
- **Database-Centric Architecture**: DuckDB for fast analytical queries
- **Modern Python Practices**: Type hints, Pydantic settings, structured logging
- **Data Analysis Ready**: Query utilities for Jupyter notebooks
- **Optimized Performance**: 5-8x faster collection with rate limiting and caching

### 🚧 Coming Soon

- **Predictive Modeling**: Revenue forecasting and success prediction models
- **Analysis Notebooks**: Genre trends, director performance, temporal patterns
- **REST API**: Single movie performance metrics and analysis endpoints

## Tech Stack

- **Python 3.12+** with modern async/await patterns
- **DuckDB** for analytical database
- **httpx** for async HTTP requests
- **Pydantic** for configuration management
- **pandas** for data manipulation
- **Jupyter** for exploratory analysis

## Quick Links

- [Architecture Overview](reference/architecture.md)
- [Development Guides](development/code-style.md)
- [GitHub Repository](https://github.com/JustaKris/Are-You-Not-Entertained)

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- API keys for TMDB and OMDB

### Installation

```bash
# Clone repository
git clone https://github.com/JustaKris/Are-You-Not-Entertained.git
cd Are-You-Not-Entertained

# Install dependencies
uv venv
uv pip install -e "."

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

```bash
# Discover movies from 2020-2024
uv run python scripts/collect_optimized.py --start-year 2020 --end-year 2024

# Refresh existing movies
uv run python scripts/collect_optimized.py --refresh-only --refresh-limit 100
```

## Project Structure

```
Are-You-Not-Entertained/
├── src/
│   ├── core/              # Core utilities (config, logging)
│   ├── data_collection/   # API clients and data collection
│   ├── database/          # DuckDB client and schema
│   └── data/              # Query utilities
├── scripts/               # Executable scripts
├── notebooks/             # Jupyter analysis notebooks
├── docs/                  # Documentation
└── tests/                 # Test suite
```

## Contributing

This is a personal learning project, but suggestions and feedback are welcome! Please check the development guides for code style and contribution guidelines.

## License

MIT License - see [LICENSE](https://github.com/JustaKris/Are-You-Not-Entertained/blob/main/LICENSE) file for details.
