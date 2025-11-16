"""
model_io.py
-----------
Utilities for saving and loading ML models.
Supports both classical pickle-based models and future
integration with MLflow or ONNX.
"""

import joblib
from pathlib import Path
from src.core.logging import get_logger
from src.core.paths import MODELS_DIR
# from src.core import paths

logger = get_logger(__name__)


def save_model(model, filename: str, directory: Path | None = None) -> Path:
    """Save a trained model using joblib."""
    directory = directory or MODELS_DIR
    directory.mkdir(parents=True, exist_ok=True)

    filepath = directory / filename

    try:
        joblib.dump(model, filepath)
        logger.info(f"Saved model to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save model: {e}", exc_info=True)
        raise

    return filepath


def load_model(filename: str, directory: Path | None = None):
    """Load a model saved with joblib."""
    directory = directory or MODELS_DIR
    filepath = directory / filename

    try:
        logger.info(f"Loading model from {filepath}")
        model = joblib.load(filepath)
    except Exception as e:
        logger.error(f"Failed to load model: {e}", exc_info=True)
        raise

    return model
