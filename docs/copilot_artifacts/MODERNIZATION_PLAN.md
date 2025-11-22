# 🚀 Project Modernization Plan: Are You Not Entertained?

**Document Version**: 1.0  
**Last Updated**: November 20, 2025  
**Status**: Comprehensive Modernization Strategy

---

## 📋 Executive Summary

This document provides a complete modernization roadmap for transitioning your movie analytics ML project from a legacy PostgreSQL + CSV-based architecture to a modern, lightweight DuckDB-powered system following Python best practices.

### Current State
- ❌ PostgreSQL database (overkill for local analytics)
- ❌ CSV-based data storage scattered across directories
- ❌ SQLAlchemy ORM models for PostgreSQL
- ❌ Mixed old/new code patterns
- ❌ Outdated dependencies (dill, etc.)

### Target State
- ✅ DuckDB as lightweight analytical database
- ✅ Parquet files for efficient data storage
- ✅ Unified Pydantic configuration system
- ✅ Modern Python 3.11+ practices
- ✅ Clean separation of concerns
- ✅ Production-ready logging and error handling

---

## 🎯 Phase 1: Database Migration (PRIORITY)

### 1.1 Why DuckDB is the Right Choice ✅

**DuckDB is PERFECT for this project** for these reasons:

| Aspect | DuckDB | PostgreSQL | Verdict |
|--------|---------|------------|---------|
| **Setup Complexity** | Zero-config, single file | Requires server, users, ports | 🟢 DuckDB |
| **Analytical Queries** | Optimized for OLAP | Better for OLTP | 🟢 DuckDB |
| **Parquet Integration** | Native, blazing fast | Requires extensions | 🟢 DuckDB |
| **Local Development** | Perfect, no server | Overkill, requires setup | 🟢 DuckDB |
| **ML Pipeline Fit** | Designed for analytics | Designed for transactions | 🟢 DuckDB |
| **Deployment** | Embedded, portable | Separate service | 🟢 DuckDB |
| **Storage** | Columnar, compressed | Row-based | 🟢 DuckDB |

**Recommendation**: Stick with DuckDB. It's the modern standard for local analytical workloads.

### 1.2 Database Architecture

```
data/
├── db/
│   └── movies.duckdb          # Main DuckDB database file
├── raw/                        # Raw API responses (optional archival)
│   ├── tmdb/
│   └── omdb/
├── intermediate/               # Parquet files for staging
│   ├── tmdb_raw.parquet
│   ├── omdb_raw.parquet
│   └── numbers_raw.parquet
└── processed/                  # Final cleaned datasets
    ├── features_v1.parquet
    ├── X_train.parquet
    ├── X_test.parquet
    ├── y_train.parquet
    └── y_test.parquet
```

### 1.3 Migration Steps

#### Step 1: Update Database Configuration
```yaml
# configs/development.yaml
database:
  type: "duckdb"
  path: "data/db/movies.duckdb"
  
# Remove PostgreSQL settings
# db_url: "postgresql://..."  # DELETE THIS
```

#### Step 2: Initialize DuckDB Schema
```bash
# Run this to create all tables
python -c "from ayne.db.duckdb_client import DuckDBClient; db = DuckDBClient(); db.create_tables_from_sql()"
```

#### Step 3: Migrate Data Collection Scripts

**Create new data collection orchestrator:**

