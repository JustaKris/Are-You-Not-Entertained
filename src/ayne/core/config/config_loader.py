"""YAML/JSON configuration file loaders for the Are You Not Entertained project.

This module handles loading environment-specific configuration from YAML files
and merging them with Pydantic settings.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values

from ayne.core.config.settings import Settings


def load_yaml_config(path: Path) -> dict[str, Any]:
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

    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
        return config or {}


def get_config_path(environment: str, configs_dir: Path | None = None) -> Path:
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
def get_settings(environment: str | None = None) -> Settings:
    """Load and return the application settings.

    This function:
    1. Determines which fields have already been explicitly set via OS environment
       variables or the `.env` file (these must always win).
    2. Loads the environment-specific YAML config.
    3. Passes only the YAML values for fields *not* already set via env/.env as
       constructor kwargs to `Settings`, so pydantic-settings applies them with
       the correct (highest, since they're init kwargs) priority - without ever
       fighting with values `model_post_init` computes for unset path fields.

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
    # Determine which keys are explicitly provided via OS env vars or .env file -
    # those must take priority over YAML no matter what.
    env_file_values = dotenv_values(".env")
    explicit_keys = {k.lower() for k in env_file_values} | {k.lower() for k in os.environ}

    # Determine the target environment without fully constructing Settings yet,
    # so we know which YAML file to load.
    resolved_environment = (
        environment
        or os.environ.get("ENVIRONMENT")
        or env_file_values.get("ENVIRONMENT")
        or Settings.model_fields["environment"].default
    )

    yaml_overrides: dict[str, Any] = {}
    try:
        config_path = get_config_path(resolved_environment)
        if config_path.exists():
            yaml_config = load_yaml_config(config_path)

            # Only pass through YAML values for fields that:
            # - correspond to an actual Settings field, and
            # - were NOT explicitly set via env vars / .env (those win instead)
            for field_name, yaml_value in yaml_config.items():
                if field_name.lower() in explicit_keys:
                    continue
                if field_name in Settings.model_fields:
                    yaml_overrides[field_name] = yaml_value
    except Exception as e:
        # If YAML loading fails, continue with just .env/env var settings
        import warnings

        warnings.warn(f"Could not load YAML config: {e}. Using .env and defaults.", stacklevel=2)

    # Constructor kwargs have the highest precedence in pydantic-settings' source
    # order, so these YAML-derived values will not be overridden by defaults, and
    # `model_post_init` will see the fields already populated and skip recomputing them.
    return Settings(**yaml_overrides)


# Singleton instance for easy import
settings: Settings = get_settings()


def reload_settings(environment: str | None = None) -> Settings:
    """Reload settings (useful for testing or environment switches).

    Args:
        environment: Optional environment override

    Returns:
        Freshly loaded Settings object
    """
    get_settings.cache_clear()
    return get_settings(environment)
