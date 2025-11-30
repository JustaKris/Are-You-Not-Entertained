"""Custom exception classes for the Are You Not Entertained project."""


class AyneError(Exception):
    """Base exception for all custom errors in the project."""

    pass


class ConfigError(AyneError):
    """Raised when configuration loading or validation fails."""

    pass


class DataError(AyneError):
    """Raised for data validation or loading errors."""

    pass


class DatabaseError(AyneError):
    """Base exception for database-related errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class DatabaseLockedError(DatabaseError):
    """Raised when database file is locked by another process.

    This typically occurs when:
    - Another instance of the application is accessing the database
    - A Jupyter notebook or script hasn't closed the connection
    - The database wasn't properly closed in a previous session

    Attributes:
        db_path: Path to the locked database file
        process_info: Information about the process holding the lock (if available)
    """

    def __init__(self, db_path: str, process_info: str | None = None):
        """Initialize DatabaseLockedError.

        Args:
            db_path: Path to the locked database file
            process_info: Optional information about the process holding the lock
        """
        self.db_path = db_path
        self.process_info = process_info

        message = f"Database file is locked: {db_path}"
        if process_info:
            message += f"\n\nFile is currently open by: {process_info}"

        message += (
            "\n\nPossible solutions:\n"
            "  1. Close any Jupyter notebooks or scripts using the database\n"
            "  2. Ensure previous CLI commands have completed\n"
            "  3. Restart your Python kernel if using Jupyter\n"
            "  4. Check for zombie processes and terminate them"
        )

        super().__init__(message)


class ModelError(AyneError):
    """Raised for model training or inference errors."""

    pass


class APIError(AyneError):
    """Raised for external API-related errors."""

    pass


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    pass


class APIRateLimitExceeded(APIError):
    """Raised when API daily/monthly quota is exceeded.

    This is different from rate limiting (429) - it indicates the API quota
    for the billing period has been exhausted (typically 401 Unauthorized).

    Attributes:
        api_name: Name of the API (e.g., 'OMDB', 'TMDB')
        items_processed: Number of items successfully processed before limit
        total_requested: Total number of items requested
        partial_data: List of successfully fetched items before quota hit
    """

    def __init__(
        self,
        api_name: str,
        items_processed: int,
        total_requested: int,
        partial_data: list | None = None,
    ):
        """Initialize APIRateLimitExceeded.

        Args:
            api_name: Name of the API that hit the limit
            items_processed: Number of items successfully processed
            total_requested: Total number of items that were requested
            partial_data: Optional list of successfully fetched items
        """
        self.api_name = api_name
        self.items_processed = items_processed
        self.total_requested = total_requested
        self.partial_data = partial_data or []

        message = (
            f"{api_name} daily quota exceeded.\n\n"
            f"Progress: {items_processed}/{total_requested} items processed successfully\n\n"
            f"The {api_name} free tier has a daily request limit that has been reached.\n"
            f"Your data up to this point has been saved.\n\n"
            f"Options:\n"
            f"  1. Wait 24 hours for the quota to reset\n"
            f"  2. Upgrade to a paid {api_name} plan for higher limits\n"
            f"  3. Resume collection tomorrow with the same command"
        )

        super().__init__(message)


class APIAuthenticationError(APIError):
    """Raised when API authentication fails."""

    pass
