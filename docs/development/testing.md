# Testing Guide

Modern testing practices for TV-HML using pytest with comprehensive coverage reporting.

## Quick Start

```powershell
# Run all tests with coverage
uv run pytest --cov=src --cov-report=html

# Run with verbose output
uv run pytest -v

# Run specific test
uv run pytest tests/unit/test_config.py::TestAnalysisConfig::test_valid_config
```

## Test Organization

```text
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Fast, isolated unit tests
│   ├── test_calendar.py
│   ├── test_config.py
│   ├── test_directory.py
│   └── test_exceptions.py
└── integration/             # End-to-end integration tests
    └── test_config_integration.py
```

## Running Tests

### By Test Type

```powershell
# Unit tests only (fast)
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# Specific test file
uv run pytest tests/unit/test_calendar.py -v

# Specific test class
uv run pytest tests/unit/test_config.py::TestAnalysisConfig -v

# Single test method
uv run pytest tests/unit/test_calendar.py::TestCalendarFunctions::test_leap_year -v
```

### With Markers

```powershell
# Run only slow tests
uv run pytest -m slow

# Skip slow tests
uv run pytest -m "not slow"

# Run tests for specific component
uv run pytest -m config
```

### Coverage Reports

```powershell
# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html

# Terminal output with missing lines
uv run pytest --cov=src --cov-report=term-missing

# Generate XML for CI/CD
uv run pytest --cov=src --cov-report=xml

# View HTML report (Windows)
start reports/coverage/html/index.html
```

**Coverage Targets:**

- **Overall**: 80% minimum for production
- **Critical modules**: 90%+ (config, io, models)
- **Current baseline**: 10%

## Test Fixtures

Common fixtures available in `conftest.py`:

```python
# Directory fixtures
temp_data_dir           # Temporary directory for test data
test_settings           # Complete Settings object with test defaults

# Configuration fixtures
test_analysis_config    # AnalysisConfig with test values
sample_year             # Year: 2025
sample_month            # Month: 9

# Mock fixtures
mock_s3_client          # Mocked boto3 S3 client
mock_athena_client      # Mocked boto3 Athena client
```

### Using Fixtures

```python
def test_example(temp_data_dir, test_settings):
    """Test using fixtures."""
    # temp_data_dir is a Path object to temporary directory
    assert temp_data_dir.exists()
    
    # test_settings has pre-configured paths
    assert test_settings.paths.data_root == temp_data_dir
    assert test_settings.analysis.year == 2025
    assert test_settings.analysis.month == 9
```

## Writing Tests

### Best Practices

1. **One test, one behavior** - Each test verifies a single thing
2. **Use descriptive names** - `test_get_days_in_month_february_leap_year`
3. **Arrange-Act-Assert** - Clear test structure
4. **Leverage fixtures** - DRY principle for setup/teardown
5. **Test edge cases** - Boundary conditions, errors, empty inputs
6. **Mock external dependencies** - S3, Athena, network calls

### Unit Test Example

```python
import pytest
from tv_hml.utils.calendar import get_days_in_month

class TestCalendarFunctions:
    """Test calendar utility functions."""

    def test_get_days_in_month_february_leap_year(self):
        """February in leap year has 29 days."""
        assert get_days_in_month(2024, 2) == 29

    def test_get_days_in_month_february_non_leap_year(self):
        """February in non-leap year has 28 days."""
        assert get_days_in_month(2025, 2) == 28
    
    def test_get_days_in_month_invalid_month(self):
        """Invalid month raises ValueError."""
        with pytest.raises(ValueError, match="Month must be between 1 and 12"):
            get_days_in_month(2025, 13)
```

### Integration Test Example

```python
from tv_hml.config.schema import Settings
from tv_hml.utils.directory import DirectoryManager

class TestConfigurationIntegration:
    """Test integration between config and directory management."""

    def test_settings_with_directory_manager(self, test_settings, temp_data_dir):
        """Settings and DirectoryManager work together correctly."""
        dm = DirectoryManager(test_settings.paths.data_root)
        structure = dm.create_full_structure(
            test_settings.analysis.year,
            test_settings.analysis.month
        )
        
        # Verify directory structure created
        assert structure["input"]["weights"].exists()
        assert structure["output"]["durations"].exists()
        assert structure["output"]["fusion"].exists()
```

