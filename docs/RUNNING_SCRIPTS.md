# Running Scripts Guide

## Quick Start

### Windows (PowerShell)
```powershell
# Option 1: Use the helper batch file (recommended)
.\run.bat test_database
.\run.bat init_database
.\run.bat collect_omdb_data --limit 5
.\run.bat collect_tmdb_data --start-year 2024

# Option 2: Use uv run directly
uv run python scripts/test_database.py
uv run python scripts/collect_omdb_data.py --limit 5

# Option 3: Activate virtual environment first
.\.venv\Scripts\Activate.ps1
python scripts/test_database.py
python scripts/collect_omdb_data.py --limit 5
```

### Linux/Mac (Bash)
```bash
# Option 1: Use the helper script (recommended)
./run.sh test_database
./run.sh init_database
./run.sh collect_omdb_data --limit 5

# Option 2: Use uv run directly
uv run python scripts/test_database.py
uv run python scripts/collect_omdb_data.py --limit 5

# Option 3: Activate virtual environment first
source .venv/bin/activate
python scripts/test_database.py
python scripts/collect_omdb_data.py --limit 5
```

## Available Scripts

### 1. test_database.py
Test that DuckDB setup works correctly.

```powershell
.\run.bat test_database
```

### 2. init_database.py
Initialize database schema (creates all tables).

```powershell
.\run.bat init_database
```

### 3. collect_tmdb_data.py
Collect movie data from TMDB API.

```powershell
# Basic usage
.\run.bat collect_tmdb_data

# With options
.\run.bat collect_tmdb_data --start-year 2020 --end-year 2024 --min-votes 200
```

**Options:**
- `--start-year`: Starting year (default: 2020)
- `--end-year`: Ending year (default: 2024)
- `--min-votes`: Minimum vote count (default: 200)
- `--max-pages`: Maximum pages per year (default: unlimited)
- `--details-limit`: Movies to get details for (default: 50)
- `--skip-basic`: Skip basic collection
- `--skip-details`: Skip details collection

### 4. collect_omdb_data.py
Collect rating data from OMDB API.

```powershell
# Basic usage
.\run.bat collect_omdb_data

# With limit
.\run.bat collect_omdb_data --limit 100
```

**Options:**
- `--limit`: Maximum movies to process (default: 100)

### 5. collect_all_data.py
Master script - runs complete collection workflow.

```powershell
.\run.bat collect_all_data
```

This script automatically:
1. Discovers movies from TMDB
2. Gets detailed TMDB features
3. Gets OMDB ratings

## Why Use `uv run`?

The `uv run` command:
- ✅ Automatically uses the correct virtual environment
- ✅ Ensures all dependencies are installed
- ✅ Sets up the Python path correctly
- ✅ Works consistently across all platforms

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'src'"

**Solution:** Use `uv run` or the helper scripts (`run.bat` / `run.sh`).

**Why it happens:** When you run `python scripts/collect_omdb_data.py` directly, Python doesn't know about your project structure or virtual environment.

### Error: "ModuleNotFoundError: No module named 'duckdb'"

**Solution:** Your dependencies aren't installed. Run:
```powershell
uv sync
```

### Error: "ValueError: TMDB API key is required"

**Solution:** Set up your `.env` file with API keys:
```bash
TMDB_API_KEY=your_tmdb_key_here
OMDB_API_KEY=your_omdb_key_here
```

### Scripts run but show red highlights in VS Code

This is normal! VS Code's linter (Pylance) can't always detect Pydantic's dynamic attributes like `settings.data_raw_dir` at static analysis time. The `# type: ignore` comments suppress these warnings, and the code runs perfectly fine.

## Complete Workflow Example

```powershell
# 1. Install dependencies (first time only)
uv sync

# 2. Set up .env file with API keys
# Edit .env and add your TMDB_API_KEY and OMDB_API_KEY

# 3. Test database setup
.\run.bat test_database

# 4. Initialize database
.\run.bat init_database

# 5. Collect data
.\run.bat collect_all_data

# Or collect step by step:
.\run.bat collect_tmdb_data --start-year 2023 --end-year 2024
.\run.bat collect_omdb_data --limit 50
```

## Environment Variables

You can override any setting via environment variables:

```powershell
# Windows PowerShell
$env:LOG_LEVEL="DEBUG"
$env:DATA_INTERMEDIATE_DIR="./custom_data"
.\run.bat test_database

# Linux/Mac
export LOG_LEVEL="DEBUG"
export DATA_INTERMEDIATE_DIR="./custom_data"
./run.sh test_database
```

## Advanced: Module Execution

You can also run scripts as modules (requires activated environment):

```powershell
# Activate environment first
.\.venv\Scripts\Activate.ps1

# Run as module
python -m scripts.test_database
python -m scripts.collect_omdb_data --limit 5
```

## Summary

**Recommended approach:**
```powershell
# Windows
.\run.bat <script_name> [options]

# Linux/Mac
./run.sh <script_name> [options]
```

This handles everything automatically! 🚀
