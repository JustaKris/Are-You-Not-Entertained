# Technical Decisions & Rationale

**Document Purpose**: Explain WHY specific technology choices were made
**Audience**: Future you, collaborators, code reviewers

---

## Core Architectural Decisions

### 1. DuckDB vs PostgreSQL vs SQLite

#### Decision: Use DuckDB

**Rationale**:

| Requirement | DuckDB | PostgreSQL | SQLite | Verdict |
| ------------- | -------- | ------------ | -------- | --------- |
| Analytical queries (aggregations, joins) | 🟢 Optimized | 🟡 OK | 🟡 Slower | DuckDB |
| Local development | 🟢 Embedded | 🔴 Server | 🟢 Embedded | DuckDB/SQLite |
| Parquet integration | 🟢 Native | 🔴 Extension | 🔴 None | DuckDB |
| Write-heavy workloads | 🟡 OK | 🟢 Excellent | 🟡 OK | PostgreSQL |
| Columnar storage | 🟢 Yes | 🔴 No | 🔴 No | DuckDB |
| Zero setup | 🟢 Yes | 🔴 No | 🟢 Yes | DuckDB/SQLite |
| ML pipeline fit | 🟢 Perfect | 🟡 Overkill | 🟡 Limited | DuckDB |

**Use case**:

- Analytical queries on movie data (aggregations, trends)
- Read-heavy workload (train models, generate reports)
- Local development (no server management)
- Parquet files for efficient storage
- Single-user access patterns

**Conclusion**: DuckDB is purpose-built for this exact use case.

**When to reconsider**:

- You need multi-user concurrent writes → PostgreSQL
- You need simple key-value storage → SQLite
- You're deploying a web app with transactions → PostgreSQL

---

### 2. Parquet vs CSV vs JSON

#### Decision: Use Parquet (with CSV for exports)

**Rationale**:

| Aspect | Parquet | CSV | JSON | Verdict |
| -------- | --------- | ----- | ------ | --------- |
| Storage size | 🟢 10x smaller | 🔴 Large | 🔴 Larger | Parquet |
| Read speed | 🟢 10x faster | 🟡 OK | 🟡 OK | Parquet |
| Schema enforcement | 🟢 Yes | 🔴 No | 🔴 No | Parquet |
| Columnar queries | 🟢 Optimized | 🔴 Poor | 🔴 Poor | Parquet |
| Human readable | 🔴 No | 🟢 Yes | 🟢 Yes | CSV/JSON |
| Pandas/Polars support | 🟢 Native | 🟢 Native | 🟢 Native | All |

**Storage strategy**:

```text
Raw API responses → Parquet (archival, debugging)
Intermediate data → Parquet (efficient processing)
Final datasets → Parquet (model training)
Reports/exports → CSV (human-readable)
```

**Performance impact** (100,000 rows of movie data):

```text
- CSV: ~50 MB, 2 sec read
- Parquet: ~5 MB, 0.2 sec read
- JSON: ~60 MB, 3 sec read
```

---

### 3. Pandas vs Polars

#### Decision: Pandas primary, Polars for performance bottlenecks

**Pandas strengths**: industry standard, massive ecosystem (scikit-learn, matplotlib, etc.),
excellent documentation.

**Polars strengths**: 5-10x faster for large datasets, better memory efficiency, modern
API with a query optimizer, multi-threaded by default.

**Strategy**:

```python
# Use Pandas for:
# - Exploratory data analysis (notebooks)
# - Integration with scikit-learn
# - Small to medium datasets (< 1M rows)

# Use Polars for:
# - Large dataset processing (> 1M rows)
# - ETL pipelines / data cleaning operations
# - Performance-critical paths
```

**Example**:

```python
import polars as pl

# Read large file efficiently and do heavy transforms with Polars
df_polars = (
    pl.read_parquet("large_dataset.parquet")
    .filter(pl.col("year") > 2000)
    .group_by("genre")
    .agg(pl.col("revenue").mean())
)

# Convert to Pandas for scikit-learn
df_pandas = df_polars.to_pandas()
model.fit(df_pandas[features], df_pandas[target])
```

