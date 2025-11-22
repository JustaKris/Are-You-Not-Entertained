# Quick Start: Using the Refactored AYNE Package

This guide helps you get started with the newly refactored `ayne` package.

---

## ⚡ Quick Installation

```bash
# 1. Navigate to project root
cd d:/Programming/Repositories/Are-You-Not-Entertained

# 2. Install the package in development mode
uv pip install -e .

# 3. Verify installation
python -c "from ayne import settings, get_logger; print('✅ Package installed successfully!')"
```

---

## 📦 New Import Pattern

### Before (Old)

```python
from src.core.config import settings
from src.data_collection.orchestrator import DataCollectionOrchestrator
from src.database.duckdb_client import DuckDBClient
```

### After (New)

```python
from ayne.core.config import settings
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.database.duckdb_client import DuckDBClient
```

### Convenient Top-Level Imports

```python
# Most common imports available at top level
from ayne import settings, get_logger, configure_logging

# Initialize logger
logger = get_logger(__name__)
logger.info("Using new package structure!")
```

---

## 🚀 Running Scripts

All scripts have been updated to use the new package structure:

```bash
# Initialize database
uv run python scripts/init_database.py

# Test database connection
uv run python scripts/test_database.py

# Collect movie data
uv run python scripts/collect_optimized.py --start-year 2024

# Test query utilities
uv run python scripts/test_query_utils.py

# Validate notebook setup
uv run python scripts/validate_notebook_setup.py
```

---

## 📓 Using in Notebooks

Update your notebook imports:

```python
# Cell 1: Setup
import os
from pyprojroot import here
os.chdir(here())

# Cell 2: Imports (NEW PATTERN)
from ayne.utils.query_utils import load_full_dataset, get_movies_with_financials
from ayne.core.config import settings

# Cell 3: Load data
df = load_full_dataset()
print(f"✅ Loaded {len(df)} movies from {settings.duckdb_path}")

# Cell 4: Work with data
df_financial = get_movies_with_financials(min_budget=1_000_000)
print(f"Found {len(df_financial)} movies with budget >= $1M")
```

---

## 🛠️ Common Tasks

### Initialize Database

```python
from ayne.database.duckdb_client import DuckDBClient
from ayne.core.logging import configure_logging, get_logger

configure_logging(level="INFO")
logger = get_logger(__name__)

db = DuckDBClient()
db.create_tables_from_sql()
logger.info("✅ Database initialized!")
```

### Collect Movie Data

```python
import asyncio
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.database.duckdb_client import DuckDBClient

async def collect_data():
    db = DuckDBClient()
    orchestrator = DataCollectionOrchestrator(db)
    
    stats = await orchestrator.run_full_collection(
        discover_start_year=2024,
        refresh_limit=50
    )
    
    print(f"✅ Collected: {stats}")
    await orchestrator.close()
    db.close()

# Run it
asyncio.run(collect_data())
```

### Query Movie Data

```python
from ayne.utils.query_utils import load_full_dataset
from ayne.database.duckdb_client import DuckDBClient

# Option 1: Use query utilities (recommended for notebooks)
df = load_full_dataset()

# Option 2: Use DuckDB client directly
db = DuckDBClient()
df = db.query("""
    SELECT m.title, t.revenue, t.budget
    FROM movies m
    JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
    WHERE t.revenue > 100000000
    ORDER BY t.revenue DESC
    LIMIT 10
""")
print(df)
db.close()
```

---

## 🔍 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'ayne'"

**Solution**: Install the package in development mode:

```bash
uv pip install -e .
```

### Problem: "ImportError: cannot import name 'settings'"

**Solution**: Make sure you're using the new import pattern:

```python
# ✅ Correct
from ayne.core.config import settings

# ❌ Incorrect (old pattern)
from src.core.config import settings
```

### Problem: Scripts fail with import errors

**Solution**: The scripts have been updated. Pull the latest changes:

```bash
git pull origin main
```

### Problem: Notebooks still using old imports

**Solution**: Update your notebook cells:

1. Find: `from src.`
2. Replace: `from ayne.`
3. Restart kernel and run all cells

---

## 📋 Quick Reference Card

### Most Common Imports

```python
# Configuration
from ayne.core.config import settings

# Logging
from ayne.core.logging import configure_logging, get_logger

# Database
from ayne.database.duckdb_client import DuckDBClient

# Data Collection
from ayne.data_collection import TMDBClient, OMDBClient
from ayne.data_collection.orchestrator import DataCollectionOrchestrator

# Utilities
from ayne.utils.query_utils import (
    load_full_dataset,
    get_movies_with_financials,
    save_processed_data
)
```

### Most Used Commands

```bash
# Install/Update package
uv pip install -e .

# Run scripts
uv run python scripts/init_database.py
uv run python scripts/collect_optimized.py

# Start Jupyter
jupyter lab notebooks/

# Run tests (when available)
uv run pytest tests/

# Lint code
uv run ruff check src/ scripts/
uv run black src/ scripts/
```

---

## 🎯 What's Different?

| Aspect | Before | After |
|--------|--------|-------|
| **Package name** | `AYNE` (uppercase) | `ayne` (lowercase) |
| **Import prefix** | `from src.` | `from ayne.` |
| **Structure** | Flat `src/` folder | Proper `src/ayne/` package |
| **Distribution** | Not distributable | Ready for PyPI |
| **IDE support** | Limited | Full autocomplete |

---

## ✅ Migration Checklist

For your existing notebooks and scripts:

- [ ] Update imports: `from src.` → `from ayne.`
- [ ] Reinstall package: `uv pip install -e .`
- [ ] Test notebook imports
- [ ] Run scripts to verify they work
- [ ] Update any personal documentation

---

## 🎓 Learn More

- **Full Documentation**: See `docs/copilot_artifacts/PACKAGE_REFACTORING_SUMMARY.md`
- **Project Structure**: See updated `README.md`
- **Configuration Guide**: See `docs/copilot_artifacts/CONFIG_QUICKSTART.md`

---

**Need Help?** Check the documentation or the error message - they now point to the correct `ayne` package structure!

✅ **You're all set!** Happy coding with the new package structure.
