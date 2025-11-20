"""
duckdb_client.py
----------------
A small DuckDB wrapper providing:
- connection management
- executing queries and statements
- importing/appending Parquet into tables
- create_tables(schema_path) which runs schema.sql
- upsert_dataframe(table_name, df, key_columns) which safely
  upserts rows using a temp table pattern.

Place this file in: src/data/duckdb_client.py
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Sequence, List, Dict, Any

import duckdb
import pandas as pd

from src.core.logging import get_logger
from src.core.config import settings

logger = get_logger(__name__)


class DuckDBClient:
    """
    Minimal DuckDB client wrapper.

    Examples:
        db = DuckDBClient()  # uses DB_FILE from paths
        df = db.query("SELECT * FROM movies LIMIT 10")
        db.import_parquet("tmdb_movies", "data/input/tmdb_movies.parquet")
        db.upsert_dataframe("movies", df_new, key_columns=["tmdb_id", "imdb_id"])
        db.close()
    """

    def __init__(self, db_path: Optional[str | Path] = None, read_only: bool = False):
        self.db_path = Path(db_path) if db_path else settings.duckdb_path  # type: ignore
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.read_only = read_only

        # DuckDB connection. Use read_only flag if needed in the future.
        self._conn = duckdb.connect(database=str(self.db_path), read_only=self.read_only)
        logger.info("DuckDB connected at %s (read_only=%s)", self.db_path, self.read_only)

    # ----------------------
    # Basic exec/query
    # ----------------------
    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> Any:
        """
        Execute a SQL statement. For DDL/DML you can call this.
        Returns the DuckDB relation (caller can call .df()).
        """
        logger.debug("Executing SQL: %s", sql if len(sql) < 500 else sql[:500] + "...")
        if params:
            return self._conn.execute(sql, params)
        return self._conn.execute(sql)

    def query(self, sql: str, params: Optional[Sequence[Any]] = None) -> pd.DataFrame:
        """
        Execute a SELECT query and return a pandas DataFrame.
        """
        rel = self.execute(sql, params)
        df = rel.df()
        logger.debug("Query returned %d rows", len(df))
        return df

    # ----------------------
    # Schema management
    # ----------------------
    def create_tables_from_sql(self, schema_path: Optional[Path | str] = None) -> None:
        """
        Execute a schema SQL file (schema.sql) to create all tables.
        """
        schema_path = Path(schema_path) if schema_path else (Path(__file__).parent / "schema.sql")
        if not schema_path.exists():
            logger.error("Schema file not found: %s", schema_path)
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        sql_text = schema_path.read_text()
        # DuckDB allows multiple statements separated by ';'
        logger.info("Creating tables from schema: %s", schema_path)
        self.execute(sql_text)
        logger.info("Schema applied successfully.")

    # ----------------------
    # Parquet helpers
    # ----------------------
    def import_parquet(self, table_name: str, parquet_path: str | Path) -> None:
        """
        Create or replace a DuckDB table from a Parquet file (full import).
        """
        parquet_path = Path(parquet_path)
        if not parquet_path.exists():
            raise FileNotFoundError(parquet_path)

        sql = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM '{parquet_path}'"
        logger.info("Importing parquet %s into table %s", parquet_path, table_name)
        self.execute(sql)

    def append_parquet(self, table_name: str, parquet_path: str | Path) -> None:
        """
        Append rows from parquet to an existing table. If table doesn't exist, it will create it.
        """
        parquet_path = Path(parquet_path)
        if not parquet_path.exists():
            raise FileNotFoundError(parquet_path)

        if not self.table_exists(table_name):
            logger.info("Table %s does not exist; using import_parquet", table_name)
            self.import_parquet(table_name, parquet_path)
            return

        sql = f"INSERT INTO {table_name} SELECT * FROM '{parquet_path}'"
        logger.info("Appending parquet %s -> %s", parquet_path, table_name)
        self.execute(sql)

    def table_exists(self, table_name: str) -> bool:
        """
        Check whether a table exists in the DB (DuckDB system table).
        """
        try:
            df = self.query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' AND table_name = ?",
                [table_name],
            )
            exists = not df.empty
            logger.debug("table_exists(%s) -> %s", table_name, exists)
            return exists
        except Exception:
            return False

    # ----------------------
    # Upsert helpers (safe pattern)
    # ----------------------
    def upsert_dataframe(self, table_name: str, df: pd.DataFrame, key_columns: Sequence[str]) -> None:
        """
        Upsert a pandas DataFrame into an existing DuckDB table using a temp view pattern.

        Pattern:
          1) Register the incoming df as a temp view named '__staging'
          2) Delete from target where key in staging
          3) Insert all rows from staging into target
          4) Unregister the view

        Parameters:
            table_name: target table
            df: pandas DataFrame
            key_columns: list of columns that uniquely identify a row (e.g. ['tmdb_id'] or ['imdb_id'])
        """
        if df.empty:
            logger.info("upsert_dataframe: nothing to upsert (empty DataFrame)")
            return

        # Normalise key column list
        if isinstance(key_columns, str):
            key_columns = [key_columns]

        # Use a deterministic staging name
        staging_view = "__staging_upsert"

        # Register DataFrame as a DuckDB view
        logger.debug("Registering staging DataFrame as view %s for upsert into %s", staging_view, table_name)
        self._conn.register(staging_view, df)

        # Build WHERE clause: (col1 = staging.col1 OR col1 IN (SELECT col1 FROM staging))
        # We'll delete rows matching any of the key combinations present in staging.
        # Use EXISTS with correlated subquery for safety.
        key_pred = " AND ".join([f"main.{col} = staging.{col}" for col in key_columns])

        delete_sql = f"""
        DELETE FROM {table_name} AS main
        WHERE EXISTS (
            SELECT 1 FROM {staging_view} AS staging WHERE {key_pred}
        )
        """
        
        # Build column list for INSERT - only insert columns present in DataFrame
        columns = list(df.columns)
        columns_str = ", ".join(columns)
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) SELECT {columns_str} FROM {staging_view}"
        logger.info("Upserting into %s (delete existing keys -> insert new rows)", table_name)

        # Execute delete then insert
        self.execute(delete_sql)
        self.execute(insert_sql)

        # Unregister staging view
        try:
            self._conn.unregister(staging_view)
        except Exception:
            # older DuckDB versions may not require/allow unregister; ignore safely
            pass

        logger.info("Upsert complete: %s rows upserted into %s", len(df), table_name)

    def upsert_records(self, table_name: str, records: Sequence[Dict[str, Any]], key_columns: Sequence[str]):
        """
        Convenience wrapper: turn records (list of dict) into DataFrame and upsert.
        """
        if not records:
            logger.info("upsert_records: no records provided")
            return
        df = pd.DataFrame.from_records(records)
        self.upsert_dataframe(table_name, df, key_columns=key_columns)

    # ----------------------
    # Refresh state helpers
    # ----------------------
    def get_movies_due_for_refresh(self, limit: Optional[int] = 1000) -> pd.DataFrame:
        """
        Return movies that are due for refresh based on movie_refresh_state.next_refresh_due,
        OR movies not present in refresh_state table (first time).
        """
        limit_clause = f"LIMIT {limit}" if limit is not None else ""
        sql = f"""
        SELECT m.movie_id, m.tmdb_id, m.imdb_id, m.title,
               r.next_refresh_due, r.frozen
        FROM movies m
        LEFT JOIN movie_refresh_state r USING(movie_id)
        WHERE (r.frozen IS NULL OR r.frozen = FALSE)
          AND (r.next_refresh_due IS NULL OR r.next_refresh_due <= current_timestamp)
        {limit_clause}
        """
        return self.query(sql)

    def set_next_refresh(self, movie_id: int, next_refresh_ts: Optional[str]):
        """
        Insert/update the next_refresh_due for a movie in movie_refresh_state.
        If the row does not exist, create it.
        """
        if not self.table_exists("movie_refresh_state"):
            # create minimal row
            self.execute(
                "INSERT INTO movie_refresh_state (movie_id, next_refresh_due, last_checked) VALUES (?, ?, current_timestamp)",
                [movie_id, next_refresh_ts],
            )
            return

        # Delete existing row and insert new - simple approach that works across versions
        self.execute("DELETE FROM movie_refresh_state WHERE movie_id = ?", [movie_id])
        self.execute(
            "INSERT INTO movie_refresh_state (movie_id, next_refresh_due, last_checked) VALUES (?, ?, current_timestamp)",
            [movie_id, next_refresh_ts],
        )

    # ----------------------
    # Utilities
    # ----------------------
    def export_table_to_parquet(self, table_name: str, parquet_path: str | Path) -> None:
        parquet_path = Path(parquet_path)
        parquet_path.parent.mkdir(parents=True, exist_ok=True)

        sql = f"COPY (SELECT * FROM {table_name}) TO '{parquet_path}' (FORMAT PARQUET)"
        logger.info("Exporting table %s to parquet %s", table_name, parquet_path)
        self.execute(sql)

    def close(self):
        """Close the DuckDB connection."""
        try:
            self._conn.close()
            logger.info("DuckDB connection closed.")
        except Exception:
            pass
