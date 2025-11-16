"""
paths.py
--------
Centralized path management for the project.

This module defines stable, reusable directory paths for datasets,
intermediate artifacts, model outputs, configuration files, and
documentation. Keeping these paths here avoids duplication and keeps
directory layout consistent across the project.
"""

from pathlib import Path

# ------------------------------------------------------------
# Root paths
# ------------------------------------------------------------

# Automatically resolve project root based on this file's location
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_INTERMEDIATE_DIR = DATA_DIR / "intermediate"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

MODELS_DIR = PROJECT_ROOT / "models"
CONFIGS_DIR = PROJECT_ROOT / "configs"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
LOGS_DIR = PROJECT_ROOT / "logs"
SRC_DIR = PROJECT_ROOT / "src"

# ------------------------------------------------------------
# Directory initialization
# ------------------------------------------------------------

def ensure_directories() -> None:
    """
    Ensure that all critical project directories exist.
    Call this once during application start or inside your logger setup.
    """
    dirs = [
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_INTERMEDIATE_DIR,
        DATA_PROCESSED_DIR,
        MODELS_DIR,
        CONFIGS_DIR,
        LOGS_DIR,
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
