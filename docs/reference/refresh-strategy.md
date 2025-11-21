# Refresh Strategy

> **Status**: Template - Content to be filled in

Intelligent data refresh strategy based on movie age and last update timestamps.

## Overview

Movies are refreshed at different intervals based on their age since release:

- **Recent** (0-60 days): Frequent updates
- **Established** (60-180 days): Moderate updates
- **Mature** (180-365 days): Less frequent updates
- **Archived** (>365 days): Infrequent updates

## Refresh Intervals

### TMDB Data

- Recent: Every 5 days
- Established: Every 15 days
- Mature: Every 30 days
- Archived: Every 90 days

### OMDB Data

- Recent: Every 5 days
- Established: Every 30 days
- Mature: Every 90 days
- Archived: Every 180 days

### Box Office Data (The Numbers)

- Recent: Every 5 days
- Established: Every 30 days
- Mature: Every 90 days
- Archived: Every 180 days

## Data Freezing

Movies can be "frozen" to stop automatic refreshes when:

- Data hasn't changed across multiple refresh cycles
- Movie is old and stable
- Manual override

## Usage

```python
from src.data_collection.refresh_strategy import calculate_refresh_plan

movie = {
    'release_date': '2024-01-15',
    'last_tmdb_update': '2024-11-01',
    'last_omdb_update': None,
    'data_frozen': False
}

plan = calculate_refresh_plan(movie)
# Returns: {'needs_tmdb': True, 'needs_omdb': True, 'reason': 'recent movie'}
```

## Related Components

- [Data Orchestration](orchestration.md)
- [Database](database.md)
