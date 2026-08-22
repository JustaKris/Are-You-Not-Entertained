# Database Monitoring and Auditing

Guide for monitoring database health, auditing data quality, and troubleshooting refresh strategy issues.

## Overview

The project includes two Jupyter notebooks for database monitoring:

- **`00_database_monitoring.ipynb`**: Daily operational monitoring
- **`01_database_audit.ipynb`**: Comprehensive quality auditing

Both notebooks are located in `notebooks/database/`.

## Daily Monitoring (`00_database_monitoring.ipynb`)

### Purpose

Quick health check of database state and recent activity.

### What It Covers

1. **Database Overview**
   - Total movie count
   - Date range coverage
   - ID coverage (TMDB/IMDb)
   - Enrichment percentages

2. **Enrichment Status by Year**
   - Movies per year with TMDB/OMDB data
   - Visual charts of enrichment coverage
   - Completion rates by year

3. **Movies Due for Update**
   - Movies needing refresh by year
   - Never-refreshed vs overdue counts
   - Top years needing attention

4. **Data Quality Metrics**
   - Field completeness percentages
   - Missing data identification
   - Quality trends over time

5. **Recent Update Activity**
   - TMDB/OMDB updates (last 14 days)
   - Full refresh counts
   - Activity trends and patterns

6. **Custom Queries**
   - Top genres
   - Monthly growth
   - Ad-hoc analysis

### When to Use

- **Daily**: Quick health check before/after collection runs
- **After major updates**: Verify expected changes
- **Before ML training**: Ensure data quality
- **Troubleshooting**: Identify gaps or issues

### Example Usage

```python
# Run the notebook to see:
# - Total movies: 32,534
# - TMDB enriched: 100%
# - OMDB enriched: 11.6%
# - Movies due for update: 462
# - Recent activity: 150 updates in last 14 days
```

## Quality Auditing (`01_database_audit.ipynb`)

### Purpose

Comprehensive data quality and refresh strategy validation.

### What It Audits

#### 1. Refresh Strategy Validation

**Refresh Flag Consistency:**

- Verifies `last_full_refresh` is set correctly
- Checks for movies with both updates but missing flag
- Validates flag matches actual enrichment state

**Freezing Logic Validation:**

- Confirms only archived movies (>365 days) are frozen
- Verifies no recent/established/mature movies frozen
- Analyzes frozen percentage by age category

**Consecutive Unchanged Tracking:**

- Distribution of unchanged cycle counts
- Validates movies frozen at correct threshold (3+ cycles)
- Identifies movies frozen prematurely

#### 2. Data Completeness

**Core Movie Fields:**

- Title completeness
- Release date coverage
- TMDB/IMDb ID coverage
- Update timestamp presence

**TMDB Enrichment Fields:**

- Overview text
- Genres
- Production companies/countries
- Runtime and vote counts
- Spoken languages

**OMDB Enrichment Fields:**

- Age ratings
- IMDb ratings and votes
- Metascores
- Awards
- Box office data
- Language/country info

#### 3. Timestamp Consistency

- Verifies update timestamps match data presence
- Identifies orphaned timestamps (timestamp but no data)
- Finds missing timestamps (data but no timestamp)
- Ensures referential integrity

#### 4. API Enrichment Coverage

- Coverage percentages by year (last 20 years)
- Identifies years with low enrichment
- Visual trends of TMDB/OMDB coverage
- Highlights gaps needing attention

#### 5. Data Quality Outliers

**Suspicious Ratings:**

- Large discrepancies between TMDB and IMDb ratings (>2.5 points)
- Suspiciously high ratings (>9.5)
- Potential data quality issues

**Missing Critical Fields:**

- Fully refreshed movies missing key data
- Movies flagged for manual review
- Incomplete enrichment identification

#### 6. Overall Health Score

Calculates a 0-100 health score based on:

- Refresh flag consistency (target: 100%)
- Freezing accuracy (target: 100%)
- Data completeness (target: >95%)
- Timestamp consistency (target: 100%)

Generates prioritized recommendations for improvements.

### When to Use

- **Weekly**: Regular health checks during active development
- **Monthly**: Production monitoring and maintenance
- **After migrations**: Verify database state post-update
- **Before releases**: Ensure data quality meets standards
- **Troubleshooting**: Deep-dive into suspected issues

