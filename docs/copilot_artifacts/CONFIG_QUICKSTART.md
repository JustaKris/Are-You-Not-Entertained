# Quick Start: New Configuration System

## Setup (5 minutes)

### 1. Create Your `.env` File

```bash
cp .env.example .env
```

Edit `.env` and add your actual API keys:

```bash
ENVIRONMENT=development
TMDB_API_KEY=your_actual_key_here
OMDB_API_KEY=your_actual_key_here
DB_URL=postgresql://localhost:5432/movies
```

### 2. Install Dependencies

```bash
pip install pydantic pydantic-settings pyyaml
# Or just:
pip install -e .
```

### 3. Use in Your Code

```python
from ayne.core.config import settings

# That's it! Use settings anywhere:
api_key = settings.tmdb_api_key
db_url = settings.db_url
```

## What You Get

✅ **Type-safe configuration** - Autocomplete & validation  
✅ **Environment support** - Different configs for dev/staging/prod  
✅ **Secure** - Sensitive data in `.env`, never in code  
✅ **Azure-ready** - Works with App Service & Key Vault  
✅ **FastAPI-ready** - For future API deployment  

## Files Created

```
.env.example              # Template (commit this)
configs/
  ├── development.yaml    # Dev config
  ├── staging.yaml        # Staging config  
  ├── production.yaml     # Production config
  └── README.md           # Full config docs
src/core/config/
  ├── __init__.py         # Exports settings
  ├── settings.py         # Settings model
  └── config_loader.py    # YAML loader
```

## Examples

### Get API Keys

```python
from ayne.core.config import settings

tmdb_key = settings.tmdb_api_key
omdb_key = settings.omdb_api_key
```

### Check Environment

```python
if settings.is_production():
    print("Running in production")
```

### Get Database URL

```python
db_url = settings.db_url
session = init_db_session(db_url)
```

## Need More Info?

- **Configuration details**: `configs/README.md`
- **Migration from old system**: `MIGRATION_GUIDE.md`
- **All settings**: `src/core/config/settings.py`
- **Example values**: `.env.example`

## Important

⚠️ **Never commit `.env` to git!** It contains your secrets.  
✅ **Do commit `.env.example`** - It's the template for others.
