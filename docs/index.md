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

### Getting Started

- **[CLI Guide](guides/cli-guide.md)** - Complete command-line interface reference
- **[Quick Start Guide](guides/data-collection-quick-reference.md)** - Common data collection commands and workflows
- **[Pre-Commit Guide](guides/pre-commit-guide.md)** - Set up code quality tools

### Core Documentation

- **[Architecture Overview](reference/architecture.md)** - System design and components
- **[Data Collection Workflow](reference/data-collection-workflow.md)** - How data collection works
- **[Data Collection Filtering](reference/data-collection-filtering.md)** - Configure filters and collection limits
- **[Refresh Strategy](reference/refresh-strategy.md)** - Intelligent data refresh logic
- **[Database Monitoring](guides/database-monitoring.md)** - Monitor health and audit data quality
- **[Development Guides](development/code-style.md)** - Code style and best practices

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
# Initialize database
ayne db init

# Discover movies from TMDB
ayne tmdb update --max-movies 1000

# Enrich with OMDB data
ayne omdb update --max-movies 500

# Run daily refresh workflow
ayne collect daily

# Validate data quality
ayne validate all
```

See the [CLI Guide](guides/cli-guide.md) for complete documentation.

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