### Example Output

```
OVERALL HEALTH SCORE: 96.8/100

✅ Refresh Consistency:      100.0/100
✅ Freezing Accuracy:        100.0/100
⚠️  Data Completeness:        89.5/100
✅ Timestamp Consistency:    99.0/100

RECOMMENDED ACTIONS:
1. 📊 Prioritize enrichment for movies with incomplete core fields
2. 📅 Focus OMDB enrichment on 3 years with <70% coverage
```

## Key Metrics to Monitor

### Health Indicators

#### 1. Enrichment Coverage

**Target**: 90%+ for recent movies (last 5 years)

```sql
SELECT
    COUNT(CASE WHEN last_tmdb_update IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as tmdb_pct,
    COUNT(CASE WHEN last_omdb_update IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as omdb_pct
FROM movies
WHERE release_date >= DATE_SUB(CURRENT_DATE, INTERVAL 5 YEAR);
```

#### 2. Refresh Flag Accuracy

**Target**: 100% (all movies with both updates have `last_full_refresh` set)

```sql
SELECT
    COUNT(*) as has_both,
    COUNT(CASE WHEN last_full_refresh IS NOT NULL THEN 1 END) as has_flag,
    COUNT(CASE WHEN last_full_refresh IS NULL THEN 1 END) as missing_flag
FROM movies
WHERE last_tmdb_update IS NOT NULL AND last_omdb_update IS NOT NULL;
```

#### 3. Frozen Movie Percentage

**Target**: <10% of total movies

```sql
SELECT
    COUNT(CASE WHEN data_frozen = TRUE THEN 1 END) as frozen,
    COUNT(*) as total,
    COUNT(CASE WHEN data_frozen = TRUE THEN 1 END) * 100.0 / COUNT(*) as frozen_pct
FROM movies;
```

#### 4. Movies Due for Update

**Target**: <5% of database

```sql
-- Movies overdue for refresh
SELECT COUNT(*) FROM movies
WHERE data_frozen = FALSE
AND (
    (DATEDIFF('day', release_date, CURRENT_DATE) <= 60 AND DATEDIFF('day', last_tmdb_update, CURRENT_DATE) > 5)
    OR (DATEDIFF('day', release_date, CURRENT_DATE) > 60 AND DATEDIFF('day', release_date, CURRENT_DATE) <= 180
        AND DATEDIFF('day', last_tmdb_update, CURRENT_DATE) > 15)
    -- ... etc for other age categories
);
```

### Performance Indicators

#### 1. Daily API Call Estimate

Track to stay within API limits:

```sql
-- TMDB calls needed today
SELECT COUNT(*) as tmdb_calls_needed
FROM movies
WHERE data_frozen = FALSE
AND (
    last_tmdb_update IS NULL
    OR (DATEDIFF('day', release_date, CURRENT_DATE) <= 60 AND DATEDIFF('day', last_tmdb_update, CURRENT_DATE) >= 5)
    OR (DATEDIFF('day', release_date, CURRENT_DATE) BETWEEN 61 AND 180 AND DATEDIFF('day', last_tmdb_update, CURRENT_DATE) >= 15)
    OR (DATEDIFF('day', release_date, CURRENT_DATE) BETWEEN 181 AND 365 AND DATEDIFF('day', last_tmdb_update, CURRENT_DATE) >= 30)
    OR (DATEDIFF('day', release_date, CURRENT_DATE) > 365 AND DATEDIFF('day', last_tmdb_update, CURRENT_DATE) >= 90)
);
```

#### 2. Unchanged Refresh Distribution

Monitor freezing efficiency:

```sql
SELECT
    consecutive_unchanged_refreshes as cycles,
    COUNT(*) as count,
    COUNT(CASE WHEN data_frozen = TRUE THEN 1 END) as frozen
FROM movies
GROUP BY consecutive_unchanged_refreshes
ORDER BY consecutive_unchanged_refreshes;
```

#### 3. Recent Activity Trends

```sql
SELECT
    DATE(last_tmdb_update) as date,
    COUNT(*) as updates
FROM movies
WHERE last_tmdb_update >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
GROUP BY date
ORDER BY date DESC;
```

