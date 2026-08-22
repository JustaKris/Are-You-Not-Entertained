# Logging

AYNE centralizes logging in `src/ayne/core/logging.py`. The application writes to
standard output through one root handler and supports readable colored logs for local
work and structured JSON logs for log aggregation.

## Quick Start

Configure logging once at application or script startup, then retrieve module loggers:

```python
from ayne.core.logging import configure_logging, get_logger

configure_logging(level="INFO", use_json=False)
logger = get_logger(__name__)

logger.info("Collection started")
logger.warning("Optional source data was not available")
logger.error("Collection failed", exc_info=True)
```

The CLI configures logging from `LOG_LEVEL` and `USE_JSON_LOGGING` in `.env`. Library
scripts should configure it themselves at their entry point.

`configure_logging` is safe to call repeatedly with the same level and output format.
This is useful because CLI modules obtain their loggers during import. Configure logging
before emitting application messages when writing a new entry point.

## Output Formats

### Colored Console Logs

This is the default for local development:

```python
configure_logging(level="DEBUG", use_json=False)
```

The output includes a timestamp, level, logger name, and message. The handler writes to
stdout; file logging is not enabled by default.

### JSON Logs

Use JSON when a platform or log collector needs structured records:

```python
configure_logging(level="INFO", use_json=True)
```

Records include the timestamp, level, logger name, message, module, process, and thread.
Exceptions are serialized as text. JSON output is suitable for container or hosted
environments, but it does not by itself provide log retention or aggregation.

## Log Levels

| Level | Use for |
| --- | --- |
| `DEBUG` | Diagnostic details such as request flow, client setup, and batch progress |
| `INFO` | Meaningful operational events, counts, and completed stages |
| `WARNING` | Recoverable problems, missing optional data, or degraded behavior |
| `ERROR` | Failed operations that need attention; include exception details when available |
| `CRITICAL` | Severe failures that prevent the application from continuing |

Collection clients keep request setup and per-batch progress at `DEBUG` so they do not
compete with Rich progress displays. User-visible progress for long CLI operations is
rendered by the command itself.

## Context Fields

The JSON formatter supports application-defined fields through the `extra_fields`
attribute on a log record:

```python
logger.info(
    "Processing collection batch",
    extra={
        "extra_fields": {
            "provider": "tmdb",
            "batch_size": 100,
            "request_id": "abc-123",
        }
    },
)
```

Keep context small and operationally useful. Do not include API keys, authorization
headers, credentials, or complete provider responses.

## Exceptions And Messages

Use the logger's arguments for values instead of assembling messages unnecessarily:

```python
try:
    result = load_data(path)
except OSError:
    logger.error("Unable to load data from %s", path, exc_info=True)
    raise
```

Log at the boundary where an error can be handled. Avoid logging the same exception at
every layer, and avoid logging inside tight loops unless the message is sampled or set
to `DEBUG`.

## Noisy Dependencies

The logging configuration reduces noise from `chromadb`, `sentence_transformers`,
`transformers`, and `httpx`. Keep third-party logger changes in the centralized
configuration so modules do not silently alter process-wide logging behavior.

## Environment Settings

These `.env` values control the main logging behavior:

```dotenv
LOG_LEVEL=INFO
USE_JSON_LOGGING=false
```

Use `LOG_LEVEL=DEBUG` while diagnosing a local collection run. Use
`USE_JSON_LOGGING=true` when another system will parse the output.

## Related Documentation

- [Code Quality](code-quality.md) - Python style and automated checks
- [Security](security.md) - Secret handling and security scans
- [CLI Guide](../guides/cli-guide.md) - Collection commands and progress output
