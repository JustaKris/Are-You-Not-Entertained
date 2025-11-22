# Path Configuration Migration Guide

## Overview

The project has been modernized to follow Python best practices by consolidating all configuration (including paths) into a single Pydantic Settings class. This provides type safety, validation, and centralized configuration management.

## What Changed

### Before (Old Approach)

```python
# Separate modules for paths and settings
from ayne.core.paths import DATA_RAW_DIR, DATA_INTERMEDIATE_DIR, MODELS_DIR
from ayne.core.config import settings

# Paths were hard-coded constants
db_path = DATA_INTERMEDIATE_DIR / "movies.duckdb"
```

### After (Modern Approach)

```python
# Everything in one place
from ayne.core.config import settings

# Paths are now part of settings with auto-initialization
db_path = settings.duckdb_path
raw_data = settings.data_raw_dir
models = settings.models_dir
```

## Benefits

1. **Type Safety**: Pydantic validates all paths at startup
2. **Centralized**: One import for all configuration
3. **Environment-Aware**: Paths can be customized per environment
4. **Auto-Creation**: Directories are created automatically
5. **Modern**: Follows current Python best practices (2024+)

## Available Path Settings

All paths in `settings`:

```python
from ayne.core.config import settings

# Core directories
settings.project_root          # Project root directory
settings.data_dir             # data/
settings.data_raw_dir         # data/raw/
settings.data_intermediate_dir # data/intermediate/
settings.data_processed_dir   # data/processed/
settings.models_dir           # models/
settings.logs_dir             # logs/

# Database
settings.duckdb_path          # data/intermediate/movies.duckdb

# API keys & other settings
settings.tmdb_api_key
settings.omdb_api_key
settings.log_level
settings.use_json_logging
```

## Migration Steps

### For New Code

✅ **Do this:**

```python
from ayne.core.config import settings

# Access paths via settings
output_path = settings.data_raw_dir / "output.parquet"
db = DuckDBClient()  # Uses settings.duckdb_path automatically
```

❌ **Don't do this:**

```python
from ayne.core.paths import DATA_RAW_DIR  # Deprecated
```

### For Existing Code

The old `src.core.paths` module still works for **backward compatibility**, but is **deprecated**:

```python
# This still works but is deprecated
from ayne.core.paths import DATA_RAW_DIR, DATA_INTERMEDIATE_DIR

# Behind the scenes, it imports from settings
# So you get the same paths, just through a deprecated interface
```

**Recommendation**: Update imports when you touch a file, but no rush to update everything at once.

## Directory Auto-Creation

Previously, you had to call `ensure_directories()`. Now directories are **automatically created** when settings loads:

```python
# Old way (no longer needed)
from ayne.core.paths import ensure_directories
ensure_directories()

# New way (automatic)
from ayne.core.config import settings
# Directories already exist!
```

## Customizing Paths

You can override paths via environment variables or YAML config:

### Via Environment Variable

```bash
# .env file
DATA_INTERMEDIATE_DIR=/custom/path/to/data
DUCKDB_PATH=/custom/db/movies.duckdb
```

### Via YAML Config

```yaml
# configs/development.yaml
data_intermediate_dir: "./custom_data/intermediate"
duckdb_path: "./custom_data/movies.duckdb"
```

## Code Examples

### Database Client

```python
from ayne.database.duckdb_client import DuckDBClient
from ayne.core.config import settings

# Uses settings.duckdb_path by default
db = DuckDBClient()

# Or override
db = DuckDBClient(db_path="/custom/path/db.duckdb")
```

### API Clients

```python
from ayne.data_collection.tmdb_client import TMDBClient
from ayne.data_collection.omdb_client import OMDBClient
from ayne.core.config import settings

# Uses settings.data_raw_dir / "tmdb" by default
tmdb = TMDBClient()

# Or override
tmdb = TMDBClient(output_dir="/custom/output/tmdb")
```

### Data Processing

```python
from ayne.core.config import settings
import pandas as pd

# Read from intermediate
df = pd.read_parquet(settings.data_intermediate_dir / "processed.parquet")

# Write to processed
df.to_parquet(settings.data_processed_dir / "final.parquet")
```

## FAQ

**Q: Do I need to update all my code immediately?**  
A: No, the old `src.core.paths` imports still work. Update gradually as you touch files.

**Q: Will my existing scripts break?**  
A: No, backward compatibility is maintained. Old code continues to work.

**Q: Can I still use custom paths?**  
A: Yes, all clients accept optional `output_dir` or `db_path` parameters.

**Q: Are directories still auto-created?**  
A: Yes, but now it happens automatically via `Settings.model_post_init()`.

**Q: What if I need a path not in settings?**  
A: Either add it to Settings, or compute it: `settings.data_dir / "custom_subdir"`

## Summary

✅ **Modern**: Pydantic Settings for all configuration  
✅ **Type-Safe**: Validated paths with proper types  
✅ **Auto-Init**: Directories created automatically  
✅ **Flexible**: Override via env vars or YAML  
✅ **Compatible**: Old imports still work  

**Recommended Migration Pattern**:

1. New code: Use `from ayne.core.config import settings`
2. Old code: Update imports when you touch the file
3. No rush: Backward compatibility maintained