```python
# scripts/collect_data.py
"""
Modern data collection script using DuckDB.
Replaces: scripts/update_db.py
"""
from ayne.core.config import settings
from ayne.core.logging import configure_logging, get_logger
from ayne.db.duckdb_client import DuckDBClient
from ayne.data_collection.tmdb import TMDBClient
from ayne.data_collection.omdb import OMDBClient
import pandas as pd

configure_logging(level=settings.log_level, use_json=settings.use_json_logging)
logger = get_logger(__name__)

def main():
    """Orchestrate data collection from all sources."""
    db = DuckDBClient()
    
    # Initialize database schema
    logger.info("Initializing database schema...")
    db.create_tables_from_sql()
    
    # Collect TMDB data
    logger.info("Fetching TMDB movie data...")
    tmdb_client = TMDBClient(api_key=settings.tmdb_api_key)
    
    # Get movies to refresh (movies with stale data)
    movies_to_refresh = db.get_movies_due_for_refresh(limit=100)
    
    if movies_to_refresh.empty:
        logger.info("No movies due for refresh. Fetching new movies...")
        # Get new movie IDs
        new_movies = tmdb_client.batch_get_movie_ids(
            start_year=2020, 
            end_year=2025, 
            min_vote_count=200
        )
        # Convert to DataFrame and upsert
        df_new = pd.DataFrame(new_movies)
        db.upsert_dataframe("movies", df_new, key_columns=["tmdb_id"])
    
    # Get full features for movies
    movie_ids = db.query("SELECT tmdb_id FROM movies WHERE last_tmdb_update IS NULL LIMIT 50")["tmdb_id"].tolist()
    
    if movie_ids:
        logger.info(f"Fetching features for {len(movie_ids)} movies...")
        features = tmdb_client.get_movie_features(movie_ids)
        df_features = pd.DataFrame(features)
        db.upsert_dataframe("tmdb_movies", df_features, key_columns=["tmdb_id"])
    
    # Collect OMDB data
    logger.info("Fetching OMDB movie data...")
    omdb_client = OMDBClient(api_key=settings.omdb_api_key, delay=0.1)
    
    # Get IMDb IDs that need OMDB data
    imdb_ids = db.query("""
        SELECT m.imdb_id 
        FROM movies m
        LEFT JOIN omdb_movies o ON m.movie_id = o.movie_id
        WHERE m.imdb_id IS NOT NULL 
          AND o.movie_id IS NULL
        LIMIT 50
    """)["imdb_id"].tolist()
    
    if imdb_ids:
        logger.info(f"Fetching OMDB data for {len(imdb_ids)} movies...")
        omdb_data = omdb_client.get_multiple_movies(imdb_ids)
        df_omdb = pd.DataFrame(omdb_data)
        db.upsert_dataframe("omdb_movies", df_omdb, key_columns=["imdb_id"])
    
    logger.info("Data collection complete!")
    db.close()

if __name__ == "__main__":
    main()
```

---

## 🔄 Phase 2: Refactor Data Collection Clients

### 2.1 Issues with Current Clients

**Problems in `tmdb.py` and `omdb.py`:**
1. ❌ Direct PostgreSQL session coupling
2. ❌ CSV file saving mixed with API logic
3. ❌ Hardcoded paths and filenames
4. ❌ Manual data type conversions
5. ❌ No proper error handling
6. ❌ Database-specific save methods

### 2.2 Modernized Client Architecture

**New pattern:**
```python
# API Client (pure data fetching)
# ├── Fetch data from API
# ├── Return normalized Python dicts/dataframes
# └── No database knowledge

# Database Client (pure storage)
# ├── Accept dataframes/dicts
# ├── Upsert to DuckDB
# └── No API knowledge

# Orchestrator (glue code)
# └── Coordinates clients and handles business logic
```

### 2.3 Refactored TMDB Client

**Create: `src/data_collection/tmdb_client.py`**

