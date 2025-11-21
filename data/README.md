# Data Directory

This directory contains all data for the "Are You Not Entertained" movie analysis project.

## Structure

```
data/
├── db/          # DuckDB database files
├── raw/         # Raw, immutable data from APIs
├── processed/   # Cleaned, analysis-ready data (Parquet)
└── artifacts/   # Model outputs and predictions (Parquet)
```

## Database

**Location**: `db/movies.duckdb`

**Tables**:
- `movies` - Core movie information
- `tmdb_movies` - TMDB API data
- `omdb_movies` - OMDB API data  
- `numbers_movies` - The Numbers financial data
- `movie_refresh_state` - Data refresh tracking

## Usage

### In Notebooks
```python
from src.data.query_utils import load_full_dataset

# Load all movie data
df = load_full_dataset()
```

### See Also
- **Complete Guide**: `../DATA_GUIDE.md`
- **Query Utilities**: `../src/data/query_utils.py`
- **Example Notebook**: `../notebooks/01_movies_data_full_imputation.ipynb`

## Important Notes

⚠️ **Never commit large data files to git!**
- Database files are in `.gitignore`
- Raw API responses are in `.gitignore`
- Processed data should be regenerated from database

✅ **Use Parquet format** for processed data (faster, smaller than CSV)

✅ **Raw data is immutable** - never modify files in `raw/`
