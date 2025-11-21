"""Pydantic-based settings and configuration management for the Are You Not Entertained project.

This module provides a modern, type-safe configuration system using Pydantic 2.x.
It supports:
- Environment-specific YAML configs (development, staging, production)
- .env file for sensitive data (API keys, database URLs)
- Azure deployment compatibility
- FastAPI integration ready
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main settings class for the Are You Not Entertained project.

    Loads configuration from:
    1. Environment variables
    2. .env file (for sensitive data)
    3. Environment-specific YAML config files

    Priority: ENV vars > .env file > YAML config
    """

    # ============================================================
    # Environment & Application Settings
    # ============================================================

    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Current deployment environment"
    )

    app_name: str = Field(default="Are You Not Entertained", description="Application name")

    debug: bool = Field(default=True, description="Enable debug mode")

    log_level: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    use_json_logging: bool = Field(
        default=False, description="Use JSON formatted logs (recommended for production)"
    )

    # ============================================================
    # Path Settings
    # ============================================================

    project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[3],
        description="Project root directory",
    )

    data_dir: Optional[Path] = Field(
        default=None, description="Data directory (defaults to project_root/data)"
    )

    data_raw_dir: Optional[Path] = Field(
        default=None, description="Raw data directory (defaults to data_dir/raw)"
    )

    data_processed_dir: Optional[Path] = Field(
        default=None, description="Processed data directory (defaults to data_dir/processed)"
    )

    data_artifacts_dir: Optional[Path] = Field(
        default=None,
        description="Artifacts directory for model outputs (defaults to data_dir/artifacts)",
    )

    data_db_dir: Optional[Path] = Field(
        default=None, description="Database directory (defaults to data_dir/db)"
    )

    models_dir: Optional[Path] = Field(
        default=None, description="Models directory (defaults to project_root/models)"
    )

    logs_dir: Optional[Path] = Field(
        default=None, description="Logs directory (defaults to project_root/logs)"
    )

    # ============================================================
    # Database Settings
    # ============================================================

    duckdb_path: Optional[Path] = Field(
        default=None,
        description="DuckDB database file path (defaults to data_intermediate_dir/movies.duckdb)",
    )

    db_url: str = Field(
        default="postgresql://localhost:5432/movies",
        description="Database connection URL (legacy PostgreSQL)",
    )

    # ============================================================
    # API Keys (Sensitive - loaded from .env)
    # ============================================================

    tmdb_api_key: Optional[str] = Field(
        default=None, description="The Movie Database (TMDB) API key"
    )

    omdb_api_key: Optional[str] = Field(
        default=None, description="Open Movie Database (OMDB) API key"
    )

    # ============================================================
    # API Configuration
    # ============================================================

    tmdb_api_base_url: str = Field(
        default="https://api.themoviedb.org/3", description="TMDB API base URL"
    )

    omdb_api_base_url: str = Field(
        default="http://www.omdbapi.com", description="OMDB API base URL"
    )

    api_rate_limit: int = Field(default=40, description="API requests per second limit")

    api_timeout: int = Field(default=30, description="API request timeout in seconds")

    # ============================================================
    # Data Processing Settings
    # ============================================================

    batch_size: int = Field(default=100, description="Batch size for data processing")

    random_seed: int = Field(default=42, description="Random seed for reproducibility")

    # ============================================================
    # FastAPI Settings (for future deployment)
    # ============================================================

    host: str = Field(default="0.0.0.0", description="FastAPI host")

    port: int = Field(default=8000, description="FastAPI port")

    reload: bool = Field(default=True, description="Enable auto-reload in development")

    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")

    # ============================================================
    # Azure Deployment Settings
    # ============================================================

    azure_subscription_id: Optional[str] = Field(default=None, description="Azure subscription ID")

    azure_resource_group: Optional[str] = Field(default=None, description="Azure resource group")

    # ============================================================
    # Pydantic Configuration
    # ============================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",  # No prefix for env vars
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from YAML
        validate_default=True,
    )

    # ============================================================
    # Validators
    # ============================================================

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    # ============================================================
    # Helper Methods
    # ============================================================

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == "staging"

    def model_post_init(self, __context) -> None:
        """Set default paths after initialization."""
        # Set default paths based on project_root
        if self.data_dir is None:
            self.data_dir = self.project_root / "data"

        if self.data_raw_dir is None:
            self.data_raw_dir = self.data_dir / "raw"

        if self.data_processed_dir is None:
            self.data_processed_dir = self.data_dir / "processed"

        if self.data_artifacts_dir is None:
            self.data_artifacts_dir = self.data_dir / "artifacts"

        if self.data_db_dir is None:
            self.data_db_dir = self.data_dir / "db"

        if self.models_dir is None:
            self.models_dir = self.project_root / "models"

        if self.logs_dir is None:
            self.logs_dir = self.project_root / "logs"

        if self.duckdb_path is None:
            self.duckdb_path = self.data_db_dir / "movies.duckdb"

        # Ensure critical directories exist
        for directory in [
            self.data_dir,
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_artifacts_dir,
            self.data_db_dir,
            self.models_dir,
            self.logs_dir,
        ]:
            if directory:
                directory.mkdir(parents=True, exist_ok=True)