```python
"""
Modern TMDB API client.
Pure data fetching - no database coupling.
"""
import time
import httpx
from typing import List, Dict, Optional
from ayne.core.logging import get_logger
from ayne.core.config import settings

logger = get_logger(__name__)


class TMDBClient:
    """TMDB API client following modern async patterns."""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit: float = 0.1):
        self.api_key = api_key or settings.tmdb_api_key
        self.base_url = settings.tmdb_api_base_url
        self.rate_limit = rate_limit
        
        if not self.api_key:
            raise ValueError("TMDB API key is required")
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with error handling and rate limiting."""
        params = params or {}
        params["api_key"] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            with httpx.Client(timeout=settings.api_timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                time.sleep(self.rate_limit)
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching {endpoint}: {e}")
            raise
    
    def discover_movies(
        self,
        start_year: int,
        end_year: Optional[int] = None,
        min_vote_count: int = 200,
        max_pages: Optional[int] = None
    ) -> List[Dict]:
        """
        Discover movies by year and vote count.
        
        Returns:
            List of movie dictionaries with basic info
        """
        end_year = end_year or start_year
        all_movies = []
        
        for year in range(start_year, end_year + 1):
            logger.info(f"Fetching TMDB movies for year {year}")
            
            endpoint = "discover/movie"
            params = {
                "primary_release_date.gte": f"{year}-01-01",
                "primary_release_date.lte": f"{year}-12-31",
                "vote_count.gte": min_vote_count,
                "sort_by": "primary_release_date.desc",
                "page": 1
            }
            
            # Get first page to determine total pages
            response = self._request(endpoint, params)
            total_pages = response.get("total_pages", 1)
            
            if max_pages:
                total_pages = min(total_pages, max_pages)
            
            # Fetch all pages
            for page in range(1, total_pages + 1):
                params["page"] = page
                response = self._request(endpoint, params)
                movies = response.get("results", [])
                all_movies.extend(movies)
                logger.debug(f"Fetched page {page}/{total_pages} for {year}")
        
        logger.info(f"Discovered {len(all_movies)} movies")
        return self._normalize_discover_results(all_movies)
    
    def get_movie_details(self, tmdb_id: int) -> Dict:
        """Fetch full movie details by TMDB ID."""
        endpoint = f"movie/{tmdb_id}"
        response = self._request(endpoint)
        return self._normalize_movie_details(response)
    
    def get_batch_movie_details(self, tmdb_ids: List[int]) -> List[Dict]:
        """Fetch details for multiple movies."""
        movies = []
        total = len(tmdb_ids)
        
        for idx, tmdb_id in enumerate(tmdb_ids, 1):
            logger.info(f"Fetching movie {idx}/{total}: TMDB ID {tmdb_id}")
            try:
                movie = self.get_movie_details(tmdb_id)
                movies.append(movie)
            except Exception as e:
                logger.error(f"Failed to fetch TMDB ID {tmdb_id}: {e}")
                continue
        
        return movies
    
    def _normalize_discover_results(self, movies: List[Dict]) -> List[Dict]:
        """Normalize discover API response to standard format."""
        normalized = []
        for movie in movies:
            normalized.append({
                "tmdb_id": movie.get("id"),
                "title": movie.get("title"),
                "release_date": movie.get("release_date"),
                "vote_count": movie.get("vote_count"),
                "vote_average": movie.get("vote_average"),
                "popularity": movie.get("popularity"),
                "genre_ids": ",".join(map(str, movie.get("genre_ids", [])))
            })
        return normalized
    
    def _normalize_movie_details(self, movie: Dict) -> Dict:
        """Normalize movie details API response."""
        genres = movie.get("genres", [])
        prod_companies = movie.get("production_companies", [])
        prod_countries = movie.get("production_countries", [])
        languages = movie.get("spoken_languages", [])
        
        return {
            "tmdb_id": movie.get("id"),
            "imdb_id": movie.get("imdb_id"),
            "title": movie.get("title"),
            "release_date": movie.get("release_date"),
            "status": movie.get("status"),
            "budget": movie.get("budget"),
            "revenue": movie.get("revenue"),
            "runtime": movie.get("runtime"),
            "vote_count": movie.get("vote_count"),
            "vote_average": movie.get("vote_average"),
            "popularity": movie.get("popularity"),
            "genres": ",".join([g.get("name", "") for g in genres]),
            "production_companies": ",".join([c.get("name", "") for c in prod_companies]),
            "production_countries": ",".join([c.get("name", "") for c in prod_countries]),
            "spoken_languages": ",".join([l.get("english_name", "") for l in languages]),
            "overview": movie.get("overview"),
            "tmdb_raw": movie  # Store full response as JSON
        }
```

### 2.4 Refactored OMDB Client

**Create: `src/data_collection/omdb_client.py`**

