# Configuration System Migration Guide

## Summary

The project has been migrated from the old `config/config_loader.py` system to a modern **Pydantic 2.x** based configuration system.

## What Changed

### Old System ❌
```python
from config.config_loader import load_config

api_key = load_config("TMDB_API_KEY")
db_url = load_config("DB_URL")
```

### New System ✅
```python
from ayne.core.config import settings

api_key = settings.tmdb_api_key
db_url = settings.db_url
```

## Key Improvements

1. **Type Safety** - All settings are type-checked and validated
2. **Environment Support** - Different configs for dev/staging/production
3. **Better Organization** - Sensitive data in `.env`, config in YAML
4. **Azure Ready** - Compatible with Azure App Service and Key Vault
5. **FastAPI Integration** - Ready for future FastAPI deployment
6. **Auto-completion** - IDE support for all settings

## New File Structure

```
Are-You-Not-Entertained/
├── .env                          # Your local sensitive data (DO NOT COMMIT)
├── .env.example                  # Template for .env (safe to commit)
├── configs/
│   ├── development.yaml          # Dev environment settings
│   ├── staging.yaml              # Staging environment settings
│   ├── production.yaml           # Production environment settings
│   └── README.md                 # Configuration documentation
└── src/
    └── core/
        └── config/
            ├── __init__.py       # Exports settings singleton
            ├── settings.py       # Pydantic settings model
            └── config_loader.py  # YAML loading logic
```

## Migration Steps for Developers

### 1. Install New Dependencies

```bash
# If not already installed
pip install pydantic pydantic-settings pyyaml python-dotenv

# Or update from pyproject.toml
pip install -e .
```

### 2. Create Your `.env` File

```bash
# Copy the example
cp .env.example .env

# Edit .env and add your actual values
# IMPORTANT: Never commit .env to git!
```

**Example `.env`:**
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

DB_URL=postgresql://localhost:5432/movies
TMDB_API_KEY=your_actual_tmdb_api_key
OMDB_API_KEY=your_actual_omdb_api_key
```

### 3. Update Your Code

Replace all instances of `load_config()`:

**Before:**
```python
from config.config_loader import load_config

def get_movies():
    api_key = load_config("TMDB_API_KEY")
    db_url = load_config("DB_URL")
    # ... rest of code
```

**After:**
```python
from ayne.core.config import settings

def get_movies():
    api_key = settings.tmdb_api_key
    db_url = settings.db_url
    # ... rest of code
```

### 4. Update Notebooks

**Before:**
```python
from config.config_loader import load_config

session = init_db_session(load_config("DB_URL"))
```

**After:**
```python
from ayne.core.config import settings

session = init_db_session(settings.db_url)
```

## Available Settings

All settings are defined in `src/core/config/settings.py`. Common ones include:

| Setting | Type | Description |
|---------|------|-------------|
| `environment` | str | Current environment (development/staging/production) |
| `debug` | bool | Debug mode flag |
| `log_level` | str | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `db_url` | str | Database connection URL |
| `tmdb_api_key` | str | TMDB API key |
| `omdb_api_key` | str | OMDB API key |
| `batch_size` | int | Data processing batch size |
| `random_seed` | int | Random seed for reproducibility |

See `src/core/config/settings.py` for the complete list.

## Configuration Priority

Settings are loaded in this order (highest priority first):

1. **Environment Variables** - Can override everything
2. **`.env` File** - Your local sensitive data
3. **YAML Config** - Environment-specific settings (development.yaml, etc.)
4. **Defaults** - Defined in settings.py

## Common Patterns

### Basic Usage
```python
from ayne.core.config import settings

# Access any setting
print(f"Environment: {settings.environment}")
print(f"Debug mode: {settings.debug}")
```

### Environment Checks
```python
from ayne.core.config import settings

if settings.is_production():
    # Production-specific logic
    pass
elif settings.is_development():
    # Development-specific logic
    pass
```

### Reload Settings (for testing)
```python
from ayne.core.config import reload_settings

# Reload with different environment
settings = reload_settings(environment="production")
```

## Troubleshooting

### "Settings not loading from .env"

**Solution:** Make sure:
- `.env` file is in the project root
- Variable names match exactly (case-insensitive)
- No quotes around values

### "Import error: cannot import settings"

**Solution:**
```python
# Correct import
from ayne.core.config import settings

# NOT this
from config.config_loader import load_config  # Old system
```

### "YAML file not found"

**Solution:** Check:
- `ENVIRONMENT` variable is set correctly in `.env`
- YAML file exists in `configs/` directory
- YAML filename matches environment (e.g., `development.yaml`)

## Files Migrated

All the following files have been updated to use the new system:

- ✅ `src/data_collection/omdb.py`
- ✅ `src/data_collection/tmdb.py`
- ✅ `scripts/update_db.py`
- ✅ `main.py`
- ✅ `database/utils.py`
- ✅ `notebooks/01_movies_data_full_imputation.ipynb`

## Removed Files

- ❌ `config/config_loader.py` - Replaced by new system
- ❌ `config/__init__.py` - No longer needed

## Adding New Configuration

### For Non-Sensitive Values (use YAML):

1. Add to `src/core/config/settings.py`:
```python
new_feature_flag: bool = Field(
    default=False,
    description="Enable new feature"
)
```

2. Add to `configs/development.yaml`:
```yaml
new_feature_flag: true
```

### For Sensitive Values (use .env):

1. Add to `src/core/config/settings.py`:
```python
api_secret: Optional[str] = Field(
    default=None,
    description="Secret API key"
)
```

2. Add to `.env.example`:
```bash
# API Secret Key
API_SECRET=your_secret_here
```

3. Add to your local `.env`:
```bash
API_SECRET=actual_secret_value
```

## Need Help?

- Check `configs/README.md` for detailed configuration guide
- Review `.env.example` for all available environment variables
- See `src/core/config/settings.py` for all settings and their types
- Read existing code for usage examples

## Benefits for Azure Deployment

The new system is designed for cloud deployment:

1. **Environment Variables** - Azure App Service can inject settings
2. **JSON Logging** - Enabled in production for Azure Monitor
3. **Flexible** - Can use Azure Key Vault for secrets
4. **Type Safe** - Catches configuration errors before deployment
