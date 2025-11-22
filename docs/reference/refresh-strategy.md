# Refresh Strategy

Intelligent age-based strategy for determining when to refresh movie data from TMDB and OMDB APIs.

## Core Concept

**Problem**: We can't update every movie every day (API limits, cost, time)

**Solution**: Update frequency based on how often data realistically changes

**Key Insight**: New movies change frequently, old movies rarely change

## Movie Age Categories

Movies are classified into 4 age categories based on days since release:

```python
class MovieAge(Enum):
    RECENT = "recent"        # 0-60 days since release
    ESTABLISHED = "established"  # 60-180 days  
    MATURE = "mature"         # 180-365 days
    ARCHIVED = "archived"      # > 365 days
```

### Age Boundaries

| Category | Days Since Release | Example |
|----------|-------------------|---------|
| **Recent** | 0-60 | Movie released 2 months ago |
| **Established** | 61-180 | Movie released 4 months ago |
| **Mature** | 181-365 | Movie released 10 months ago |
| **Archived** | 366+ | Movie released 2 years ago |

### Rationale

**Recent (0-60 days)**:

- Still in theaters or just released to streaming
- Box office numbers updating
- Reviews and ratings accumulating
- High data volatility

**Established (60-180 days)**:

- Theatrical run mostly complete
- Initial reviews in
- Box office stabilizing
- Moderate data changes

**Mature (180-365 days)**:

- Available on streaming/rental
- All major reviews published
- Awards season may impact ratings
- Fewer data changes

**Archived (365+ days)**:

- Historical film
- Data mostly stable
- Occasional rating adjustments
- Rare data changes

## Refresh Intervals

### TMDB Refresh Intervals

| Age Category | Refresh Every | Reasoning |
|-------------|---------------|-----------|
| Recent | **5 days** | Budget/revenue updates, vote counts changing |
| Established | **15 days** | Vote average stabilizing, genres/companies set |
| Mature | **30 days** | Data mostly stable, occasional corrections |
| Archived | **90 days** | Very stable, quarterly checks sufficient |

### OMDB Refresh Intervals

| Age Category | Refresh Every | Reasoning |
|-------------|---------------|-----------|
| Recent | **5 days** | IMDb ratings volatile, RT/Metacritic scores changing |
| Established | **30 days** | Awards accumulating, ratings stabilizing |
| Mature | **90 days** | Most awards decided, ratings stable |
| Archived | **180 days** | Minimal changes, semi-annual checks |

### Box Office (The Numbers) - Future

Currently not implemented, but planned:

| Age Category | Refresh Every |
|-------------|---------------|
| Recent | 5 days |
| Established | 30 days |
| Mature | 90 days |
| Archived | 180 days |

## Implementation

### Determining Movie Age

```python
def get_movie_age(release_date: datetime) -> MovieAge:
    """Classify movie by age category."""
    days_since_release = (datetime.now(timezone.utc) - release_date).days
    
    if days_since_release <= 60:
        return MovieAge.RECENT
    elif days_since_release <= 180:
        return MovieAge.ESTABLISHED
    elif days_since_release <= 365:
        return MovieAge.MATURE
    else:
        return MovieAge.ARCHIVED
```

### Checking if Refresh Needed

```python
def needs_tmdb_refresh(
    release_date: datetime,
    last_tmdb_update: Optional[datetime]
) -> bool:
    """Check if TMDB data needs refreshing."""
    
    # Never updated = always refresh
    if last_tmdb_update is None:
        return True
    
    # Get interval based on age
    interval_days = get_tmdb_refresh_interval(release_date)
    
    # Check if enough time has passed
    threshold = datetime.now(timezone.utc) - timedelta(days=interval_days)
    return last_tmdb_update < threshold
```

### Example Scenarios

#### Scenario 1: Recent Movie

```python
# Movie released 30 days ago
release_date = datetime.now(timezone.utc) - timedelta(days=30)

# Age: RECENT
age = get_movie_age(release_date)  # MovieAge.RECENT

# Refresh intervals
tmdb_interval = 5 days
omdb_interval = 5 days

# If last updated 6 days ago
last_update = datetime.now(timezone.utc) - timedelta(days=6)

# Needs refresh? YES (6 > 5)
needs_refresh = needs_tmdb_refresh(release_date, last_update)  # True
```

#### Scenario 2: Mature Movie