```python
"""
Modern OMDB API client.
Pure data fetching - no database coupling.
"""
import time
import httpx
from typing import List, Dict, Optional
from ayne.core.logging import get_logger
from ayne.core.config import settings

logger = get_logger(__name__)


class OMDBClient:
    """OMDB API client following modern patterns."""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit: float = 0.1):
        self.api_key = api_key or settings.omdb_api_key
        self.base_url = settings.omdb_api_base_url
        self.rate_limit = rate_limit
        
        if not self.api_key:
            raise ValueError("OMDB API key is required")
    
    def _request(self, params: Dict) -> Dict:
        """Make API request with error handling."""
        params["apikey"] = self.api_key
        
        try:
            with httpx.Client(timeout=settings.api_timeout) as client:
                response = client.get(self.base_url, params=params)
                response.raise_for_status()
                time.sleep(self.rate_limit)
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from OMDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching from OMDB: {e}")
            raise
    
    def get_movie_by_imdb_id(self, imdb_id: str) -> Dict:
        """Fetch movie by IMDb ID."""
        params = {"i": imdb_id}
        response = self._request(params)
        
        if response.get("Response") == "False":
            logger.warning(f"Movie not found: {imdb_id}")
            return {}
        
        return self._normalize_movie(response)
    
    def get_batch_movies(self, imdb_ids: List[str]) -> List[Dict]:
        """Fetch multiple movies by IMDb ID."""
        movies = []
        total = len(imdb_ids)
        
        for idx, imdb_id in enumerate(imdb_ids, 1):
            logger.info(f"Fetching movie {idx}/{total}: IMDb ID {imdb_id}")
            try:
                movie = self.get_movie_by_imdb_id(imdb_id)
                if movie:
                    movies.append(movie)
            except Exception as e:
                logger.error(f"Failed to fetch IMDb ID {imdb_id}: {e}")
                continue
        
        return movies
    
    def _normalize_movie(self, movie: Dict) -> Dict:
        """Normalize OMDB API response."""
        # Extract ratings
        rt_rating = None
        mc_rating = None
        
        for rating in movie.get("Ratings", []):
            source = rating.get("Source", "")
            value = rating.get("Value", "")
            
            if source == "Rotten Tomatoes":
                rt_rating = int(value.rstrip("%")) if value != "N/A" else None
            elif source == "Metacritic":
                mc_rating = int(value.split("/")[0]) if value != "N/A" else None
        
        # Parse box office
        box_office = movie.get("BoxOffice", "N/A")
        if box_office != "N/A":
            box_office = int(box_office.replace("$", "").replace(",", ""))
        else:
            box_office = None
        
        # Parse IMDb rating
        imdb_rating = movie.get("imdbRating")
        if imdb_rating and imdb_rating != "N/A":
            imdb_rating = float(imdb_rating)
        else:
            imdb_rating = None
        
        # Parse metascore
        metascore = movie.get("Metascore")
        if metascore and metascore != "N/A":
            metascore = int(metascore)
        else:
            metascore = None
        
        return {
            "imdb_id": movie.get("imdbID"),
            "title": movie.get("Title"),
            "year": int(movie.get("Year")) if movie.get("Year", "N/A") != "N/A" else None,
            "rated": movie.get("Rated"),
            "released": movie.get("Released"),
            "runtime": movie.get("Runtime"),
            "genre": movie.get("Genre"),
            "director": movie.get("Director"),
            "writer": movie.get("Writer"),
            "actors": movie.get("Actors"),
            "plot": movie.get("Plot"),
            "language": movie.get("Language"),
            "country": movie.get("Country"),
            "awards": movie.get("Awards"),
            "imdb_rating": imdb_rating,
            "imdb_votes": movie.get("imdbVotes"),
            "box_office": box_office,
            "metacritic_score": metascore,
            "rotten_tomatoes_rating": rt_rating,
            "meta_critic_rating": mc_rating,
            "omdb_raw": movie  # Store full response
        }
```

---

## 🗂️ Phase 3: File and Directory Cleanup

### 3.1 Files to DELETE

```bash
# Old database system
database/
├── __init__.py          # DELETE
├── models.py            # DELETE (SQLAlchemy models)
├── queries.py           # DELETE (raw SQL)
└── utils.py             # DELETE (PostgreSQL utils)

# Old data collection
src/data_collection/
├── tmdb.py              # REPLACE with tmdb_client.py
└── omdb.py              # REPLACE with omdb_client.py

# Old scripts
scripts/
└── update_db.py         # REPLACE with collect_data.py

# Postgres remnants
src/db/postgres/         # DELETE entire directory
```

### 3.2 Files to MOVE

```bash
# Move to proper locations
src/data/io/
├── io.py                # Keep, modernize
└── io_parquet.py        # Keep, enhance

# Utils to consolidate
src/utils/
├── utils.py             # Refactor, split into focused modules
└── model_io.py          # Keep, modernize for joblib
```

### 3.3 New Files to CREATE

