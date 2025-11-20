"""
Configuration module for Are You Not Entertained project.

This module provides a centralized configuration system using Pydantic 2.x
with support for environment-specific YAML configs and .env files.

Usage:
    >>> from src.core.config import settings
    >>> api_key = settings.tmdb_api_key
    >>> db_url = settings.db_url
    
    # Or reload settings with a different environment
    >>> from src.core.config import get_settings
    >>> prod_settings = get_settings(environment="production")
"""

from .config_loader import get_settings, reload_settings, settings
from .settings import Settings

__all__ = [
    "settings",
    "get_settings", 
    "reload_settings",
    "Settings",
]
