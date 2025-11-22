"""Query utilities for data analysis and notebooks.

This module provides convenient functions for querying the DuckDB database
and loading data into pandas DataFrames for analysis in Jupyter notebooks.

Modern best practices:
- Type hints for clarity
- Context managers for resource management
- Logging for debugging
- Clean separation of concerns
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ayne.core.config import settings
from ayne.core.logging import get_logger
from ayne.database.duckdb_client import DuckDBClient

logger = get_logger(__name__)


def get_db_client(read_only: bool = True) -> DuckDBClient:
    """Get a DuckDB client instance.

    Args:
        read_only: Whether to open database in read-only mode (default True for analysis)

    Returns:
        DuckDBClient instance

    Example:
        >>> db = get_db_client()
        >>> df = db.query("SELECT * FROM movies LIMIT 10")
        >>> db.close()
    """
    return DuckDBClient(read_only=read_only)


def query_movies(
    filters: Optional[Dict[str, Any]] = None,
    columns: Optional[List[str]] = None,
    limit: Optional[int] = None,
    order_by: Optional[str] = None,
) -> pd.DataFrame:
    """Query movies table with convenient filtering.

    Args:
        filters: Dictionary of column:value pairs for filtering
        columns: List of columns to select (None = all columns)
        limit: Maximum number of rows to return
        order_by: Column name to order by (e.g., "release_date DESC")

    Returns:
        DataFrame with query results

    Example:
        >>> # Get recent movies with budget info
        >>> df = query_movies(
        ...     filters={"release_year": 2024},
        ...     columns=["title", "budget", "revenue"],
        ...     order_by="revenue DESC",
        ...     limit=100
        ... )
    """
    # Build SELECT clause
    select_cols = ", ".join(columns) if columns else "*"

    # Build WHERE clause
    where_clause = ""
    if filters:
        conditions = [f"{col} = {repr(val)}" for col, val in filters.items()]
        where_clause = "WHERE " + " AND ".join(conditions)

    # Build ORDER BY clause
    order_clause = f"ORDER BY {order_by}" if order_by else ""

    # Build LIMIT clause
    limit_clause = f"LIMIT {limit}" if limit else ""

    # Construct full query
    query = f"""
        SELECT {select_cols}
        FROM movies
        {where_clause}
        {order_clause}
        {limit_clause}
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Queried movies table: {len(df)} rows returned")
        return df
    finally:
        db.close()


def load_full_dataset(include_nulls: bool = True) -> pd.DataFrame:
    """Load the complete movies dataset for analysis.

    This joins all relevant tables (movies, tmdb_movies, omdb_movies, numbers_movies)
    to provide a comprehensive view of all available data.

    Args:
        include_nulls: Whether to include movies with missing data

    Returns:
        DataFrame with complete movie data

    Example:
        >>> df = load_full_dataset()
        >>> print(f"Loaded {len(df)} movies")
        >>> df.info()
    """
    query = """
        SELECT
            m.*,
            t.title as tmdb_title,
            t.overview,
            t.popularity,
            t.vote_average as tmdb_vote_average,
            t.vote_count as tmdb_vote_count,
            t.budget as tmdb_budget,
            t.revenue as tmdb_revenue,
            t.runtime as tmdb_runtime,
            t.status,
            t.genres as genre_names,
            t.production_companies as production_company_name,
            t.production_countries as production_country_name,
            t.spoken_languages,
            o.rated,
            o.released,
            o.runtime as omdb_runtime,
            o.genre as omdb_genre,
            o.director,
            o.writer,
            o.actors,
            o.language,
            o.country,
            o.awards,
            o.metascore,
            o.imdb_rating,
            o.imdb_votes,
            o.box_office,
            o.rotten_tomatoes_rating,
            o.meta_critic_rating,
            n.production_budget,
            n.domestic_box_office as domestic_gross,
            n.worldwide_box_office as worldwide_gross
        FROM movies m
        LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
        LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
        LEFT JOIN numbers_movies n ON m.movie_id = n.movie_id
    """

    if not include_nulls:
        query += """
        WHERE m.budget IS NOT NULL
          AND m.revenue IS NOT NULL
        """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Loaded full dataset: {len(df)} movies with {len(df.columns)} columns")
        return df
    finally:
        db.close()


