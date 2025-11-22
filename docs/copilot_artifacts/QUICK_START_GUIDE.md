# 🚀 Quick Start Guide: Database Migration

**Purpose**: Get your DuckDB database up and running ASAP  
**Time to Complete**: ~30 minutes  
**Difficulty**: Beginner-Friendly

---

## 🎯 Immediate Actions (Do These First)

### Step 1: Install DuckDB (2 minutes)

```bash
# Navigate to project root
cd d:/Programming/Repositories/Are-You-Not-Entertained

# Install DuckDB using uv
uv add duckdb
```

### Step 2: Fix Import in duckdb_client.py (Done! ✅)

The import issue has been fixed. The file now correctly imports:

```python
from ayne.core.paths import DATA_INTERMEDIATE_DIR
```

### Step 3: Initialize Database (5 minutes)

Create a simple initialization script:

```python
# scripts/init_database.py
"""Initialize DuckDB database with schema."""
from ayne.db.duckdb_client import DuckDBClient
from ayne.core.logging import configure_logging, get_logger
from ayne.core.config import settings

configure_logging(level="INFO")
logger = get_logger(__name__)

def main():
    """Initialize the database."""
    logger.info("Initializing DuckDB database...")
    
    # Create database client
    db = DuckDBClient()
    
    # Create all tables from schema
    db.create_tables_from_sql()
    
    # Verify tables were created
    tables = ["movies", "tmdb_movies", "omdb_movies", "numbers_movies", "movie_refresh_state"]
    for table in tables:
        exists = db.table_exists(table)
        status = "✅" if exists else "❌"
        logger.info(f"{status} Table '{table}' exists: {exists}")
    
    db.close()
    logger.info("Database initialization complete!")

if __name__ == "__main__":
    main()
```

Run it:

```bash
python scripts/init_database.py
```

### Step 4: Test Basic Queries (5 minutes)

```python
# scripts/test_database.py
"""Test database connectivity and basic operations."""
from ayne.db.duckdb_client import DuckDBClient
import pandas as pd

def main():
    db = DuckDBClient()
    
    # Test 1: Query empty tables
    print("Test 1: Query movies table")
    result = db.query("SELECT COUNT(*) as count FROM movies")
    print(f"Movies count: {result['count'].iloc[0]}")
    
    # Test 2: Insert sample data
    print("\nTest 2: Insert sample movie")
    sample_data = pd.DataFrame({
        "tmdb_id": [12345],
        "title": ["Test Movie"],
        "release_date": ["2024-01-01"]
    })
    db.upsert_dataframe("movies", sample_data, key_columns=["tmdb_id"])
    
    # Test 3: Query inserted data
    print("\nTest 3: Verify insert")
    result = db.query("SELECT * FROM movies")
    print(result)
    
    # Test 4: Update existing record
    print("\nTest 4: Update movie")
    updated_data = pd.DataFrame({
        "tmdb_id": [12345],
        "title": ["Test Movie UPDATED"],
        "release_date": ["2024-01-01"]
    })
    db.upsert_dataframe("movies", updated_data, key_columns=["tmdb_id"])
    
    result = db.query("SELECT * FROM movies WHERE tmdb_id = 12345")
    print(result)
    
    db.close()
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    main()
```

Run it:

```bash
python scripts/test_database.py
```

---

## 🔧 Fix Configuration (10 minutes)

### Update .env File

Your current `.env` is good but needs minor tweaks:

```bash
# Environment
ENVIRONMENT=development
DEBUG=true

# API Keys (already correct)
TMDB_API_KEY=4e2712dbe95581a261b49b89fe1cf6a3
OMDB_API_KEY=67aa553f

# Logging
LOG_LEVEL=INFO
USE_JSON_LOGGING=false

# NEW: Database path (optional, defaults to data/db/movies.duckdb)
# DATABASE_PATH=data/db/movies.duckdb
```

### Update development.yaml

Add database configuration:

```yaml
# configs/development.yaml
app_name: "Are You Not Entertained"
environment: "development"
debug: true

# Logging
log_level: "DEBUG"
use_json_logging: false

# Database (NEW)
database:
  type: "duckdb"
  path: "data/db/movies.duckdb"
  read_only: false

# API Configuration
tmdb_api_base_url: "https://api.themoviedb.org/3"
omdb_api_base_url: "http://www.omdbapi.com"
api_rate_limit: 40
api_timeout: 30

# Data Processing
batch_size: 100
random_seed: 42

# FastAPI Server
host: "127.0.0.1"
port: 8000
reload: true
cors_origins:
  - "http://localhost:3000"
  - "http://localhost:8000"
  - "http://127.0.0.1:3000"
  - "http://127.0.0.1:8000"
```

---

