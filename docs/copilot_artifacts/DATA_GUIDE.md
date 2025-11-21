# Data Directory Structure Guide

## Overview
This guide explains the modern data directory structure for the "Are You Not Entertained" project, following Python best practices for data science projects.

## Directory Structure

```
data/
├── db/                      # Database files (DuckDB)
│   └── movies.duckdb       # Main production database
├── raw/                     # Raw, immutable data from sources
│   ├── tmdb/               # TMDB API responses (parquet)
│   └── omdb/               # OMDB API responses (parquet)
├── processed/               # Cleaned, transformed data ready for analysis
│   └── *.parquet           # Preprocessed datasets for modeling
└── artifacts/               # Model outputs and predictions
    └── *.parquet           # Training sets, predictions, feature matrices
```

## Directory Purposes

### `data/db/` - Database Files
**Purpose**: Store database files separate from data files

**Contents**:
- `movies.duckdb` - Main DuckDB database with consolidated movie data
- **Tables**: `movies`, `tmdb_movies`, `omdb_movies`, `numbers_movies`, `movie_refresh_state`

**Best Practices**:
- ✅ Keep databases separate from CSV/Parquet files
- ✅ Use DuckDB for structured, queryable data
- ✅ Never manually edit database files
- ❌ Don't store large binary files here

**Access Pattern**:
```python
from src.data.query_utils import get_db_client

db = get_db_client(read_only=True)
df = db.query("SELECT * FROM movies LIMIT 100")
db.close()
```

### `data/raw/` - Raw Source Data
**Purpose**: Immutable data as received from external sources

**Contents**:
- `tmdb/` - TMDB API response data
- `omdb/` - OMDB API response data
- Parquet files from data collection scripts

**Best Practices**:
- ✅ Never modify files in this directory
- ✅ Use as source of truth for re-processing
- ✅ Store in efficient formats (Parquet > CSV)
- ❌ Don't store processed or cleaned data here
- ❌ Don't store temporary files here

**Access Pattern**:
```python
# Raw data is typically loaded into DuckDB
# For direct access:
import pandas as pd
df = pd.read_parquet("data/raw/tmdb/02_movie_features.parquet")
```

### `data/processed/` - Processed Data
**Purpose**: Cleaned, transformed data ready for analysis and modeling

**Contents**:
- Feature-engineered datasets
- Imputed data
- Analysis-ready tables
- Intermediate results from notebooks

**Best Practices**:
- ✅ Store reproducible transformations
- ✅ Document preprocessing steps in notebooks
- ✅ Use Parquet for large datasets (faster, smaller)
- ✅ Include version/date in filenames
- ❌ Don't store raw data here

**Naming Convention**:
- `movies_preprocessed_2024-11-21.parquet`
- `movies_with_financials.parquet`
- `movies_imputed_full.parquet`

**Access Pattern**:
```python
from src.data.query_utils import save_processed_data
import pandas as pd

# Save processed data
df_clean = preprocess_movies(df_raw)
save_processed_data(df_clean, "movies_preprocessed", format="parquet")

# Load processed data
df = pd.read_parquet("data/processed/movies_preprocessed.parquet")
```

### `data/artifacts/` - Model Artifacts
**Purpose**: Outputs from machine learning pipelines

**Contents**:
- Training/test splits (`X_train.parquet`, `y_train.parquet`)
- Model predictions
- Feature matrices
- Evaluation results

**Best Practices**:
- ✅ Store train/test splits for reproducibility
- ✅ Version artifacts with model versions
- ✅ Use Parquet for large feature matrices
- ✅ Keep artifacts tied to specific model runs
- ❌ Don't store model binaries here (use `models/`)

**Naming Convention**:
- `X_train_v1.parquet`, `X_test_v1.parquet`
- `y_train_v1.parquet`, `y_test_v1.parquet`
- `predictions_model_v2.parquet`

**Access Pattern**:
```python
from src.data.query_utils import save_artifacts
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Save artifacts
save_artifacts(X_train, "X_train", format="parquet")
save_artifacts(y_train, "y_train", format="parquet")

# Load artifacts
X_train = pd.read_parquet("data/artifacts/X_train.parquet")
```

## Database Schema

### `movies` - Main Movies Table
Core movie information with unique identifiers:
- `tmdb_id` - TMDB identifier
- `imdb_id` - IMDB identifier
- `title` - Movie title
- `release_date` - Release date
- `budget` - Production budget
- `revenue` - Box office revenue
- `last_tmdb_update` - Last refresh timestamp
- `last_omdb_update` - Last refresh timestamp
- `data_frozen` - Whether data is stable (no more updates)

### `tmdb_movies` - TMDB Data
Detailed information from The Movie Database:
- Movie details (overview, tagline, runtime, status)
- Vote statistics (average, count)
- Popularity metrics
- Genre, production company, country, languages

### `omdb_movies` - OMDB Data
Rich information from Open Movie Database:
- Ratings (IMDB, Rotten Tomatoes, Metacritic)
- Cast and crew (director, writer, actors)
- Awards and nominations
- Production details

### `numbers_movies` - The Numbers Data
Financial data from The Numbers:
- Production budget
- Domestic gross
- Worldwide gross