def get_movies_with_financials(min_budget: float = 0, min_revenue: float = 0) -> pd.DataFrame:
    """Get movies with financial data for budget/revenue analysis.

    Args:
        min_budget: Minimum budget threshold
        min_revenue: Minimum revenue threshold

    Returns:
        DataFrame with movies having financial data

    Example:
        >>> # Get movies with substantial budgets
        >>> df = get_movies_with_financials(min_budget=10_000_000)
        >>> print(f"Found {len(df)} movies with budget >= $10M")
    """
    query = f"""
        SELECT
            m.*,
            t.title as tmdb_title,
            t.popularity,
            t.vote_average,
            t.vote_count,
            t.runtime,
            t.genres as genre_names,
            t.budget,
            t.revenue,
            o.director,
            o.writer,
            o.actors,
            o.imdb_rating,
            o.imdb_votes,
            o.metascore,
            o.rotten_tomatoes_rating
        FROM movies m
        INNER JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
        LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
        WHERE t.budget >= {min_budget}
          AND t.revenue >= {min_revenue}
          AND t.budget IS NOT NULL
          AND t.revenue IS NOT NULL
        ORDER BY m.release_date DESC
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(
            f"Loaded {len(df)} movies with financials (budget >= {min_budget}, revenue >= {min_revenue})"
        )
        return df
    finally:
        db.close()


def get_movies_by_year_range(start_year: int, end_year: Optional[int] = None) -> pd.DataFrame:
    """Get movies released in a specific year range.

    Args:
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive), defaults to start_year

    Returns:
        DataFrame with movies in the year range

    Example:
        >>> # Get all movies from 2020-2024
        >>> df = get_movies_by_year_range(2020, 2024)
    """
    end_year = end_year or start_year

    query = f"""
        SELECT *
        FROM movies
        WHERE EXTRACT(YEAR FROM release_date) BETWEEN {start_year} AND {end_year}
        ORDER BY release_date DESC
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Loaded {len(df)} movies from {start_year}-{end_year}")
        return df
    finally:
        db.close()


def get_table_info(table_name: str) -> pd.DataFrame:
    """Get schema information for a table.

    Args:
        table_name: Name of the table

    Returns:
        DataFrame with column information

    Example:
        >>> info = get_table_info("movies")
        >>> print(info[["column_name", "column_type", "null"]])
    """
    query = f"DESCRIBE {table_name}"

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Retrieved schema info for table '{table_name}'")
        return df
    finally:
        db.close()


def execute_custom_query(query: str) -> pd.DataFrame:
    """Execute a custom SQL query.

    Args:
        query: SQL query string

    Returns:
        DataFrame with query results

    Example:
        >>> query = '''
        ...     SELECT genre_names, COUNT(*) as count
        ...     FROM movies
        ...     GROUP BY genre_names
        ...     ORDER BY count DESC
        ...     LIMIT 10
        ... '''
        >>> df = execute_custom_query(query)
    """
    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Custom query executed: {len(df)} rows returned")
        return df
    finally:
        db.close()


# def save_processed_data(df: pd.DataFrame, filename: str, format: str = "parquet") -> Path:
#     """Save processed DataFrame to the processed data directory.

#     Args:
#         df: DataFrame to save
#         filename: Name of the file (without extension)
#         format: Format to save ('parquet', 'csv', 'feather')

#     Returns:
#         Path to the saved file

#     Example:
#         >>> df_clean = load_full_dataset()
#         >>> # ... preprocessing ...
#         >>> save_processed_data(df_clean, "movies_preprocessed", format="parquet")
#     """
#     output_dir = Path(getattr(settings, "data_processed_dir", Path.cwd() / "data" / "processed"))
#     output_dir.mkdir(parents=True, exist_ok=True)  # type: ignore

#     if format == "parquet":
#         output_path = output_dir / f"{filename}.parquet"  # type: ignore
#         df.to_parquet(output_path, index=False)
#     elif format == "csv":
#         output_path = output_dir / f"{filename}.csv"  # type: ignore
#         df.to_csv(output_path, index=False)
#     elif format == "feather":
#         output_path = output_dir / f"{filename}.feather"  # type: ignore
#         df.to_feather(output_path)
#     else:
#         raise ValueError(f"Unsupported format: {format}")

#     logger.info(f"Saved {len(df)} rows to {output_path}")
#     return output_path


# def save_artifacts(df: pd.DataFrame, filename: str, format: str = "parquet") -> Path:
#     """Save model artifacts (features, predictions) to the artifacts directory.

#     .. deprecated::
#         Use ayne.utils.io.save_artifacts() instead.
#         This function is kept for backward compatibility.

#     Args:
#         df: DataFrame to save
#         filename: Name of the file (without extension)
#         format: Format to save ('parquet', 'csv', 'feather')

#     Returns:
#         Path to the saved file

#     Example:
#         >>> # Save training features
#         >>> save_artifacts(X_train, "X_train", format="parquet")
#         >>> save_artifacts(y_train, "y_train", format="parquet")
#     """
#     output_dir = Path(getattr(settings, "data_artifacts_dir", Path.cwd() / "data" / "artifacts"))
#     output_dir.mkdir(parents=True, exist_ok=True)  # type: ignore

#     if format == "parquet":
#         output_path = output_dir / f"{filename}.parquet"  # type: ignore
#         df.to_parquet(output_path, index=False)
#     elif format == "csv":
#         output_path = output_dir / f"{filename}.csv"  # type: ignore
#         df.to_csv(output_path, index=False)
#     elif format == "feather":
#         output_path = output_dir / f"{filename}.feather"  # type: ignore
#         df.to_feather(output_path)
#     else:
#         raise ValueError(f"Unsupported format: {format}")

#     logger.info(f"Saved artifacts: {len(df)} rows to {output_path}")
#     return output_path


# NOTE: For new code, prefer using the utilities in ayne.utils.io module:
# - save_dataframe() / load_dataframe() for general I/O
# - save_processed_data() / load_processed_data() for processed data
# - save_artifacts() / load_artifacts() for model artifacts
#
# The above functions in this module are kept for backward compatibility
# with existing notebooks but will delegate to ayne.utils.io in future versions.
