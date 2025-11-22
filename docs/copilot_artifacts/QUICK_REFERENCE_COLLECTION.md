# Optimized Data Collection - Quick Reference

## Common Commands

### Daily Refresh (Recommended)
```bash
uv run python scripts/collect_optimized.py --refresh-only --refresh-limit 100
```

### Discover New Movies
```bash
uv run python scripts/collect_optimized.py --start-year 2024 --max-pages 5
```

### Full Workflow
```bash
uv run python scripts/collect_optimized.py \
    --start-year 2024 \
    --end-year 2024 \
    --max-pages 5 \
    --refresh-limit 50
```

---

## Refresh Intervals

| Movie Age | TMDB | OMDB | Box Office |
|-----------|------|------|------------|
| 0-60 days | 5d | 5d | 5d |
| 60-180 days | 15d | 30d | 30d |
| 180-365 days | 30d | 90d | 90d |
| > 365 days | 90d | 180d | 180d |

---

## Rate Limits

- **TMDB**: 4 req/s, 10 concurrent
- **OMDB**: 2 req/s, 5 concurrent

---

## Key Files

- **Script**: `scripts/collect_optimized.py`
- **Orchestrator**: `src/data_collection/orchestrator.py`
- **Refresh Logic**: `src/data_collection/refresh_strategy.py`
- **Async Clients**: 
  - `src/data_collection/tmdb/async_client.py`
  - `src/data_collection/omdb/async_client.py`

---

## Database Stats

```python
from ayne.database.duckdb_client import DuckDBClient
db = DuckDBClient()
stats = db.get_collection_stats()
print(stats)
db.close()
```

---

## Check Movies Due for Refresh

```sql
SELECT title, release_date, last_tmdb_update, last_omdb_update,
       DATEDIFF('day', release_date, CURRENT_DATE) as age_days
FROM movies
WHERE data_frozen = FALSE
  AND last_full_refresh IS NULL
LIMIT 10;
```

---

## Performance

- **5-8x faster** than sync version
- 50 movies in ~5-10 seconds
- Concurrent API calls with rate limiting

---

## Monitoring

Logs show progress:
```
INFO | Starting refresh for 50 movies...
INFO | Fetching TMDB data for 50 movies...
INFO | Progress: 10/50 movies fetched
INFO | ✅ Updated TMDB data for 50 movies
```
