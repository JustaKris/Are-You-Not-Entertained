"""Model serialization utilities using joblib.

This module provides modern utilities for saving and loading ML models
with metadata, versioning, and proper error handling.

Joblib is the recommended approach for scikit-learn models because:
- Efficient serialization of numpy arrays
- Better performance than pickle for large models
- More stable across Python versions
- Industry standard for ML model persistence
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import joblib

from ayne.core.config import settings
from ayne.core.logging import get_logger

logger = get_logger(__name__)


def save_model(
    model: Any,
    filename: str,
    directory: Optional[Union[str, Path]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    compress: Union[int, bool] = 3,
) -> Path:
    """Save a trained ML model to disk using joblib.

    Args:
        model: Trained model object (e.g., sklearn estimator, pipeline)
        filename: Name of the file (with or without .joblib extension)
        directory: Directory to save to (defaults to artifacts/models/)
        metadata: Optional metadata dict to save alongside model
        compress: Compression level (0-9) or True for default (3), False for none

    Returns:
        Path to the saved model file

    Example:
        >>> from sklearn.ensemble import RandomForestRegressor
        >>> model = RandomForestRegressor().fit(X_train, y_train)
        >>> metadata = {
        ...     "model_type": "RandomForestRegressor",
        ...     "features": X_train.columns.tolist(),
        ...     "train_score": 0.95,
        ...     "test_score": 0.87
        ... }
        >>> save_model(model, "rf_model", metadata=metadata)
    """
    # Set default directory if not provided
    if directory is None:
        directory = Path(settings.data_artifacts_dir) / "models"  # type: ignore
    else:
        directory = Path(directory)

    # Create directory if it doesn't exist
    directory.mkdir(parents=True, exist_ok=True)

    # Add extension if not present
    filename_path = Path(filename)
    if not filename_path.suffix:
        filename = f"{filename}.joblib"

    output_path = directory / filename

    try:
        # Save model with compression
        joblib.dump(model, output_path, compress=compress)
        logger.info(f"Saved model to {output_path} (compress={compress})")

        # Save metadata if provided
        if metadata is not None:
            # Add timestamp to metadata
            metadata_with_timestamp = {
                "saved_at": datetime.now().isoformat(),
                "model_class": type(model).__name__,
                **metadata,
            }

            metadata_path = output_path.with_suffix(".json")
            with open(metadata_path, "w") as f:
                json.dump(metadata_with_timestamp, f, indent=2, default=str)
            logger.info(f"Saved model metadata to {metadata_path}")

        return output_path

    except Exception as e:
        logger.error(f"Failed to save model to {output_path}: {e}")
        raise


def load_model(
    filepath: Union[str, Path],
    load_metadata: bool = False,
) -> Union[Any, tuple[Any, Dict[str, Any]]]:
    """Load a trained ML model from disk.

    Args:
        filepath: Path to the model file (.joblib)
        load_metadata: If True, also load metadata file and return as tuple

    Returns:
        Loaded model object, or tuple of (model, metadata) if load_metadata=True

    Example:
        >>> model = load_model("artifacts/models/rf_model.joblib")
        >>> model, metadata = load_model("artifacts/models/rf_model.joblib", load_metadata=True)
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Model file not found: {filepath}")

    try:
        # Load model
        model = joblib.load(filepath)
        logger.info(f"Loaded model from {filepath}")

        # Load metadata if requested
        if load_metadata:
            metadata_path = filepath.with_suffix(".json")
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                logger.info(f"Loaded metadata from {metadata_path}")
                return model, metadata
            else:
                logger.warning(f"Metadata file not found: {metadata_path}")
                return model, {}

        return model

    except Exception as e:
        logger.error(f"Failed to load model from {filepath}: {e}")
        raise


def save_pipeline(
    pipeline: Any,
    name: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """Save a scikit-learn pipeline with metadata.

    This is a convenience wrapper around save_model specifically for pipelines.

    Args:
        pipeline: Trained pipeline object
        name: Name for the pipeline (e.g., "preprocessing_pipeline")
        metadata: Optional metadata dict

    Returns:
        Path to the saved pipeline file

    Example:
        >>> from sklearn.pipeline import Pipeline
        >>> pipe = Pipeline([
        ...     ('scaler', StandardScaler()),
        ...     ('model', RandomForestRegressor())
        ... ])
        >>> pipe.fit(X_train, y_train)
        >>> save_pipeline(pipe, "full_pipeline", metadata={"version": "1.0"})
    """
    return save_model(pipeline, name, metadata=metadata)


def load_pipeline(
    filepath: Union[str, Path], load_metadata: bool = False
) -> Union[Any, tuple[Any, Dict[str, Any]]]:
    """Load a scikit-learn pipeline from disk.

    This is a convenience wrapper around load_model specifically for pipelines.

    Args:
        filepath: Path to the pipeline file
        load_metadata: If True, also load metadata

    Returns:
        Loaded pipeline object, or tuple of (pipeline, metadata)

    Example:
        >>> pipe = load_pipeline("artifacts/models/full_pipeline.joblib")
    """
    return load_model(filepath, load_metadata=load_metadata)


def list_saved_models(directory: Optional[Union[str, Path]] = None) -> list[Path]:
    """List all saved models in a directory.

    Args:
        directory: Directory to search (defaults to artifacts/models/)

    Returns:
        List of paths to .joblib model files

    Example:
        >>> models = list_saved_models()
        >>> for model_path in models:
        ...     print(model_path.name)
    """
    if directory is None:
        directory = Path(settings.data_artifacts_dir) / "models"  # type: ignore
    else:
        directory = Path(directory)

    if not directory.exists():
        logger.warning(f"Models directory not found: {directory}")
        return []

    model_files = list(directory.glob("*.joblib"))
    logger.info(f"Found {len(model_files)} model files in {directory}")
    return sorted(model_files)


def get_model_info(filepath: Union[str, Path]) -> Dict[str, Any]:
    """Get information about a saved model without loading it.

    Args:
        filepath: Path to the model file

    Returns:
        Dictionary with model information (metadata + file stats)

    Example:
        >>> info = get_model_info("artifacts/models/rf_model.joblib")
        >>> print(info["saved_at"])
        >>> print(info["file_size_mb"])
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Model file not found: {filepath}")

    info: Dict[str, Any] = {
        "filepath": str(filepath),
        "filename": filepath.name,
        "file_size_mb": filepath.stat().st_size / (1024 * 1024),
        "modified_at": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
    }

    # Try to load metadata
    metadata_path = filepath.with_suffix(".json")
    if metadata_path.exists():
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        info.update(metadata)

    return info
