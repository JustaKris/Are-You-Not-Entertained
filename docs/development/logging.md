# Logging Configuration

**Centralized logging setup for development and production environments.**

---

## Overview

The Are You Not Entertained (AYNE) project uses a centralized logging configuration (`src/core/logging.py`) that provides:

- **JSON logging** for production/cloud environments (Azure, AWS, Docker)
- **Colorized console logging** for local development
- **Structured log filtering** to suppress noisy third-party libraries
- **Consistent formatting** across all modules

This replaces the previous `logger.py` module with a more robust, production-ready solution.

## Quick Start

### Basic Usage

```python
from src.tv_hml.utils.logging import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Log messages
logger.info("Processing started")
logger.warning("Data quality issue detected")
logger.error("Failed to load file", exc_info=True)
```

### Pipeline Configuration

The CLI automatically configures logging based on verbosity flags:

```python
# In your own scripts using the library
from tv_hml.utils.logging import configure_logging

# Configure logging once at application startup
configure_logging(
    level="INFO",        # DEBUG, INFO, WARNING, ERROR, CRITICAL
    use_json=False,      # True for production, False for development
    include_uvicorn=False  # True if running with uvicorn/FastAPI
)
```

## Configuration Options

### Log Levels

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Detailed diagnostic information (variable values, flow control) |
| `INFO` | General operational messages (process started, completed, counts) |
| `WARNING` | Potentially problematic situations (missing optional files, degraded performance) |
| `ERROR` | Error events that might still allow the application to continue |
| `CRITICAL` | Severe errors causing premature termination |

### Output Formats

#### Development (Colorized)

```python
configure_logging(level="INFO", use_json=False)
```

**Output:**

```text
2025-11-19 14:32:15 | INFO     | tv_hml.transform.fusion | Loading socio file from data/input/2025-09/socio/Sozio_2025_gxl.sav
2025-11-19 14:32:16 | INFO     | tv_hml.transform.fusion | Loaded 20,332 panelists from socio file
2025-11-19 14:32:17 | WARNING  | tv_hml.utils.directory  | Missing input subdirectory: weights
2025-11-19 14:32:18 | ERROR    | tv_hml.io.s3            | Failed to download from S3: BucketNotFound
```

**Features:**

- Color-coded log levels (Green=INFO, Yellow=WARNING, Red=ERROR)
- Human-readable timestamps
- Clear module names
- Easy to scan visually

#### Production (JSON)

```python
configure_logging(level="INFO", use_json=True)
```

**Output:**

```json
{"timestamp": "2025-11-19 14:32:15", "level": "INFO", "logger": "tv_hml.transform.fusion", "message": "Loading socio file", "module": "fusion", "process": 12345, "thread": 67890}
{"timestamp": "2025-11-19 14:32:16", "level": "INFO", "logger": "tv_hml.transform.fusion", "message": "Loaded 20,332 panelists", "module": "fusion", "process": 12345, "thread": 67890}
```

**Features:**

- Structured JSON for log aggregation tools
- Parseable by Azure Monitor, CloudWatch, Datadog, Loki
- Includes metadata (process ID, thread ID, module)
- Easy to query and filter

## Advanced Usage

### Custom Context Fields

Add custom fields to log entries:

```python
import logging

logger = get_logger(__name__)

# Create a log record with extra fields
extra_fields = {
    "request_id": "abc-123",
    "user_id": "user_456",
    "correlation_id": "xyz-789"
}

# Log with context
record = logging.LogRecord(
    name=logger.name,
    level=logging.INFO,
    pathname="",
    lineno=0,
    msg="Processing user request",
    args=(),
    exc_info=None
)
record.extra_fields = extra_fields
logger.handle(record)
```

**JSON Output:**

```json
{
    "timestamp": "2025-11-19 14:32:15",
    "level": "INFO",
    "message": "Processing user request",
    "request_id": "abc-123",
    "user_id": "user_456",
    "correlation_id": "xyz-789"
}
```

### Exception Logging

Always include exception info for error logs:

```python
try:
    process_data(file_path)
except Exception as e:
    logger.error(f"Failed to process {file_path}: {e}", exc_info=True)
    raise
```

**Benefit:** Full stack traces are captured in logs for debugging.

### Suppressing Noisy Libraries

The logging configuration automatically suppresses verbose output from:

- `chromadb` - Telemetry messages
- `sentence_transformers` - Model loading details
- `transformers` - Tokenizer warnings
- `httpx` - HTTP request details

To suppress additional libraries:

```python
import logging

# In your configure_logging() setup
logging.getLogger("some_noisy_library").setLevel(logging.ERROR)
```

## Best Practices

### ✅ Do's