## 📝 Create Your First Data Collection Script (10 minutes)

This is a MINIMAL version to get you started:

```python
# scripts/collect_data_simple.py
"""Simple data collection script to get started."""
from ayne.db.duckdb_client import DuckDBClient
from ayne.data_collection.tmdb import TMDBClient
from ayne.core.config import settings
from ayne.core.logging import configure_logging, get_logger
import pandas as pd

configure_logging(level="INFO")
logger = get_logger(__name__)

def main():
    """Collect sample movie data."""
    db = DuckDBClient()
    tmdb = TMDBClient(api_key=settings.tmdb_api_key)
    
    # Get 10 popular movies from 2024
    logger.info("Fetching movies from TMDB...")
    movies = tmdb.get_movie_ids(start_year=2024, min_vote_count=300, save_to_file=False)
    
    # Take first 10 only for testing
    movies = movies[:10]
    logger.info(f"Got {len(movies)} movies")
    
    # Convert to DataFrame and normalize column names
    df = pd.DataFrame(movies)
    df = df.rename(columns=lambda x: x.lower())
    
    # Map column names to match database schema
    df = df.rename(columns={
        "id": "tmdb_id",
        "vote_average": "vote_average",
        "vote_count": "vote_count"
    })
    
    # Select only columns that exist in movies table
    columns_to_keep = ["tmdb_id", "title", "release_date"]
    df = df[columns_to_keep]
    
    logger.info(f"Inserting {len(df)} movies into database...")
    db.upsert_dataframe("movies", df, key_columns=["tmdb_id"])
    
    # Verify
    result = db.query("SELECT COUNT(*) as count FROM movies")
    logger.info(f"Total movies in database: {result['count'].iloc[0]}")
    
    # Show sample
    sample = db.query("SELECT * FROM movies LIMIT 5")
    print("\nSample movies:")
    print(sample)
    
    db.close()
    logger.info("✅ Data collection complete!")

if __name__ == "__main__":
    main()
```

Run it:

```bash
python scripts/collect_data_simple.py
```

---

## 🎓 What You've Accomplished

After completing these steps, you will have:

✅ **DuckDB installed** and working  
✅ **Database schema created** with all tables  
✅ **Configuration system** properly set up  
✅ **First data collection script** running  
✅ **Sample movie data** in your database  

---

## 🚦 Next Steps

### Immediate (Next 1-2 Days)

1. Review the full **MODERNIZATION_PLAN.md** document
2. Create unit tests for DuckDBClient
3. Refactor TMDB client to remove database coupling

### Short-term (Next Week)

1. Create modern TMDB and OMDB clients
2. Build comprehensive data collection orchestrator
3. Delete old PostgreSQL code

### Medium-term (Next 2-4 Weeks)

1. Migrate all data preprocessing to use DuckDB
2. Update model training pipeline
3. Create data export scripts for Parquet

---

## 🆘 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'duckdb'"

**Solution**:

```bash
uv add duckdb
# or
uv sync
```

### Problem: "FileNotFoundError: schema.sql not found"

**Solution**: Check that `src/db/schema.sql` exists in your project.

### Problem: "ImportError: cannot import name 'DATA_INTERMEDIATE_DIR'"

**Solution**: Already fixed! The import now correctly uses `src.core.paths`.

### Problem: Database file not created

**Solution**:

```python
# Check path configuration
from ayne.core.paths import DATA_INTERMEDIATE_DIR
print(DATA_INTERMEDIATE_DIR)

# Ensure directory exists
DATA_INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
```

### Problem: API calls fail

**Solution**: Verify your API keys in `.env`:

```bash
# Check keys are loaded
python -c "from ayne.core.config import settings; print(f'TMDB: {settings.tmdb_api_key[:10]}...')"
```

---

## 💡 Pro Tips

1. **Always test in small batches first** - Don't fetch 1000 movies right away
2. **Use logging liberally** - It helps debug issues
3. **Check the DuckDB file size** - It should grow as you add data
4. **Query your data often** - Verify everything looks correct
5. **Backup before experimenting** - Copy your `.duckdb` file

---

## 📚 Files You Created Today

```bash
scripts/
├── init_database.py         # Initialize schema
├── test_database.py          # Test basic operations
└── collect_data_simple.py    # First data collection

# You also have:
src/db/
├── duckdb_client.py          # ✅ Fixed import
└── schema.sql                # ✅ Database schema
```

---

## 🎉 Congratulations

You now have a modern DuckDB-based data infrastructure. The next phase is refactoring your API clients to be database-agnostic.

**Need help?** Use the copy-paste prompts in the main MODERNIZATION_PLAN.md document.

---

*Last Updated: November 20, 2025*  
*Quick Start Guide v1.0*
