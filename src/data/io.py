"""
io.py
-----
Convenience functions for reading and writing datasets, models,
and general project artifacts. All paths are sourced from py
to ensure consistent project structure.

Logging is used instead of print statements to support both
notebooks and production scripts smoothly.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union

from src.core.logging import get_logger
from src.core.paths import DATA_PROCESSED_DIR

# Initialize logger for this module
logger = get_logger(__name__)


# ------------------------------------------------------------
# DataFrame I/O
# ------------------------------------------------------------

def save_dataframe(
    df: pd.DataFrame,
    filename: str,
    directory: Optional[Union[str, Path]] = None,
    sep: str = ",",
    index: bool = False,
) -> Path:
    """
    Save a Pandas DataFrame to a CSV file with robust logging and
    directory safety checks.

    Parameters
    ----------
    df : pd.DataFrame
        The dataset to save.
    filename : str
        The name of the output CSV file.
    directory : str or Path, optional
        Directory to save into. Defaults to the processed data directory.
    sep : str
        Field separator used in the CSV file.
    index : bool
        Whether to include the index column in the saved file.

    Returns
    -------
    Path
        The full path of the saved file.
    """
    directory = Path(directory) if directory else DATA_PROCESSED_DIR
    output_path = directory / filename

    try:
        directory.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, sep=sep, index=index)
        logger.info(f"Saved DataFrame to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save DataFrame to {output_path}: {e}", exc_info=True)
        raise

    return output_path


def load_dataframe(
    filename: str,
    directory: Optional[Union[str, Path]] = None,
    sep: str = ",",
) -> pd.DataFrame:
    """
    Load a CSV file into a Pandas DataFrame with logging.

    Parameters
    ----------
    filename : str
        The name of the CSV file to load.
    directory : str or Path, optional
        Directory where the file is located. Defaults to processed data.

    sep : str
        Field separator for the CSV file.

    Returns
    -------
    pd.DataFrame
        The loaded dataset.
    """
    directory = Path(directory) if directory else DATA_PROCESSED_DIR
    input_path = directory / filename

    try:
        logger.info(f"Loading DataFrame from {input_path}")
        df = pd.read_csv(input_path, sep=sep)
    except FileNotFoundError:
        logger.error(f"File not found: {input_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load DataFrame from {input_path}: {e}", exc_info=True)
        raise

    return df