1. **Use appropriate log levels:**

   ```python
   logger.info("Processing 1,234 records")        # Normal operation
   logger.warning("Using default value for X")     # Potential issue
   logger.error("Failed to connect to database")   # Actual error
   ```

2. **Include relevant context:**

   ```python
   logger.info(f"Processed {count:,} records in {duration:.2f}s")
   logger.error(f"File not found: {file_path}")
   ```

3. **Use f-strings for formatting:**

   ```python
   logger.info(f"User {user_id} completed action {action}")
   ```

4. **Log at module boundaries:**

   ```python
   def process_fusion(year, month):
       logger.info(f"Starting fusion for {year}-{month:02d}")
       # ... processing ...
       logger.info(f"Fusion complete: {total_records:,} records")
   ```

### ❌ Don'ts

1. **Don't over-log in tight loops:**

   ```python
   # BAD - logs 10,000 times
   for i in range(10000):
       logger.debug(f"Processing item {i}")
   
   # GOOD - logs once or periodically
   logger.info(f"Processing {len(items):,} items")
   for i, item in enumerate(items):
       if i % 1000 == 0:
           logger.debug(f"Progress: {i:,}/{len(items):,}")
   ```

2. **Don't log sensitive data:**

   ```python
   # BAD
   logger.info(f"Password: {password}")
   
   # GOOD
   logger.info("Authentication successful")
   ```

3. **Don't use print() statements:**

   ```python
   # BAD
   print("Processing started")
   
   # GOOD
   logger.info("Processing started")
   ```

4. **Don't log before configuring:**

   ```python
   # BAD - logger not configured yet
   logger = get_logger(__name__)
   logger.info("Starting...")
   configure_logging()
   
   # GOOD - configure first
   configure_logging()
   logger = get_logger(__name__)
   logger.info("Starting...")
   ```

## Migration from Old Logger

### Changes Required

**Old Code (`logger.py`):**

```python
from src.tv_hml.utils.logger import setup_logger, get_logger

# Setup with file handler
logger = setup_logger(
    name="tv_hml.module",
    level=logging.INFO,
    log_file="logs/module.log",
    console=True
)
```

**New Code (`logging.py`):**

```python
from src.tv_hml.utils.logging import configure_logging, get_logger

# Configure once at app startup
configure_logging(level="INFO", use_json=False)

# Get logger in each module
logger = get_logger(__name__)
```

### Key Differences

| Feature | Old (`logger.py`) | New (`logging.py`) |
|---------|-------------------|-------------------|
| Configuration | Per-module setup | Global configuration |
| Format | Console only | JSON or colorized |
| Filtering | Manual | Automatic for known libraries |
| Production Ready | No | Yes (JSON logging) |
| File Logging | Per-module files | Centralized (via handlers) |

## Deployment Considerations

### Local Development

```python
# Use colorized logging
configure_logging(level="DEBUG", use_json=False)
```

### Docker/Kubernetes

```python
# Use JSON logging for container logs
import os
use_json = os.getenv("LOG_FORMAT", "json") == "json"
configure_logging(level="INFO", use_json=use_json)
```

### Azure/AWS

```python
# Enable JSON logging for cloud log aggregation
configure_logging(level="INFO", use_json=True)
```

### CI/CD Pipeline

```python
# Use plain text for readable build logs
configure_logging(level="INFO", use_json=False)
```

## Troubleshooting

### Logs Not Appearing

**Problem:** No log output is shown.

**Solution:**

```python
# Ensure configure_logging() is called before any get_logger()
configure_logging(level="INFO", use_json=False)
logger = get_logger(__name__)
logger.info("Test message")  # Should now appear
```

### Too Much Log Output

**Problem:** Logs are overwhelming with debug messages.

**Solution:**

```python
# Use INFO level instead of DEBUG
configure_logging(level="INFO", use_json=False)
```

### JSON Logs Not Parsing

**Problem:** JSON logs are malformed in log aggregation tool.

**Solution:**

```python
# Ensure use_json=True is set
configure_logging(level="INFO", use_json=True, include_uvicorn=False)
```

### Duplicate Log Messages

**Problem:** Same log message appears multiple times.

**Solution:**

```python
# Don't call configure_logging() multiple times
# Call it once in main() or __main__ block

if __name__ == "__main__":
    configure_logging(level="INFO", use_json=False)
    main()  # All modules will use this configuration
```

## Related Documentation

- [Development Setup](setup.md) - Initial project setup
- [Contributing](contributing.md) - Code contribution guidelines
- [Debugging](../troubleshooting/debugging.md) - Debugging techniques

---

**Last Updated:** November 19, 2025  
**Logging Module:** `src/tv_hml/utils/logging.py`