### Parametrized Tests

Test multiple inputs efficiently:

```python
import pytest

@pytest.mark.parametrize("year,month,expected", [
    (2024, 1, 31),   # January
    (2024, 2, 29),   # Leap year February
    (2025, 2, 28),   # Non-leap year February
    (2024, 4, 30),   # April
    (2024, 12, 31),  # December
])
def test_days_in_month(year, month, expected):
    """Test days in month for various cases."""
    assert get_days_in_month(year, month) == expected
```

### Mocking External Services

```python
from unittest.mock import Mock, patch
import pytest

class TestS3Download:
    """Test S3 download functionality."""
    
    @patch('boto3.client')
    def test_download_weights(self, mock_boto_client, temp_data_dir):
        """Test successful S3 download."""
        # Arrange
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        # Act
        downloader = S3Downloader(bucket="test-bucket")
        result = downloader.download_file("key", temp_data_dir / "file.txt")
        
        # Assert
        mock_s3.download_file.assert_called_once()
        assert result.exists()
```

## Coverage Status

### Current Coverage by Module

| Module | Coverage | Status | Priority |
|--------|----------|--------|----------|
| `utils.calendar` | 100% | ✅ Complete | - |
| `utils.exceptions` | 100% | ✅ Complete | - |
| `utils.types` | 100% | ✅ Complete | - |
| `config.schema` | 81% | 🟡 Good | Increase to 90% |
| `utils.directory` | 66% | 🟡 Good | Increase to 80% |
| `config.loader` | 58% | 🟡 Partial | Increase to 80% |
| `io.s3` | 0% | ❌ None | High priority |
| `io.athena` | 0% | ❌ None | High priority |
| `models.fusion` | 0% | ❌ None | Medium priority |

### Testing Priorities

**Phase 1 - Core Foundation (Current):**

1. Configuration loading/validation
2. Directory management
3. Calendar utilities

**Phase 2 - I/O Operations:**

1. S3 download/upload (with mocks)
2. Athena query execution (with mocks)
3. File readers/writers

**Phase 3 - Data Processing:**

1. Weight processing
2. Hours aggregation
3. Duration calculation

**Phase 4 - ML & Fusion:**

1. LightGBM training
2. Imputation logic
3. Validation metrics

## CI/CD Integration

Tests run automatically in GitLab CI pipeline:

```yaml
test:
  stage: test
  script:
    - uv sync
    - uv run pytest --cov=src --cov-report=xml --cov-report=term
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: reports/coverage/coverage.xml
```

See [CI/CD Documentation](ci-cd.md) for complete pipeline details.

## Test Configuration

### pytest.ini

Configuration in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "-v",
    "--strict-markers",
    "--cov-report=term-missing",
]
markers = [
    "slow: marks tests as slow",
    "integration: integration tests",
    "unit: unit tests",
]
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'tv_hml'`

```powershell
# Install package in editable mode
uv pip install -e .
```

**Issue**: Tests pass locally but fail in CI

- Check Python version consistency
- Verify all dependencies in `pyproject.toml`
- Review test isolation (files created/modified)

**Issue**: Coverage report not generated

```powershell
# Clean and regenerate
Remove-Item -Recurse -Force .coverage, reports/coverage/
uv run pytest --cov=src --cov-report=html
```

### Clear Test Caches

```powershell
# Remove pytest cache
Remove-Item -Recurse -Force .pytest_cache

# Remove coverage data
Remove-Item -Recurse -Force .coverage, reports/coverage/

# Remove Python cache
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
```

## Related Documentation

- **[Linting Guide](linting.md)** - Code quality checks
- **[Formatting Guide](formatting.md)** - Code formatting standards
- **[Code Style](code-style.md)** - General style guidelines
- **[CI/CD Pipeline](ci-cd.md)** - Automated testing pipeline

## Next Steps

1. **Increase coverage** - Focus on I/O and transformation modules
2. **Add integration tests** - Test complete pipeline steps
3. **Performance tests** - Benchmark critical operations
4. **Property-based testing** - Use Hypothesis for edge cases
