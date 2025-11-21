# Data Collection Orchestration

> **Status**: Template - Content to be filled in

High-level orchestration of data collection workflow across multiple APIs.

## Overview

The `DataCollectionOrchestrator` coordinates:

1. Movie discovery (TMDB)
2. Detail fetching (TMDB)
3. Ratings enrichment (OMDB)
4. Box office data (The Numbers)
5. Database updates
6. Refresh logic

## Workflow

### Full Collection

```python
from src.data_collection.orchestrator import DataCollectionOrchestrator
from src.database.duckdb_client import DuckDBClient

db = DuckDBClient()
orchestrator = DataCollectionOrchestrator(db)

# Run complete workflow
stats = await orchestrator.run_full_collection(
    discover_start_year=2024,
    discover_end_year=2024,
    refresh_limit=100
)

# Returns statistics
# {
#     "discovered": 150,
#     "tmdb_updated": 100,
#     "omdb_updated": 95,
#     "frozen": 5
# }
```

### Discovery Only

```python
count = await orchestrator.discover_and_store_movies(
    start_year=2024,
    min_vote_count=200
)
```

### Refresh Only

```python
# Get movies needing refresh
movies_df = orchestrator.get_movies_for_refresh(limit=100)

# Refresh them
tmdb_updated, omdb_updated, frozen = await orchestrator.refresh_movie_data(
    movies_df,
    fetch_tmdb=True,
    fetch_omdb=True
)
```

## Integration

Used by scripts:

- `scripts/collect_optimized.py`: Main collection script

## Related Components

- [TMDB Client](tmdb-client.md)
- [OMDB Client](omdb-client.md)
- [Refresh Strategy](refresh-strategy.md)
- [Database](database.md)