```python
# Movie released 300 days ago
release_date = datetime.now(timezone.utc) - timedelta(days=300)

# Age: MATURE
age = get_movie_age(release_date)  # MovieAge.MATURE

# Refresh intervals
tmdb_interval = 30 days
omdb_interval = 90 days

# If TMDB updated 25 days ago
last_tmdb = datetime.now(timezone.utc) - timedelta(days=25)
needs_tmdb = needs_tmdb_refresh(release_date, last_tmdb)  # False (25 < 30)

# If OMDB updated 100 days ago
last_omdb = datetime.now(timezone.utc) - timedelta(days=100)
needs_omdb = needs_omdb_refresh(release_date, last_omdb)  # True (100 > 90)
```

#### Scenario 3: Archived Movie

```python
# Movie released 500 days ago
release_date = datetime.now(timezone.utc) - timedelta(days=500)

# Age: ARCHIVED
age = get_movie_age(release_date)  # MovieAge.ARCHIVED

# Refresh intervals
tmdb_interval = 90 days
omdb_interval = 180 days

# Long intervals mean fewer updates = fewer API calls
```

## Data Freezing

For very stable old movies, we can "freeze" them to stop automatic refreshes entirely.

### Freezing Criteria

A movie can be frozen if **ALL** conditions are met:

1. **Age**: Must be ≥ 365 days since release
2. **Has been updated**: At least once for TMDB or OMDB
3. **Stability**: No data changes for 3 consecutive refresh cycles

### Why Freeze?

- **API savings**: No calls for stable movies
- **Focus resources**: Prioritize new/changing movies
- **Performance**: Faster refresh queries

### Implementation

```python
def should_freeze_movie(
    release_date: datetime,
    last_tmdb_update: Optional[datetime],
    last_omdb_update: Optional[datetime],
    consecutive_unchanged_cycles: int = 0
) -> bool:
    """Determine if movie should be frozen."""
    
    days_since_release = (datetime.now(timezone.utc) - release_date).days
    
    # Must be old enough
    if days_since_release < 365:
        return False
    
    # Must have been updated at least once
    if last_tmdb_update is None and last_omdb_update is None:
        return False
    
    # Must be stable
    if consecutive_unchanged_cycles >= 3:
        return True
    
    return False
```

### Freeze Example

```python
# Movie released 2 years ago
release_date = datetime.now(timezone.utc) - timedelta(days=730)

# Has been updated multiple times
last_tmdb = datetime.now(timezone.utc) - timedelta(days=100)
last_omdb = datetime.now(timezone.utc) - timedelta(days=200)

# Data hasn't changed in 3 update cycles
unchanged_cycles = 3

# Should freeze? YES
should_freeze = should_freeze_movie(
    release_date,
    last_tmdb,
    last_omdb,
    unchanged_cycles
)  # True

# Mark as frozen in database
db.execute(
    "UPDATE movies SET data_frozen = TRUE WHERE movie_id = ?",
    [movie_id]
)
```

### Unfreezing

Frozen movies can be manually unfrozen if needed:

```sql
-- Unfreeze a specific movie
UPDATE movies SET data_frozen = FALSE WHERE movie_id = 12345;

-- Unfreeze all movies from a specific year
UPDATE movies SET data_frozen = FALSE 
WHERE EXTRACT(YEAR FROM release_date) = 2020;
```

## SQL Query for Refresh Candidates

The system generates a SQL query to find movies needing refresh:

```sql
SELECT
    m.movie_id,
    m.tmdb_id,
    m.imdb_id,
    m.title,
    m.release_date,
    m.last_tmdb_update,
    m.last_omdb_update,
    m.data_frozen,
    DATEDIFF('day', m.release_date, CURRENT_DATE) as days_since_release
FROM movies m
WHERE 
    m.data_frozen = FALSE  -- Exclude frozen
    AND (
        -- Never refreshed
        m.last_full_refresh IS NULL
        
        -- Recent (0-60 days): TMDB every 5 days, OMDB every 5 days
        OR (
            DATEDIFF('day', m.release_date, CURRENT_DATE) <= 60
            AND (
                m.last_tmdb_update IS NULL
                OR DATEDIFF('day', m.last_tmdb_update, CURRENT_TIMESTAMP) >= 5
                OR m.last_omdb_update IS NULL
                OR DATEDIFF('day', m.last_omdb_update, CURRENT_TIMESTAMP) >= 5
            )
        )
        
        -- Established (60-180 days): TMDB every 15 days, OMDB every 30 days
        OR (
            DATEDIFF('day', m.release_date, CURRENT_DATE) > 60
            AND DATEDIFF('day', m.release_date, CURRENT_DATE) <= 180
            AND (
                m.last_tmdb_update IS NULL
                OR DATEDIFF('day', m.last_tmdb_update, CURRENT_TIMESTAMP) >= 15
                OR m.last_omdb_update IS NULL
                OR DATEDIFF('day', m.last_omdb_update, CURRENT_TIMESTAMP) >= 30
            )
        )
        
        -- Mature (180-365 days): TMDB every 30 days, OMDB every 90 days
        OR (
            DATEDIFF('day', m.release_date, CURRENT_DATE) > 180
            AND DATEDIFF('day', m.release_date, CURRENT_DATE) <= 365
            AND (
                m.last_tmdb_update IS NULL
                OR DATEDIFF('day', m.last_tmdb_update, CURRENT_TIMESTAMP) >= 30
                OR m.last_omdb_update IS NULL
                OR DATEDIFF('day', m.last_omdb_update, CURRENT_TIMESTAMP) >= 90
            )
        )
        
        -- Archived (>365 days): TMDB every 90 days, OMDB every 180 days
        OR (
            DATEDIFF('day', m.release_date, CURRENT_DATE) > 365
            AND (
                m.last_tmdb_update IS NULL
                OR DATEDIFF('day', m.last_tmdb_update, CURRENT_TIMESTAMP) >= 90
                OR m.last_omdb_update IS NULL
                OR DATEDIFF('day', m.last_omdb_update, CURRENT_TIMESTAMP) >= 180
            )
        )
    )
ORDER BY
    CASE WHEN m.last_full_refresh IS NULL THEN 0 ELSE 1 END,  -- Prioritize never-refreshed
    m.release_date DESC  -- Then newest first
LIMIT 100;  -- Configurable limit
```

## Refresh Plan Calculation

For each movie, we calculate what needs updating:

```python
def calculate_refresh_plan(movie: Dict[str, Any]) -> Dict[str, bool]:
    """Calculate what needs refreshing for a specific movie."""
    
    release_date = movie['release_date']
    last_tmdb = movie.get('last_tmdb_update')
    last_omdb = movie.get('last_omdb_update')
    
    return {
        'needs_tmdb': needs_tmdb_refresh(release_date, last_tmdb),
        'needs_omdb': needs_omdb_refresh(release_date, last_omdb),
        'needs_numbers': False  # Future implementation
    }
```

### Usage in Orchestrator

```python
# Get movies needing refresh
movies_df = orchestrator.get_movies_for_refresh(limit=100)

# Calculate plans for each
movies_df['refresh_plan'] = movies_df.apply(
    lambda row: calculate_refresh_plan(row.to_dict()),
    axis=1
)

# Separate by needs
needs_tmdb = movies_df[
    movies_df['refresh_plan'].apply(lambda x: x['needs_tmdb'])
]

needs_omdb = movies_df[
    movies_df['refresh_plan'].apply(lambda x: x['needs_omdb'])
]

# Fetch only what's needed
if not needs_tmdb.empty:
    await fetch_tmdb_data(needs_tmdb)

if not needs_omdb.empty:
    await fetch_omdb_data(needs_omdb)
```

## Benefits of This Strategy

### 1. **API Efficiency**

```
Traditional approach: Update all 10,000 movies daily
- TMDB calls: 10,000/day
- OMDB calls: 10,000/day
- Total: 20,000/day ❌ Exceeds limits

Age-based approach: Update subset based on age
- Recent (100 movies): Update every 5 days = 20/day
- Established (200): Update every 15-30 days = ~10/day
- Mature (300): Update every 30-90 days = ~5/day
- Archived (9,400): Update every 90-180 days = ~70/day
- Total: ~105/day ✅ Well under limits
```

### 2. **Data Freshness**

- New releases get frequent updates when they matter most
- Older movies checked less often (their data is stable)
- Best balance of freshness vs. efficiency

### 3. **Cost Optimization**

- Fewer API calls = lower costs
- Prioritize new content that users care about
- Don't waste calls on unchanging data

### 4. **Performance**

- Smaller batches = faster queries
- Frozen movies excluded from queries
- Focus computational resources on active movies

## Tuning the Strategy

### Adjust Intervals

Want more/less frequent updates? Modify thresholds:

```python
class RefreshThresholds:
    # More aggressive (more API calls)
    TMDB_RECENT = 3          # Was 5
    TMDB_ESTABLISHED = 10     # Was 15
    
    # More conservative (fewer API calls)
    TMDB_MATURE = 45          # Was 30
    TMDB_ARCHIVED = 120       # Was 90
```

### Adjust Age Boundaries

Change when movies transition between age categories:

```python
class RefreshThresholds:
    # Make "Recent" period shorter
    AGE_RECENT = 30           # Was 60
    
    # Extend "Mature" period
    AGE_MATURE = 540          # Was 365
```

### Adjust Freezing

Make freezing more/less aggressive:

```python
class RefreshThresholds:
    # More aggressive freezing
    FREEZE_MIN_AGE_DAYS = 180  # Was 365
    FREEZE_STABLE_CYCLES = 2    # Was 3
    
    # Less aggressive
    FREEZE_MIN_AGE_DAYS = 730   # 2 years
    FREEZE_STABLE_CYCLES = 5    # More cycles
```

## Monitoring Strategy Effectiveness

### Key Metrics

1. **Update Coverage**:

```sql
-- % of movies updated within their interval
SELECT 
    COUNT(CASE WHEN last_tmdb_update >= CURRENT_DATE - interval THEN 1 END) * 100.0 / COUNT(*)
FROM movies;
```

2. **Frozen Movie Count**:

```sql
SELECT COUNT(*), COUNT(*) * 100.0 / (SELECT COUNT(*) FROM movies) as pct
FROM movies WHERE data_frozen = TRUE;
```

3. **Age Distribution**:

```sql
SELECT 
    CASE 
        WHEN days <= 60 THEN 'Recent'
        WHEN days <= 180 THEN 'Established'
        WHEN days <= 365 THEN 'Mature'
        ELSE 'Archived'
    END as category,
    COUNT(*) as count
FROM (
    SELECT DATEDIFF('day', release_date, CURRENT_DATE) as days
    FROM movies
)
GROUP BY category;
```

4. **Daily API Calls** (estimate):

```sql
-- Movies due for TMDB update today
SELECT COUNT(*) FROM movies
WHERE data_frozen = FALSE
AND (
    last_tmdb_update IS NULL
    OR DATEDIFF('day', last_tmdb_update, CURRENT_DATE) >= [interval based on age]
);
```

## Best Practices

### 1. Start with Default Intervals

The default configuration is well-tested. Only adjust if you have specific needs.

### 2. Monitor API Usage

Track actual vs. estimated API calls to ensure you're within limits.

### 3. Batch Refresh Operations

Don't try to update everything at once:

```python
# Good: Steady daily batches
orchestrator.run_full_collection(refresh_limit=100)

# Bad: Massive one-time updates
orchestrator.run_full_collection(refresh_limit=10000)
```

### 4. Let Freezing Happen

Trust the freezing logic. Frozen movies save resources.

### 5. Manual Overrides When Needed

For specific high-priority movies:

```sql
-- Force update for specific movie
UPDATE movies 
SET last_tmdb_update = NULL, last_omdb_update = NULL
WHERE tmdb_id = 12345;

-- This movie will be picked up in next refresh
```

## Troubleshooting

### Problem: Too Many API Calls

**Solution**: Increase intervals or reduce refresh_limit

```python
# Option 1: Longer intervals
RefreshThresholds.TMDB_RECENT = 7  # Was 5

# Option 2: Smaller batches
refresh_limit=50  # Was 100
```

### Problem: Data Too Stale

**Solution**: Decrease intervals or unfreeze movies

```python
# Option 1: Shorter intervals
RefreshThresholds.TMDB_ARCHIVED = 60  # Was 90

# Option 2: Unfreeze old movies
UPDATE movies SET data_frozen = FALSE 
WHERE EXTRACT(YEAR FROM release_date) >= 2020;
```

### Problem: Never-Updated Movies

**Check**:

```sql
SELECT COUNT(*) FROM movies 
WHERE last_full_refresh IS NULL;
```

**Solution**: Run targeted refresh or increase limit

## Related Documentation

- [Data Collection Workflow](data-collection-workflow.md) - Overall collection process
- [TMDB Client](tmdb-client.md) - TMDB API details
- [OMDB Client](omdb-client.md) - OMDB API details
- [Data Orchestration](orchestration.md) - Orchestrator implementation