```bash
src/db/
├── __init__.py
├── duckdb_client.py      # ✅ Already exists, enhance
└── schema.sql            # ✅ Already exists

src/data_collection/
├── __init__.py
├── tmdb_client.py        # New modern client
├── omdb_client.py        # New modern client
└── the_numbers_scraper.py  # Future: web scraping

scripts/
├── collect_data.py       # New orchestrator
├── init_database.py      # Database initialization
└── export_data.py        # Export to parquet/CSV

src/pipelines/
├── __init__.py
├── data_ingestion.py     # Data collection pipeline
├── preprocessing.py      # Data cleaning pipeline
└── training.py           # Model training pipeline
```

---

## 📦 Phase 4: Dependencies Modernization

### 4.1 Dependencies to REMOVE

```toml
# OLD - Remove from pyproject.toml
"sqlalchemy>=2.0,<3.0"          # ❌ No longer needed (DuckDB native)
"psycopg2-binary>=2.9,<3.0"     # ❌ PostgreSQL driver not needed
"dill>=0.3,<1.0"                # ❌ Use joblib/cloudpickle instead
```

### 4.2 Dependencies to ADD

```toml
# NEW - Add to pyproject.toml
dependencies = [
    # ... existing dependencies ...
    "duckdb>=1.1,<2.0",           # ✅ Analytical database
    "httpx>=0.27,<1.0",           # ✅ Already there, modern HTTP
    "joblib>=1.4,<2.0",           # ✅ Better than dill for models
]
```

### 4.3 Dependencies to UPDATE

```toml
# Check for updates
"pydantic>=2.9,<3.0"            # Latest Pydantic v2
"fastapi>=0.115,<1.0"           # Latest FastAPI
"pandas>=2.2,<3.0"              # ✅ Already good
"polars>=1.7,<2.0"              # ✅ Consider using for speed
```

### 4.4 Run Dependency Audit

```bash
# Install and run security audit
uv pip install pip-audit
pip-audit

# Update dependencies
uv sync --upgrade

# Check for unused dependencies
uv pip list --not-required
```

---

## 🏗️ Phase 5: Configuration System Enhancement

### 5.1 Current Issues

1. ❌ Hardcoded database URL in settings
2. ❌ Missing DuckDB configuration
3. ❌ API keys exposed in code
4. ❌ No environment-specific overrides

### 5.2 Enhanced Settings

**Update: `src/core/config/settings.py`**

```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Literal, Optional


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    type: Literal["duckdb", "duckdb-memory"] = "duckdb"
    path: Path = Field(default=Path("data/db/movies.duckdb"))
    read_only: bool = False
    
    @property
    def connection_string(self) -> str:
        if self.type == "duckdb-memory":
            return ":memory:"
        return str(self.path)


class APISettings(BaseSettings):
    """API client configuration."""
    tmdb_api_key: Optional[str] = None
    omdb_api_key: Optional[str] = None
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    omdb_base_url: str = "http://www.omdbapi.com"
    rate_limit: float = 0.1  # seconds between requests
    timeout: int = 30  # seconds


class Settings(BaseSettings):
    """Main application settings."""
    
    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    app_name: str = "Are You Not Entertained"
    debug: bool = True
    
    # Logging
    log_level: str = "INFO"
    use_json_logging: bool = False
    
    # Database (nested config)
    database: DatabaseSettings = DatabaseSettings()
    
    # API (nested config)
    api: APISettings = APISettings()
    
    # Paths
    data_dir: Path = Field(default=Path("data"))
    models_dir: Path = Field(default=Path("models"))
    
    # ML
    random_seed: int = 42
    batch_size: int = 100
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",  # Allows DATABASE__PATH=...
        case_sensitive=False,
        extra="ignore",
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return v.upper()
```

### 5.3 Environment Configuration

**Update: `configs/development.yaml`**

```yaml
environment: development
debug: true
log_level: DEBUG
use_json_logging: false

database:
  type: duckdb
  path: data/db/movies_dev.duckdb
  read_only: false

api:
  tmdb_base_url: https://api.themoviedb.org/3
  omdb_base_url: http://www.omdbapi.com
  rate_limit: 0.1
  timeout: 30

data_dir: data
models_dir: models
random_seed: 42
batch_size: 100
```

**Update: `.env`**