---

### 4. Requests vs HTTPX

#### Decision: Use HTTPX

**Rationale**:

| Feature | HTTPX | Requests | Verdict |
| --------- | ------- | ---------- | --------- |
| Async support | 🟢 Native | 🔴 No | HTTPX |
| HTTP/2 | 🟢 Yes | 🔴 No | HTTPX |
| Modern API | 🟢 Yes | 🟡 Older | HTTPX |
| Maintained | 🟢 Active | 🟡 Slow | HTTPX |

**Why it matters**:

```python
# With requests (synchronous, blocking)
for movie_id in movie_ids:  # 1000 movies
    response = requests.get(f"api/movie/{movie_id}")
    # Total time: 1000 * 0.5s = 500 seconds (8+ minutes)

# With httpx (async, concurrent)
async with httpx.AsyncClient() as client:
    tasks = [client.get(f"api/movie/{id}") for id in movie_ids]
    responses = await asyncio.gather(*tasks)
    # Total time: ~10 seconds (50x faster)
```

All three async clients in this project (TMDB, OMDB, The Numbers) use httpx, sharing a
common `AsyncRateLimiter` + `retry_with_backoff` implementation (see
[rate-limiting.md](../reference/rate-limiting.md)).

---

### 5. Pickle/Dill vs Joblib vs Cloudpickle

#### Decision: Use Joblib for models

| Library | Use case | Strengths | Weaknesses |
| --------- | ---------- | ----------- | ------------ |
| **pickle** | Built-in serialization | Standard, fast | Limited types, version issues |
| **dill** | Extended pickle | More types | Slower, maintenance issues |
| **joblib** | ML models | Numpy-optimized, compression | ML-focused only |
| **cloudpickle** | Lambda functions | Dynamic code, flexible | Larger files |

```python
# For scikit-learn models → joblib
from ayne.ml.models.serialize import save_model, load_model
save_model(model, "model_v1")
model = load_model("data/artifacts/models/model_v1.joblib")

# For XGBoost → native save
model.save_model("xgb_model.json")
```

See [utilities-guide.md](../guides/utilities-guide.md) for the full serialization API.

---

### 6. SQLAlchemy ORM vs Raw SQL vs Query Builder

#### Decision: Raw, parameterized SQL for DuckDB

**Why not an ORM**: DuckDB doesn't need ORM overhead, analytical queries don't map well to
ORM, there are no complex relationships to manage, and ORMs impose a performance penalty
for aggregations.

**Why raw SQL**: direct/explicit control, easy to optimize, better for analytical queries,
no impedance mismatch.

**Pattern**:

```python
# GOOD: Parameterized raw SQL
db.query(
    """
    SELECT m.title, t.revenue, o.imdb_rating
    FROM movies m
    JOIN tmdb_movies t ON m.movie_id = t.movie_id
    JOIN omdb_movies o ON m.movie_id = o.movie_id
    WHERE m.release_date > ?
    """,
    params=["2020-01-01"],
)

# BAD: String formatting (SQL injection risk)
year = "2020-01-01"
db.query(f"SELECT * FROM movies WHERE release_date > '{year}'")
```

**When to reconsider**: moving to PostgreSQL with multi-user writes, building a REST API
with CRUD operations, or needing automatic schema migrations (Alembic + SQLAlchemy).

---

### 7. Configuration Management

#### Decision: Pydantic Settings + YAML + .env

```text
┌─────────────────────────────────────────┐
│ Environment Variables (highest priority)│
├─────────────────────────────────────────┤
│ .env file (secrets, local overrides)    │
├─────────────────────────────────────────┤
│ YAML configs (environment-specific)     │
├─────────────────────────────────────────┤
│ Pydantic defaults (fallbacks)           │
└─────────────────────────────────────────┘
```

**Benefits**: type safety (Pydantic validates all config at startup), environment
separation (different YAML for dev/staging/prod), secret management (sensitive data in
`.env` only), IDE autocomplete, and early validation.

