# Configuration Guide

This directory contains environment-specific configuration files for the **Are You Not Entertained** project.

## Overview

The project uses a modern configuration system built with **Pydantic 2.x** that supports:
- ✅ Environment-specific YAML configs (development, staging, production)
- ✅ `.env` file for sensitive data (API keys, passwords)
- ✅ Type-safe configuration with validation
- ✅ Azure deployment compatibility
- ✅ FastAPI integration ready

## Configuration Priority

Settings are loaded in the following priority order (highest to lowest):

1. **Environment Variables** - Override everything
2. **`.env` File** - Sensitive data (API keys, DB URLs)
3. **YAML Config Files** - Environment-specific settings

## Quick Start

### 1. Set Up Your Environment File

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your actual API keys
# NEVER commit .env to version control!
```

### 2. Configure Your Environment

The `ENVIRONMENT` variable in your `.env` file determines which YAML config is loaded:

- `development` → `configs/development.yaml`
- `staging` → `configs/staging.yaml`
- `production` → `configs/production.yaml`

### 3. Use Settings in Your Code

```python
# Import the settings singleton
from src.core.config import settings

# Access configuration
api_key = settings.tmdb_api_key
db_url = settings.db_url
log_level = settings.log_level

# Check environment
if settings.is_production():
    print("Running in production mode")
```

## File Descriptions

### Environment YAML Files

- **`development.yaml`** - Local development settings
  - Debug mode enabled
  - Verbose logging
  - Local server configuration
  - CORS for localhost

- **`staging.yaml`** - Pre-production testing
  - Debug mode enabled (for troubleshooting)
  - JSON logging (like production)
  - Azure-compatible settings
  - Staging URLs

- **`production.yaml`** - Live deployment
  - Debug mode disabled
  - JSON logging for cloud monitoring
  - Production-optimized batch sizes
  - Strict CORS settings

### Sensitive Data (.env)

Store in `.env` file (NOT in YAML):
- `TMDB_API_KEY` - The Movie Database API key
- `OMDB_API_KEY` - Open Movie Database API key
- `DB_URL` - Database connection string
- `AZURE_SUBSCRIPTION_ID` - Azure credentials
- Any other secrets

## Adding New Configuration

### Adding a Non-Sensitive Setting

1. Add field to `src/core/config/settings.py`:
```python
new_setting: str = Field(
    default="default_value",
    description="Description of the setting"
)
```

2. Add to YAML files (e.g., `development.yaml`):
```yaml
new_setting: "custom_value"
```

### Adding a Sensitive Setting

1. Add field to `src/core/config/settings.py`:
```python
secret_key: Optional[str] = Field(
    default=None,
    description="Secret key for encryption"
)
```

2. Add to `.env.example`:
```bash
# Secret Key
SECRET_KEY=your_secret_key_here
```

3. Users add actual value to their local `.env`

## Environment Variables Override

You can override any setting via environment variables:

```bash
# Override in shell
export LOG_LEVEL=DEBUG
export BATCH_SIZE=50

# Or in .env file
LOG_LEVEL=DEBUG
BATCH_SIZE=50
```

## Best Practices

### ✅ DO:
- Keep sensitive data in `.env` (never commit!)
- Use YAML files for environment-specific non-sensitive config
- Update `.env.example` when adding new environment variables
- Use type hints and validation in `settings.py`
- Document new settings with descriptions

### ❌ DON'T:
- Commit `.env` file to version control
- Put API keys or passwords in YAML files
- Hardcode configuration values in code
- Use different field names in YAML vs settings.py

## Azure Deployment

For Azure deployment:

1. **App Service Configuration**
   - Set environment variables in Azure Portal
   - Variables override YAML and `.env`

2. **Key Vault Integration** (Recommended for production)
   ```python
   # Future: Add Azure Key Vault integration
   # Secrets loaded from Key Vault override all other sources
   ```

## Troubleshooting

### Settings not loading from YAML?

Check:
1. `ENVIRONMENT` variable is set correctly
2. YAML file exists in `configs/` directory
3. YAML syntax is valid (no tabs, proper indentation)

### API keys not working?

Check:
1. `.env` file exists in project root
2. Variable names match exactly (case-insensitive)
3. No quotes around values in `.env`

### Import errors?

```python
# Correct import
from src.core.config import settings

# Also valid
from src.core.config import get_settings
settings = get_settings()
```

## Example `.env` File

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

DB_URL=postgresql://user:password@localhost:5432/movies

TMDB_API_KEY=your_actual_tmdb_key
OMDB_API_KEY=your_actual_omdb_key
```

## Migration from Old Config

The old `config/config_loader.py` system has been replaced. Update imports:

```python
# Old way ❌
from config.config_loader import load_config
api_key = load_config("TMDB_API_KEY")

# New way ✅
from src.core.config import settings
api_key = settings.tmdb_api_key
```

## Support

For questions or issues with configuration:
1. Check this README
2. Review `.env.example` for required variables
3. Inspect `src/core/config/settings.py` for all available settings