## Troubleshooting Guide

### Issue: High Frozen Movie Count

**Symptom**: >20% of movies frozen

**Diagnosis**:

```sql
-- Check frozen distribution by age
SELECT
    CASE
        WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 60 THEN 'Recent'
        WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 180 THEN 'Established'
        WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 365 THEN 'Mature'
        ELSE 'Archived'
    END as age_category,
    COUNT(CASE WHEN data_frozen = TRUE THEN 1 END) as frozen,
    COUNT(*) as total
FROM movies
GROUP BY age_category;
```

**Solutions**:

1. **Unfreeze non-archived movies** (should never happen):

   ```sql
   UPDATE movies SET data_frozen = FALSE, consecutive_unchanged_refreshes = 0
   WHERE DATEDIFF('day', release_date, CURRENT_DATE) < 365;
   ```

2. **Reset archived movies if needed**:

   ```sql
   -- Unfreeze all archived movies
   UPDATE movies SET data_frozen = FALSE, consecutive_unchanged_refreshes = 0
   WHERE DATEDIFF('day', release_date, CURRENT_DATE) >= 365;
   ```

3. **Force refresh frozen movies**:

   ```powershell
   ayne collect daily --include-frozen
   ```

### Issue: Missing `last_full_refresh` Flags

**Symptom**: Movies have both updates but `last_full_refresh` is NULL

**Diagnosis**:

```sql
SELECT COUNT(*) as affected
FROM movies
WHERE last_tmdb_update IS NOT NULL
AND last_omdb_update IS NOT NULL
AND last_full_refresh IS NULL;
```

**Solution**: Run the canonical database validator:

```powershell
uv run ayne validate database
```

Structural, relationship, and domain findings are blocking errors. Stale TMDB and OMDB
records are warnings by default because old historical data can still be valid. Treat
freshness warnings as failures for a release check:

```powershell
uv run ayne validate database --strict-freshness
```

For a specific finding, use the code in the validation table to choose a focused query.
For example, to inspect missing full-refresh flags:

```sql
UPDATE movies
SET last_full_refresh = GREATEST(last_tmdb_update, last_omdb_update)
WHERE last_tmdb_update IS NOT NULL
AND last_omdb_update IS NOT NULL
AND last_full_refresh IS NULL;
```

Do not patch the schema manually. If the finding is caused by a schema change, add a
numbered migration under `src/ayne/database/migrations/` and run `uv run ayne db migrate`.

### Issue: Low Enrichment Coverage

**Symptom**: <80% OMDB coverage for recent years

**Diagnosis**:

```sql
SELECT
    EXTRACT(YEAR FROM release_date) as year,
    COUNT(*) as total,
    COUNT(CASE WHEN last_omdb_update IS NOT NULL THEN 1 END) as enriched,
    COUNT(CASE WHEN last_omdb_update IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as pct
FROM movies
WHERE release_date >= DATE_SUB(CURRENT_DATE, INTERVAL 5 YEAR)
GROUP BY year
ORDER BY year DESC;
```

**Solutions**:

1. **Target recent years**:

   ```powershell
   ayne omdb enrich --min-year 2023 --max-movies 1000
   ```

2. **Increase daily limits**:

   ```powershell
   ayne collect daily --omdb-limit 500
   ```

3. **Check for missing IMDb IDs**:

   ```sql
   -- Movies that can't be enriched (no IMDb ID)
   SELECT COUNT(*) FROM movies
   WHERE imdb_id IS NULL AND last_tmdb_update IS NOT NULL;
   ```

### Issue: Timestamp Inconsistencies

**Symptom**: Data present but no update timestamp, or vice versa

**Diagnosis**:

```sql
-- Orphaned TMDB timestamps
SELECT COUNT(*) FROM movies m
LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
WHERE m.last_tmdb_update IS NOT NULL AND t.tmdb_id IS NULL;

-- Missing TMDB timestamps
SELECT COUNT(*) FROM movies m
LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
WHERE t.tmdb_id IS NOT NULL AND m.last_tmdb_update IS NULL;
```

**Solutions**:

1. **Remove orphaned timestamps**:

   ```sql
   UPDATE movies SET last_tmdb_update = NULL
   WHERE movie_id IN (
       SELECT m.movie_id FROM movies m
       LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
       WHERE m.last_tmdb_update IS NOT NULL AND t.tmdb_id IS NULL
   );
   ```

2. **Add missing timestamps from data**:

   ```sql
   UPDATE movies SET last_tmdb_update = CURRENT_TIMESTAMP
   WHERE movie_id IN (
       SELECT m.movie_id FROM movies m
       LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
       WHERE t.tmdb_id IS NOT NULL AND m.last_tmdb_update IS NULL
   );
   ```

## Best Practices

### 1. Regular Monitoring Schedule

- **Daily**: Quick check with `00_database_monitoring.ipynb` before collection runs
- **Weekly**: Full audit with `01_database_audit.ipynb` during active development
- **Monthly**: Comprehensive audit in production

### 2. Proactive Maintenance

- Monitor frozen movie percentage (keep <15%)
- Track enrichment coverage (maintain >90% for recent movies)
- Watch for API quota issues (daily call estimates)
- Review consecutive unchanged distributions

### 3. Documentation

- Log audit results and trends
- Document any manual interventions
- Track health score over time
- Note recommendations implemented

### 4. Automation

Consider scheduling monitoring:

Use Windows Task Scheduler for recurring notebook runs. Create a task with `pwsh.exe`
as the program, set the repository root as **Start in**, and use an argument such as:

```powershell
-NoProfile -Command "uv run jupyter nbconvert --execute notebooks/database/00_database_monitoring.ipynb --to html --output ('reports/daily_{0}.html' -f (Get-Date -Format yyyyMMdd))"
```

Create a second weekly task with the same settings and replace the notebook path with
`notebooks/database/01_database_audit.ipynb` and the output prefix with `audit`.

## Related Documentation

- [Refresh Strategy](../reference/refresh-strategy.md) - Age-based refresh intervals
- [Database Schema](../reference/database.md) - Table structures
- [CLI Guide](cli-guide.md) - Collection commands
- [Data Collection Workflow](data-collection-workflow.md) - Overall process

## Quick Reference

### Health Check Checklist

- [ ] Overall health score >90
- [ ] Refresh flag consistency 100%
- [ ] Freezing accuracy 100%
- [ ] Data completeness >95%
- [ ] Timestamp consistency >98%
- [ ] Frozen movies <15% of total
- [ ] Recent movies (last 5 years) >90% OMDB enriched
- [ ] Movies due for update <5% of database
- [ ] No suspicious ratings requiring review
- [ ] No critical fields missing in enriched movies

### Common Queries

```sql
-- Quick health summary
SELECT
    COUNT(*) as total_movies,
    COUNT(CASE WHEN data_frozen = TRUE THEN 1 END) * 100.0 / COUNT(*) as frozen_pct,
    COUNT(CASE WHEN last_full_refresh IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as fully_refreshed_pct,
    AVG(consecutive_unchanged_refreshes) as avg_unchanged_cycles
FROM movies;

-- Recent enrichment activity
SELECT
    DATE(last_tmdb_update) as date,
    COUNT(*) as tmdb_updates,
    COUNT(CASE WHEN last_omdb_update = last_tmdb_update THEN 1 END) as omdb_updates
FROM movies
WHERE last_tmdb_update >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
GROUP BY date
ORDER BY date DESC;

-- Top issues to address
SELECT
    'Missing full refresh flags' as issue,
    COUNT(*) as count
FROM movies
WHERE last_tmdb_update IS NOT NULL AND last_omdb_update IS NOT NULL AND last_full_refresh IS NULL

UNION ALL

SELECT
    'Non-archived frozen movies' as issue,
    COUNT(*) as count
FROM movies
WHERE data_frozen = TRUE AND DATEDIFF('day', release_date, CURRENT_DATE) < 365

UNION ALL

SELECT
    'Movies due for update' as issue,
    COUNT(*) as count
FROM movies
WHERE data_frozen = FALSE
AND last_full_refresh IS NOT NULL
AND DATEDIFF('day', last_tmdb_update, CURRENT_DATE) >
    CASE
        WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 60 THEN 5
        WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 180 THEN 15
        WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 365 THEN 30
        ELSE 90
    END;
```