## Working with Data in Notebooks

### Setup (Cell 1)
```python
import os
from pyprojroot import here
os.chdir(here())

from src.data.query_utils import (
    load_full_dataset,
    get_movies_with_financials,
    save_processed_data,
    save_artifacts
)
```

### Load Data (Cell 2)
```python
# Load complete dataset with all joined tables
df = load_full_dataset(include_nulls=True)
print(f"Loaded {len(df)} movies")
df.info()
```

### Query Specific Data (Cell 3)
```python
# Get movies with financial data
df_financial = get_movies_with_financials(min_budget=1_000_000)
print(f"Found {len(df_financial)} movies with budget >= $1M")
```

### Save Processed Data (Cell 4)
```python
# After preprocessing
df_clean = preprocess_pipeline.transform(df)
save_processed_data(df_clean, "movies_preprocessed_2024-11-21", format="parquet")
```

### Save Model Artifacts (Cell 5)
```python
# After train/test split
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

save_artifacts(X_train, "X_train", format="parquet")
save_artifacts(X_test, "X_test", format="parquet")
save_artifacts(y_train, "y_train", format="parquet")
save_artifacts(y_test, "y_test", format="parquet")
```

## File Formats

### Parquet (Recommended)
**When to use**: Large datasets (> 10MB), production pipelines

**Advantages**:
- ✅ Columnar format (fast queries)
- ✅ Compressed (smaller files)
- ✅ Preserves data types
- ✅ Fast read/write

**Example**:
```python
df.to_parquet("data/processed/movies.parquet", index=False)
df = pd.read_parquet("data/processed/movies.parquet")
```

### CSV
**When to use**: Small datasets, human readability, external sharing

**Advantages**:
- ✅ Human-readable
- ✅ Universal compatibility
- ✅ Easy to version control (text)

**Disadvantages**:
- ❌ Larger file size
- ❌ Slower to read/write
- ❌ Type inference issues

**Example**:
```python
df.to_csv("data/processed/movies.csv", index=False)
df = pd.read_csv("data/processed/movies.csv")
```

### Feather
**When to use**: Fast Python/R interoperability

**Advantages**:
- ✅ Very fast read/write
- ✅ Preserves data types
- ✅ R compatibility

**Example**:
```python
df.to_feather("data/processed/movies.feather")
df = pd.read_feather("data/processed/movies.feather")
```

## Configuration

### Database Path
Configured in `src/core/config/settings.py`:
```python
duckdb_path = data_dir / "db" / "movies.duckdb"
```

### Data Directories
Auto-created by settings on import:
```python
from src.core.config import settings

print(settings.data_db_dir)        # data/db
print(settings.data_raw_dir)       # data/raw
print(settings.data_processed_dir) # data/processed
print(settings.data_artifacts_dir) # data/artifacts
```

## Migration from Old Structure

### Old Structure (Deprecated)
```
data/
├── intermediate/
│   └── movies.duckdb     # OLD LOCATION
├── raw/
│   └── 0_base_data.csv   # REMOVED
└── processed/
    └── *.csv             # REMOVED
```

### New Structure (Current)
```
data/
├── db/                   # NEW: Dedicated database directory
│   └── movies.duckdb
├── raw/
│   ├── tmdb/
│   └── omdb/
├── processed/            # For parquet files
└── artifacts/            # For model outputs
```

### What Changed
1. ✅ `movies.duckdb` moved from `intermediate/` to `db/`
2. ✅ Removed `0_base_data.csv` (now in DuckDB)
3. ✅ Removed old processed CSV files
4. ✅ Use Parquet instead of CSV for processed data
5. ✅ Separate `artifacts/` for model outputs

## Best Practices Summary

### DO ✅
- Use DuckDB for structured, queryable data
- Store processed data in Parquet format
- Use `query_utils.py` functions in notebooks
- Document data transformations
- Version processed datasets in filenames
- Keep raw data immutable
- Separate artifacts from processed data

### DON'T ❌
- Manually edit database files
- Store large CSV files (use Parquet)
- Modify files in `raw/`
- Mix raw and processed data
- Store temporary files in data directories
- Commit large data files to git (use .gitignore)

## Troubleshooting

### Database Connection Issues
```python
from src.data.query_utils import get_db_client

# Check database location
from src.core.config import settings
print(f"Database at: {settings.duckdb_path}")

# Test connection
db = get_db_client(read_only=True)
tables = db.query("SHOW TABLES")
print(tables)
db.close()
```

### Missing Data Directories
Directories are auto-created by settings. If missing:
```python
from src.core.config import settings

# Directories created automatically on import
print(settings.data_db_dir.exists())       # Should be True
print(settings.data_processed_dir.exists()) # Should be True
```

### Performance Tips
1. Use Parquet for large datasets (> 10MB)
2. Query only needed columns from DuckDB
3. Use `read_only=True` when possible
4. Close database connections after use
5. Use chunked processing for huge datasets

## References

- [DuckDB Documentation](https://duckdb.org/docs/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Parquet Format](https://parquet.apache.org/)
- Project Configuration: `src/core/config/settings.py`
- Query Utilities: `src/data/query_utils.py`
- Database Client: `src/database/duckdb_client.py`
