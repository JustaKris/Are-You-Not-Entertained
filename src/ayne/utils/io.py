"""Data I/O utility functions for ML workflows.

This module provides modern utilities for reading and writing data files
in various formats (CSV, Parquet, Feather) with proper error handling,
logging, and type safety.

Best practices:
- Type hints for all functions
- Pathlib for cross-platform paths
- Logging for debugging
- Automatic directory creation
- Consistent error handling
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from ayne.core.config import settings
from ayne.core.logging import get_logger

logger = get_logger(__name__)


def save_dataframe(
    df: pd.DataFrame,
    filename: str,
    directory: Optional[Union[str, Path]] = None,
    format: str = "parquet",
    **kwargs: Any,
) -> Path:
    """Save a pandas DataFrame to disk in the specified format.

    Args:
        df: DataFrame to save
        filename: Name of the file (with or without extension)
        directory: Directory to save to (defaults to data/processed/)
        format: File format ('parquet', 'csv', 'feather')
        **kwargs: Additional arguments passed to the save function

    Returns:
        Path to the saved file

    Example:
        >>> df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        >>> save_dataframe(df, "my_data", format="parquet")
        >>> save_dataframe(df, "my_data.csv", format="csv", index=False)
    """
    # Set default directory if not provided
    if directory is None:
        directory = Path(settings.data_processed_dir)  # type: ignore
    else:
        directory = Path(directory)

    # Create directory if it doesn't exist
    directory.mkdir(parents=True, exist_ok=True)

    # Add extension if not present
    filename_path = Path(filename)
    if not filename_path.suffix:
        if format == "parquet":
            filename = f"{filename}.parquet"
        elif format == "csv":
            filename = f"{filename}.csv"
        elif format == "feather":
            filename = f"{filename}.feather"

    output_path = directory / filename

    # Save based on format
    try:
        if format == "parquet":
            df.to_parquet(output_path, **kwargs)
        elif format == "csv":
            # Default to no index for CSV unless specified
            if "index" not in kwargs:
                kwargs["index"] = False
            df.to_csv(output_path, **kwargs)
        elif format == "feather":
            df.to_feather(output_path, **kwargs)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'parquet', 'csv', or 'feather'")

        logger.info(f"Saved {len(df)} rows × {len(df.columns)} columns to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to save DataFrame to {output_path}: {e}")
        raise


def load_dataframe(
    filepath: Union[str, Path],
    format: Optional[str] = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Load a pandas DataFrame from disk.

    Args:
        filepath: Path to the file
        format: File format (auto-detected from extension if not provided)
        **kwargs: Additional arguments passed to the load function

    Returns:
        Loaded DataFrame

    Example:
        >>> df = load_dataframe("data/processed/my_data.parquet")
        >>> df = load_dataframe("data/processed/my_data.csv", format="csv")
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Auto-detect format from extension if not provided
    if format is None:
        format = filepath.suffix.lstrip(".")

    # Load based on format
    try:
        if format == "parquet":
            df = pd.read_parquet(filepath, **kwargs)
        elif format == "csv":
            df = pd.read_csv(filepath, **kwargs)
        elif format == "feather":
            df = pd.read_feather(filepath, **kwargs)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'parquet', 'csv', or 'feather'")

        logger.info(f"Loaded {len(df)} rows × {len(df.columns)} columns from {filepath}")
        return df

    except Exception as e:
        logger.error(f"Failed to load DataFrame from {filepath}: {e}")
        raise


def save_artifacts(
    df: pd.DataFrame,
    filename: str,
    format: str = "parquet",
    **kwargs: Any,
) -> Path:
    """Save model artifacts to the artifacts directory.

    This is a convenience wrapper around save_dataframe that automatically
    saves to the artifacts directory (data/artifacts/).

    Args:
        df: DataFrame to save
        filename: Name of the file (with or without extension)
        format: File format ('parquet', 'csv', 'feather')
        **kwargs: Additional arguments passed to the save function

    Returns:
        Path to the saved file

    Example:
        >>> save_artifacts(X_train, "X_train", format="parquet")
        >>> save_artifacts(y_train, "y_train", format="parquet")
    """
    artifacts_dir = Path(settings.data_artifacts_dir)  # type: ignore
    return save_dataframe(df, filename, directory=artifacts_dir, format=format, **kwargs)


def load_artifacts(
    filename: str,
    format: Optional[str] = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Load model artifacts from the artifacts directory.

    This is a convenience wrapper around load_dataframe that automatically
    loads from the artifacts directory (data/artifacts/).

    Args:
        filename: Name of the file (with or without extension)
        format: File format (auto-detected from extension if not provided)
        **kwargs: Additional arguments passed to the load function

    Returns:
        Loaded DataFrame

    Example:
        >>> X_train = load_artifacts("X_train.parquet")
        >>> y_train = load_artifacts("y_train.parquet")
    """
    artifacts_dir = Path(settings.data_artifacts_dir)  # type: ignore
    filepath = artifacts_dir / filename
    return load_dataframe(filepath, format=format, **kwargs)


def save_processed_data(
    df: pd.DataFrame,
    filename: str,
    format: str = "parquet",
    **kwargs: Any,
) -> Path:
    """Save processed data to the processed data directory.

    This is a convenience wrapper around save_dataframe that automatically
    saves to the processed directory (data/processed/).

    Args:
        df: DataFrame to save
        filename: Name of the file (with or without extension)
        format: File format ('parquet', 'csv', 'feather')
        **kwargs: Additional arguments passed to the save function

    Returns:
        Path to the saved file

    Example:
        >>> save_processed_data(df_clean, "movies_preprocessed", format="parquet")
    """
    processed_dir = Path(settings.data_processed_dir)  # type: ignore
    return save_dataframe(df, filename, directory=processed_dir, format=format, **kwargs)


def load_processed_data(
    filename: str,
    format: Optional[str] = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Load processed data from the processed data directory.

    This is a convenience wrapper around load_dataframe that automatically
    loads from the processed directory (data/processed/).

    Args:
        filename: Name of the file (with or without extension)
        format: File format (auto-detected from extension if not provided)
        **kwargs: Additional arguments passed to the load function

    Returns:
        Loaded DataFrame

    Example:
        >>> df = load_processed_data("movies_preprocessed.parquet")
    """
    processed_dir = Path(settings.data_processed_dir)  # type: ignore
    filepath = processed_dir / filename
    return load_dataframe(filepath, format=format, **kwargs)
