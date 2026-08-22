"""AYNE - Are You Not Entertained?

A modern data science project for movie box office analysis and prediction.

Main modules:
- core: Configuration, logging, and exceptions
- data_collection: API clients for TMDB, OMDB, and The Numbers
- database: DuckDB client for analytics
- utils: Data query and manipulation utilities
- ml: Machine learning models (coming soon)
- api: REST API (coming soon)
- cli: Command-line interface (coming soon)
- web: Web interface (coming soon)
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ayne")
except PackageNotFoundError:
    __version__ = "0.4.0"

# Convenient top-level imports for common use cases
from ayne.core.config import settings
from ayne.core.logging import configure_logging, get_logger

__all__ = [
    "__version__",
    "configure_logging",
    "get_logger",
    "settings",
]
