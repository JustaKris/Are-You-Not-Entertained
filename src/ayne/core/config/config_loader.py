"""YAML/JSON configuration file loaders for the Are You Not Entertained project.

This module handles loading environment-specific configuration from YAML files
and merging them with Pydantic settings.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from ayne.core.config.settings import Settings


def load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        path: Path to the YAML configuration file

    Returns:
        Dictionary containing the configuration

    Raises:
        FileNotFoundError: If the YAML file doesn't exist
        yaml.YAMLError: If the YAML file is malformed
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        return config or {}


def get_config_path(environment: str, configs_dir: Optional[Path] = None) -> Path:
    """Get the path to the environment-specific config file.

    Args:
        environment: Environment name (development, staging, production)
        configs_dir: Optional custom configs directory path

    Returns:
        Path to the YAML config file
    """
    if configs_dir is None:
        # Default to project root / configs
        # From src/ayne/core/config/config_loader.py, go up 4 levels to reach project root
        project_root = Path(__file__).resolve().parents[4]
        configs_dir = project_root / "configs"

    config_file = configs_dir / f"{environment}.yaml"
    return config_file


@lru_cache(maxsize=1)
def get_settings(environment: Optional[str] = None) -> Settings:
    """Load and return the application settings.

    This function:
    1. Loads environment-specific YAML config (lowest priority - as defaults)
    2. Loads environment variables (medium priority)
    3. Loads .env file (highest priority)

    Priority: ENV vars > .env > YAML > hardcoded defaults

    Args:
        environment: Optional environment override (development, staging, production)

    Returns:
        Settings object with all configuration loaded

    Example:
        >>> from src.core.config import get_settings
        >>> settings = get_settings()
        >>> api_key = settings.tmdb_api_key
    """
    # First, create settings from .env and env vars (this respects priority)
    settings = Settings()

    # Now load YAML config for this environment
    try:
        config_path = get_config_path(settings.environment)
        if config_path.exists():
            yaml_config = load_yaml_config(config_path)

            # For each field in YAML, only set it if it's still at its default value
            # This way .env and env vars take priority
            for field_name, yaml_value in yaml_config.items():
                if hasattr(settings, field_name):
                    # Get the current value
                    current_value = getattr(settings, field_name)
                    # Get the field's default value
                    field_info = settings.model_fields.get(field_name)
                    if field_info:
                        # Check if current value is the default
                        # If it is, use YAML value; if not, .env/env var has set it
                        default_value = field_info.default
                        if current_value == default_value:
                            setattr(settings, field_name, yaml_value)
    except Exception as e:
        # If YAML loading fails, continue with just .env settings
        import warnings

        warnings.warn(f"Could not load YAML config: {e}. Using .env and defaults.", stacklevel=2)

    return settings


# Singleton instance for easy import
settings: Settings = get_settings()


def reload_settings(environment: Optional[str] = None) -> Settings:
    """Reload settings (useful for testing or environment switches).

    Args:
        environment: Optional environment override

    Returns:
        Freshly loaded Settings object
    """
    get_settings.cache_clear()
    return get_settings(environment)