```bash
# Environment
ENVIRONMENT=development

# API Keys (SENSITIVE)
API__TMDB_API_KEY=your_tmdb_key_here
API__OMDB_API_KEY=your_omdb_key_here

# Database (optional override)
DATABASE__PATH=data/db/movies.duckdb

# Logging
LOG_LEVEL=INFO
USE_JSON_LOGGING=false
```

---

## 🧪 Phase 6: Testing Strategy

### 6.1 Test Structure

```bash
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── unit/
│   ├── test_duckdb_client.py
│   ├── test_tmdb_client.py
│   ├── test_omdb_client.py
│   └── test_config.py
├── integration/
│   ├── test_data_collection.py
│   ├── test_database_ops.py
│   └── test_pipelines.py
└── fixtures/
    ├── sample_tmdb_response.json
    └── sample_omdb_response.json
```

### 6.2 Sample Test: DuckDB Client

**Create: `tests/unit/test_duckdb_client.py`**

```python
import pytest
import pandas as pd
from pathlib import Path
from ayne.db.duckdb_client import DuckDBClient


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary DuckDB for testing."""
    db_path = tmp_path / "test.duckdb"
    db = DuckDBClient(db_path=db_path)
    db.create_tables_from_sql()
    yield db
    db.close()


def test_table_creation(temp_db):
    """Test that schema creates tables."""
    assert temp_db.table_exists("movies")
    assert temp_db.table_exists("tmdb_movies")
    assert temp_db.table_exists("omdb_movies")


def test_upsert_dataframe(temp_db):
    """Test upsert functionality."""
    # Insert initial data
    df = pd.DataFrame({
        "tmdb_id": [1, 2, 3],
        "title": ["Movie A", "Movie B", "Movie C"],
        "release_date": ["2020-01-01", "2021-01-01", "2022-01-01"]
    })
    
    temp_db.upsert_dataframe("movies", df, key_columns=["tmdb_id"])
    
    # Verify insert
    result = temp_db.query("SELECT COUNT(*) as count FROM movies")
    assert result["count"].iloc[0] == 3
    
    # Update existing row
    df_update = pd.DataFrame({
        "tmdb_id": [1],
        "title": ["Movie A Updated"],
        "release_date": ["2020-01-01"]
    })
    
    temp_db.upsert_dataframe("movies", df_update, key_columns=["tmdb_id"])
    
    # Verify update (count should still be 3)
    result = temp_db.query("SELECT COUNT(*) as count FROM movies")
    assert result["count"].iloc[0] == 3
    
    # Verify title changed
    result = temp_db.query("SELECT title FROM movies WHERE tmdb_id = 1")
    assert result["title"].iloc[0] == "Movie A Updated"


def test_query_with_params(temp_db):
    """Test parameterized queries."""
    df = pd.DataFrame({
        "tmdb_id": [1, 2, 3],
        "title": ["Movie A", "Movie B", "Movie C"],
        "release_date": ["2020-01-01", "2021-01-01", "2022-01-01"]
    })
    temp_db.upsert_dataframe("movies", df, key_columns=["tmdb_id"])
    
    result = temp_db.query(
        "SELECT * FROM movies WHERE tmdb_id = ?",
        params=[2]
    )
    assert len(result) == 1
    assert result["title"].iloc[0] == "Movie B"
```

---

## 🚀 Phase 7: Implementation Roadmap

### Week 1: Database Migration
- [x] Day 1: Review and finalize DuckDB schema
- [ ] Day 2: Create `scripts/init_database.py`
- [ ] Day 3: Test schema creation and basic CRUD
- [ ] Day 4: Write unit tests for DuckDBClient
- [ ] Day 5: Document database architecture

### Week 2: API Client Refactoring
- [ ] Day 1: Create modern `tmdb_client.py`
- [ ] Day 2: Create modern `omdb_client.py`
- [ ] Day 3: Write unit tests with mocked responses
- [ ] Day 4: Create `scripts/collect_data.py` orchestrator
- [ ] Day 5: Test end-to-end data collection

### Week 3: Legacy Code Removal
- [ ] Day 1: Delete `database/` folder and PostgreSQL code
- [ ] Day 2: Remove SQLAlchemy dependencies
- [ ] Day 3: Update imports across project
- [ ] Day 4: Fix broken tests
- [ ] Day 5: Clean up unused files