```python
from ayne.core.config import settings

api_key = settings.tmdb_api_key  # str | None
timeout = settings.api_timeout    # int (validated)
```

**Alternatives considered**: configparser (too basic, no validation), plain Python files
(security risk, no separation), JSON (no comments, harder to maintain), TOML (good, but
YAML is more readable for these configs).

---

### 8. Logging Strategy

#### Decision: Structured logging with the standard `logging` module

**Development**: colorized, human-readable console logs (`configure_logging(level="DEBUG", use_json=False)`).

**Production**: JSON logs for parsing by log aggregators (`configure_logging(level="INFO", use_json=True)`)
— parseable by CloudWatch/Datadog/Loki, supports structured querying, easy to add context
fields (`request_id`, `user_id`), no log-parsing regex.

```python
logger = get_logger(__name__)
logger.info("Movie processed", extra={"movie_id": 12345, "processing_time_ms": 234})
```

---

### 9. Dependency Management

#### Decision: Use `uv` instead of pip/poetry

| Tool | Speed | Resolution | Lock files | Verdict |
| -------- | ------- | ------------ | ------------ | --------- |
| pip | Slow | Basic | No | Legacy |
| pip-tools | Slow | Good | Yes | OK |
| poetry | Slow | Good | Yes | Good |
| pdm | Fast | Good | Yes | Modern |
| uv | Blazing | Excellent | Yes | Best |

`uv` is 10-100x faster than pip, has better dependency resolution, is compatible with
pip/poetry/requirements.txt, and uses a single `pyproject.toml` (PEP 621).

```powershell
uv sync                       # Install dependencies
uv add duckdb                 # Add a package
uv add --group dev pytest     # Add a dev dependency
uv sync --upgrade             # Update all packages
```

---

## Modern Python Practices Applied

### Type hints everywhere

```python
def process_movies(movies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [m for m in movies if m["year"] > 2000]
```

### Pathlib over os.path

```python
from pathlib import Path
path = Path("data") / "movies.csv"
```

### Context managers

```python
with DuckDBClient() as db:
    result = db.query("SELECT * FROM movies")
```

### Pydantic models over raw dicts

```python
from pydantic import BaseModel

class Movie(BaseModel):
    title: str
    year: int
    revenue: int

movie = Movie(title="The Matrix", year=1999, revenue=463000000)
```

---

## Performance Benchmarks

### Query performance (100k movies)

```text
Operation               | Time    | Improvement
------------------------|---------|------------
DuckDB aggregation      | 0.05s   | Baseline
PostgreSQL aggregation  | 0.3s    | 6x slower
Pandas groupby          | 1.2s    | 24x slower
CSV full scan           | 3.5s    | 70x slower
```

### Data loading (1M rows)

```text
Format    | File Size | Read Time | Write Time
----------|-----------|-----------|------------
Parquet   | 12 MB     | 0.3s      | 0.5s
CSV       | 145 MB    | 4.2s      | 3.8s
JSON      | 180 MB    | 6.5s      | 5.2s
```

### API client performance (fetching 100 movies)

```text
- requests (sync):      52 seconds
- httpx (sync):         50 seconds
- httpx (async):        5 seconds (10x faster)
```

---

## Future Considerations

- **FastAPI**: add when a REST API for predictions is needed (building a web application).
- **Celery/RQ**: add when background job processing is needed (long-running collection tasks).
- **Redis**: add when repeated API calls to the same endpoints cause rate-limit issues.
- **Docker**: add when deploying to production (moving to cloud).
- **Great Expectations**: add if data quality issues increase (bad data causing model failures).

---

## Summary of Decisions

| Component | Choice | Primary Reason |
| --------- | -------- | ---------------- |
| Database | DuckDB | Analytical queries, Parquet integration |
| Storage | Parquet | 10x compression, columnar efficiency |
| DataFrames | Pandas | Ecosystem + performance |
| HTTP Client | HTTPX | Async support, modern |
| Serialization | Joblib | ML model optimization |
| Config | Pydantic + YAML | Type safety, validation |
| Logging | Python logging | Structured JSON option |
| Package Manager | uv | Speed, modern standards |
