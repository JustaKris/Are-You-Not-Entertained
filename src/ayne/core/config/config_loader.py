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
        project_root = Path(__file__).resolve().parents[3]
        configs_dir = project_root / "configs"

    config_file = configs_dir / f"{environment}.yaml"
    return config_file


@lru_cache(maxsize=1)
def get_settings(environment: Optional[str] = None) -> Settings:
    """Load and return the application settings.

    This function:
    1. Loads environment variables and .env file
    2. Loads environment-specific YAML config
    3. Merges them with priority: ENV vars > .env > YAML

    Args:
        environment: Optional environment override (development, staging, production)

    Returns:
        Settings object with all configuration loaded

    Example:
        >>> from src.core.config import get_settings
        >>> settings = get_settings()
        >>> api_key = settings.tmdb_api_key
    """
    # First, create base settings from .env and environment variables
    settings = Settings()

    # Override environment if specified
    if environment:
        settings.environment = environment

    # Try to load environment-specific YAML config
    try:
        config_path = get_config_path(settings.environment)
        if config_path.exists():
            yaml_config = load_yaml_config(config_path)

            # Update settings with YAML config (env vars still have priority)
            # We recreate the settings object with YAML values as defaults
            settings = Settings(**yaml_config)
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