### Week 4: Configuration & Testing
- [ ] Day 1: Enhance Pydantic settings
- [ ] Day 2: Update all config files
- [ ] Day 3: Write integration tests
- [ ] Day 4: Run full test suite
- [ ] Day 5: Update documentation

### Week 5: Pipeline Development
- [ ] Day 1: Create data ingestion pipeline
- [ ] Day 2: Create preprocessing pipeline
- [ ] Day 3: Update model training to use DuckDB
- [ ] Day 4: Test pipelines end-to-end
- [ ] Day 5: Performance optimization

---

## 📝 Best Practices Checklist

### Code Quality
- [ ] Use type hints everywhere (`from typing import ...`)
- [ ] Follow PEP 8 (enforced by Black)
- [ ] Write docstrings (Google style)
- [ ] Use dataclasses/Pydantic for structured data
- [ ] Avoid mutable default arguments

### Modern Python Patterns
- [ ] Use `pathlib.Path` instead of string paths
- [ ] Use f-strings for formatting
- [ ] Use context managers (`with` statements)
- [ ] Use `httpx` instead of `requests`
- [ ] Use `joblib` instead of `pickle`/`dill`

### Error Handling
- [ ] Use specific exceptions, not bare `except`
- [ ] Log errors before re-raising
- [ ] Use custom exceptions for domain errors
- [ ] Validate inputs with Pydantic
- [ ] Provide helpful error messages

### Configuration
- [ ] Store secrets in `.env` only
- [ ] Use Pydantic for validation
- [ ] Support environment overrides
- [ ] Document all config options
- [ ] Provide sensible defaults

### Database
- [ ] Use parameterized queries (no SQL injection)
- [ ] Handle NULL values gracefully
- [ ] Use transactions for multi-step operations
- [ ] Index frequently queried columns
- [ ] Regular VACUUM/ANALYZE

### Testing
- [ ] Unit test all business logic
- [ ] Integration test data flows
- [ ] Mock external APIs
- [ ] Use fixtures for test data
- [ ] Maintain >80% coverage

---

## 🎓 Recommended Tools & Libraries

### Essential Modern Tools

```toml
# Must-have for modern ML projects
dependencies = [
    # Core ML Stack
    "pandas>=2.2",           # Data manipulation
    "polars>=1.7",           # Faster alternative to pandas
    "numpy>=2.1",            # Numerical computing
    "scikit-learn>=1.5",     # ML algorithms
    "xgboost>=2.0",          # Gradient boosting
    
    # Database & Storage
    "duckdb>=1.1",           # Analytical database
    "pyarrow>=16.1",         # Parquet I/O
    
    # APIs & HTTP
    "httpx>=0.27",           # Modern async HTTP client
    "beautifulsoup4>=4.12",  # Web scraping
    
    # Configuration
    "pydantic>=2.9",         # Data validation
    "pydantic-settings>=2.0",# Settings management
    "python-dotenv>=1.0",    # .env file support
    
    # Serialization
    "joblib>=1.4",           # Model serialization
    "cloudpickle>=3.0",      # Enhanced pickling
    
    # Experiment Tracking
    "mlflow>=2.15",          # Model versioning
    
    # Visualization
    "matplotlib>=3.8",       # Static plots
    "seaborn>=0.13",         # Statistical viz
    "plotly>=6.0",           # Interactive plots
    
    # Web Framework (future)
    "fastapi>=0.115",        # Modern API framework
    "uvicorn>=0.30",         # ASGI server
]

[dependency-groups]
dev = [
    "pytest>=8.3",           # Testing framework
    "pytest-cov>=6.0",       # Coverage reporting
    "pytest-asyncio>=0.24",  # Async tests
    "black>=24.0",           # Code formatter
    "ruff>=0.6",             # Fast linter
    "mypy>=1.13",            # Type checking
    "ipython>=8.27",         # Better REPL
]
```

### Tools to Consider Adding

```toml
[dependency-groups]
data-quality = [
    "great-expectations>=0.18",  # Data validation
    "pandera>=0.20",             # DataFrame validation
]

monitoring = [
    "evidently>=0.4",            # ML monitoring
    "prometheus-client>=0.20",   # Metrics
]

performance = [
    "dask>=2024.9",              # Parallel computing
    "ray>=2.30",                 # Distributed computing
]
```

---

## 📚 Next Steps - Copy/Paste Prompts

### Prompt 1: Initialize DuckDB Schema
```
I need to create a script that initializes the DuckDB database using the schema.sql file. 
The script should:
1. Import DuckDBClient from ayne.db.duckdb_client
2. Create the database file if it doesn't exist
3. Run the schema.sql to create all tables
4. Add some basic validation (check that tables exist)
5. Include proper logging
6. Save as scripts/init_database.py
```

### Prompt 2: Refactor TMDB Client
```
I need to refactor src/data_collection/tmdb.py into a modern client following these requirements:
1. Remove all database coupling (no SQLAlchemy, no session parameters)
2. Use httpx instead of requests
3. Return normalized pandas DataFrames or lists of dicts
4. Add proper error handling and logging
5. Follow the architecture I defined in the modernization plan
6. Save as src/data_collection/tmdb_client.py (new file)
```

### Prompt 3: Create Data Collection Orchestrator
```
I need a new data collection orchestrator script that:
1. Uses the modern DuckDBClient
2. Uses the new tmdb_client and omdb_client
3. Fetches movies intelligently (only those needing updates)
4. Uses the upsert patterns in DuckDB
5. Includes proper logging and error handling
6. Saves as scripts/collect_data.py
```

### Prompt 4: Update Configuration
```
I need to enhance my Pydantic settings to support:
1. Nested database configuration (type, path, read_only)
2. Nested API configuration (keys, base URLs, rate limits)
3. Environment variable overrides with __ delimiter
4. Update configs/development.yaml to match new structure
```

### Prompt 5: Write Tests
```
I need comprehensive unit tests for DuckDBClient including:
1. Schema creation
2. Upsert operations (insert and update)
3. Parameterized queries
4. Table existence checks
5. Error handling
Save as tests/unit/test_duckdb_client.py
```

### Prompt 6: Create Data Export Script
```
I need a script to export DuckDB tables to Parquet files:
1. Accept table name and output path as arguments
2. Use DuckDBClient.export_table_to_parquet()
3. Include options for date-based exports
4. Add logging and validation
5. Save as scripts/export_data.py
```

### Prompt 7: Cleanup Legacy Code
```
I need to safely remove legacy PostgreSQL code:
1. Delete database/ folder (after backing up queries)
2. Remove old src/data_collection/tmdb.py and omdb.py
3. Delete scripts/update_db.py
4. Remove SQLAlchemy and psycopg2 from pyproject.toml
5. Fix any broken imports across the project
6. Update README.md to reflect new architecture
```

---

## 🎯 Success Criteria

### Technical Goals
- ✅ Zero PostgreSQL dependencies
- ✅ All data in DuckDB + Parquet
- ✅ < 100ms query response time for analytics
- ✅ > 80% test coverage
- ✅ No hardcoded paths or credentials
- ✅ All linting passes (ruff, black, mypy)

### Documentation Goals
- ✅ Clear README with setup instructions
- ✅ API client docstrings
- ✅ Database schema documentation
- ✅ Configuration guide
- ✅ Contribution guidelines

### Performance Goals
- ✅ API collection: < 5 sec per movie
- ✅ Database upsert: < 1 sec for 100 rows
- ✅ Query performance: < 100ms for joins
- ✅ Parquet I/O: < 2 sec for 10k rows

---

## 📞 Support & Resources

### Documentation
- [DuckDB Official Docs](https://duckdb.org/docs/)
- [Pydantic V2 Docs](https://docs.pydantic.dev/latest/)
- [HTTPX User Guide](https://www.python-httpx.org/)
- [Pytest Documentation](https://docs.pytest.org/)

### Community
- Stack Overflow: Tag questions with `duckdb`, `pydantic`
- GitHub Discussions: Share patterns and questions

### Reference Projects
- [DuckDB Examples](https://github.com/duckdb/duckdb/tree/main/examples)
- [Modern Python Template](https://github.com/cjolowicz/cookiecutter-hypermodern-python)

---

**END OF MODERNIZATION PLAN v1.0**

*Last Updated: November 20, 2025*
*Author: GitHub Copilot*
*Project: Are You Not Entertained?*
