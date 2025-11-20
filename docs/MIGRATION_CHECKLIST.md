# ✅ Migration Checklist & Progress Tracker

**Purpose**: Track your progress through the modernization process  
**Usage**: Check off items as you complete them  
**Last Updated**: November 20, 2025

---

## 🎯 Phase 1: Database Setup (Week 1)

### Day 1: Environment Setup
- [x] Install DuckDB (`uv add duckdb`)
- [x] Fix import in `duckdb_client.py`
- [ ] Create `data/db/` directory
- [ ] Test DuckDB connection
- [ ] Verify schema.sql exists

### Day 2: Database Initialization
- [ ] Create `scripts/init_database.py`
- [ ] Run schema creation
- [ ] Verify all 5 tables exist
- [ ] Test basic INSERT/SELECT queries
- [ ] Document database location in README

### Day 3: Basic CRUD Operations
- [ ] Create `scripts/test_database.py`
- [ ] Test upsert functionality
- [ ] Test parameterized queries
- [ ] Test joins between tables
- [ ] Verify data persistence

### Day 4: Unit Tests
- [ ] Create `tests/unit/test_duckdb_client.py`
- [ ] Test schema creation
- [ ] Test upsert operations
- [ ] Test query methods
- [ ] Test error handling
- [ ] Run pytest and verify passing

### Day 5: Documentation
- [ ] Document database schema in `docs/DATABASE_SCHEMA.md`
- [ ] Add DuckDB usage examples
- [ ] Update README with database info
- [ ] Create backup strategy doc

**Phase 1 Completion Criteria**:
- ✅ DuckDB operational with all tables
- ✅ Unit tests passing
- ✅ Documentation complete

---

## 🔄 Phase 2: API Client Refactoring (Week 2)

### Day 1: TMDB Client
- [ ] Create `src/data_collection/tmdb_client.py`
- [ ] Remove database coupling
- [ ] Use httpx instead of requests
- [ ] Implement `discover_movies()` method
- [ ] Implement `get_movie_details()` method
- [ ] Add error handling and logging

### Day 2: OMDB Client
- [ ] Create `src/data_collection/omdb_client.py`
- [ ] Remove database coupling
- [ ] Use httpx instead of requests
- [ ] Implement `get_movie_by_imdb_id()` method
- [ ] Implement `get_batch_movies()` method
- [ ] Add rating parsing logic

### Day 3: Unit Tests for Clients
- [ ] Create `tests/unit/test_tmdb_client.py`
- [ ] Create `tests/unit/test_omdb_client.py`
- [ ] Mock API responses with fixtures
- [ ] Test error handling
- [ ] Test rate limiting
- [ ] Test data normalization

### Day 4: Integration Script
- [ ] Create `scripts/collect_data.py`
- [ ] Integrate TMDB client + DuckDB
- [ ] Integrate OMDB client + DuckDB
- [ ] Add progress logging
- [ ] Add error recovery
- [ ] Test with small batch (10 movies)

### Day 5: Validation
- [ ] Run full data collection (100 movies)
- [ ] Verify data in DuckDB
- [ ] Check for duplicates
- [ ] Validate data quality
- [ ] Document collection workflow

**Phase 2 Completion Criteria**:
- ✅ Modern API clients (no DB coupling)
- ✅ Working data collection orchestrator
- ✅ Tests passing

---

## 🧹 Phase 3: Legacy Code Cleanup (Week 3)

### Day 1: Backup
- [ ] Git commit current state
- [ ] Tag release: `git tag pre-cleanup-v1.0`
- [ ] Push to remote
- [ ] Create backup branch: `git checkout -b backup-old-code`

### Day 2: Remove PostgreSQL Code
- [ ] Delete `database/` folder
- [ ] Remove `from database import ...` references
- [ ] Delete `src/db/postgres/` folder
- [ ] Update imports in all affected files
- [ ] Run `grep -r "from database" .` to find stragglers

### Day 3: Remove Old Dependencies
- [ ] Remove `sqlalchemy` from `pyproject.toml`
- [ ] Remove `psycopg2-binary` from `pyproject.toml`
- [ ] Remove `dill` (replace with joblib)
- [ ] Run `uv sync` to update lockfile
- [ ] Run `uv pip list` to verify

### Day 4: Delete Old Files
- [ ] Delete `src/data_collection/tmdb.py` (replaced)
- [ ] Delete `src/data_collection/omdb.py` (replaced)
- [ ] Delete `scripts/update_db.py` (replaced)
- [ ] Delete any unused CSV files
- [ ] Clean up `__pycache__` directories

### Day 5: Fix Broken References
- [ ] Search for broken imports
- [ ] Update notebook imports
- [ ] Fix any remaining test failures
- [ ] Run full test suite
- [ ] Update README to reflect changes

**Phase 3 Completion Criteria**:
- ✅ No PostgreSQL dependencies
- ✅ All old code removed
- ✅ Tests passing

---

## ⚙️ Phase 4: Configuration Enhancement (Week 4)

### Day 1: Update Settings
- [ ] Enhance `src/core/config/settings.py`
- [ ] Add nested `DatabaseSettings`
- [ ] Add nested `APISettings`
- [ ] Support `env_nested_delimiter="__"`
- [ ] Add validation for all fields

### Day 2: Update Config Files
- [ ] Update `configs/development.yaml`
- [ ] Update `configs/staging.yaml`
- [ ] Update `configs/production.yaml`
- [ ] Add database section to all configs
- [ ] Add API section to all configs

### Day 3: Update .env
- [ ] Add `DATABASE__PATH` variable
- [ ] Add `API__TMDB_API_KEY` variable
- [ ] Add `API__OMDB_API_KEY` variable
- [ ] Update `.env.example` template
- [ ] Document all env vars

### Day 4: Test Configuration
- [ ] Test loading from .env
- [ ] Test loading from YAML
- [ ] Test environment overrides
- [ ] Test validation errors
- [ ] Create config tests

### Day 5: Documentation
- [ ] Create `docs/CONFIGURATION.md`
- [ ] Document all settings
- [ ] Add examples for each environment
- [ ] Document precedence rules
- [ ] Update README

**Phase 4 Completion Criteria**:
- ✅ Nested configuration working
- ✅ Environment overrides functional
- ✅ Documentation complete

---

## 🔬 Phase 5: Testing & Quality (Week 5)

### Day 1: Unit Tests
- [ ] Achieve 80% coverage for `src/db/`
- [ ] Achieve 80% coverage for `src/data_collection/`
- [ ] Achieve 80% coverage for `src/core/config/`
- [ ] Fix any failing tests
- [ ] Generate coverage report

### Day 2: Integration Tests
- [ ] Create `tests/integration/test_data_collection.py`
- [ ] Test full TMDB → DuckDB flow
- [ ] Test full OMDB → DuckDB flow
- [ ] Test data quality checks
- [ ] Test error recovery

### Day 3: Code Quality
- [ ] Run `black .` (format code)
- [ ] Run `ruff check .` (lint code)
- [ ] Run `mypy src/` (type check)
- [ ] Fix all linting issues
- [ ] Add pre-commit hooks

### Day 4: Performance Testing
- [ ] Benchmark DuckDB query performance
- [ ] Benchmark API collection speed
- [ ] Benchmark Parquet I/O
- [ ] Identify bottlenecks
- [ ] Document findings

### Day 5: Documentation Review
- [ ] Review all docstrings
- [ ] Update README.md
- [ ] Update CONTRIBUTING.md
- [ ] Create CHANGELOG.md
- [ ] Generate API docs (pdoc3)

**Phase 5 Completion Criteria**:
- ✅ >80% test coverage
- ✅ All linting passing
- ✅ Documentation complete

---

## 🚀 Phase 6: Pipeline Modernization (Week 6)

### Day 1: Data Ingestion Pipeline
- [ ] Create `src/pipelines/data_ingestion.py`
- [ ] Orchestrate TMDB + OMDB + The Numbers
- [ ] Add progress tracking
- [ ] Add error handling
- [ ] Add resume capability

### Day 2: Preprocessing Pipeline
- [ ] Update `src/data_preprocessing/preprocess.py`
- [ ] Read from DuckDB instead of CSV
- [ ] Write to Parquet instead of CSV
- [ ] Modernize imputation logic
- [ ] Add data validation

### Day 3: Feature Engineering
- [ ] Update `src/features/feature_engineering.py`
- [ ] Add temporal features
- [ ] Add interaction features
- [ ] Add encoding logic
- [ ] Test feature quality

### Day 4: Training Pipeline
- [ ] Update `src/models/train.py`
- [ ] Read training data from Parquet
- [ ] Add MLflow tracking
- [ ] Save models with joblib
- [ ] Add model validation

### Day 5: End-to-End Test
- [ ] Run full pipeline start-to-finish
- [ ] Collect data → preprocess → train
- [ ] Verify outputs at each stage
- [ ] Measure total runtime
- [ ] Document pipeline

**Phase 6 Completion Criteria**:
- ✅ Working end-to-end pipeline
- ✅ All stages tested
- ✅ Performance acceptable

---

## 📊 Phase 7: Notebooks Update (Week 7)

### Day 1: Data Collection Notebook
- [ ] Update notebook 01 imports
- [ ] Use new TMDB client
- [ ] Use new OMDB client
- [ ] Update visualizations
- [ ] Test execution

### Day 2: EDA Notebook
- [ ] Update notebook 02 imports
- [ ] Read from DuckDB
- [ ] Update plots
- [ ] Add new analyses
- [ ] Test execution

### Day 3: Preprocessing Notebook
- [ ] Update notebook 03 imports
- [ ] Use modern preprocessing
- [ ] Update feature engineering
- [ ] Test execution
- [ ] Document changes

### Day 4: Modeling Notebook
- [ ] Update notebook 04 imports
- [ ] Use joblib for models
- [ ] Add MLflow logging
- [ ] Update evaluation
- [ ] Test execution

### Day 5: Cleanup
- [ ] Clear all outputs
- [ ] Run all notebooks fresh
- [ ] Fix any errors
- [ ] Update notebook README
- [ ] Archive old notebooks

**Phase 7 Completion Criteria**:
- ✅ All notebooks execute without errors
- ✅ Use modern code patterns
- ✅ Well-documented

---

## 🎉 Final Validation Checklist

### Code Quality
- [ ] All tests passing (`pytest`)
- [ ] >80% code coverage
- [ ] No linting errors (`ruff check .`)
- [ ] Type checking passing (`mypy src/`)
- [ ] Code formatted (`black .`)

### Documentation
- [ ] README.md up to date
- [ ] All docs/ files complete
- [ ] API documentation generated
- [ ] Configuration documented
- [ ] Examples provided

### Functionality
- [ ] Data collection working
- [ ] Database operations working
- [ ] Preprocessing pipeline working
- [ ] Model training working
- [ ] All notebooks executing

### Performance
- [ ] DuckDB queries < 100ms
- [ ] API collection < 5s per movie
- [ ] Parquet I/O < 2s for 10k rows
- [ ] Pipeline completes in reasonable time

### Security
- [ ] No secrets in code
- [ ] .env in .gitignore
- [ ] API keys not committed
- [ ] Dependencies audited (`pip-audit`)

### Project Structure
- [ ] Logical directory organization
- [ ] Consistent naming conventions
- [ ] No dead code
- [ ] Clear separation of concerns

---

## 📈 Progress Tracking

**Overall Progress**: 0/7 phases complete

```
Phase 1: Database Setup         [░░░░░░░░░░] 0%
Phase 2: API Refactoring       [░░░░░░░░░░] 0%
Phase 3: Legacy Cleanup        [░░░░░░░░░░] 0%
Phase 4: Configuration         [░░░░░░░░░░] 0%
Phase 5: Testing & Quality     [░░░░░░░░░░] 0%
Phase 6: Pipeline Modernization[░░░░░░░░░░] 0%
Phase 7: Notebooks Update      [░░░░░░░░░░] 0%
```

**Start Date**: November 20, 2025  
**Target Completion**: 7 weeks from start  
**Current Phase**: Phase 1 (Database Setup)

---

## 🎯 Quick Wins (Do These First)

These give immediate value:

1. **✅ Fix DuckDB Import** (5 min) - DONE!
2. **Initialize Database** (10 min) - Creates working DB
3. **Simple Data Collection** (20 min) - Gets first data
4. **Create Unit Tests** (30 min) - Ensures quality
5. **Update README** (15 min) - Documents progress

---

## 🆘 Blockers & Issues Log

### Current Blockers
- None yet

### Resolved Issues
- [x] DuckDB import path incorrect → Fixed in duckdb_client.py

### Questions to Resolve
- [ ] Should we migrate existing CSV data to DuckDB?
- [ ] Keep old notebooks or archive?
- [ ] Deploy to Azure or AWS first?

---

## 📝 Notes & Learnings

**Week 1**:

-

**Week 2**:

-

**Week 3**:

-

---

## 🎓 Success Metrics

When you can answer "YES" to these questions, you're done:

1. **Can you collect new movie data with one command?**
   - [ ] Yes, `python scripts/collect_data.py` works

2. **Is all data in DuckDB and Parquet?**
   - [ ] Yes, no CSV files in use

3. **Are there zero PostgreSQL dependencies?**
   - [ ] Yes, removed from pyproject.toml

4. **Do all tests pass?**
   - [ ] Yes, `pytest` shows all green

5. **Can you train a model end-to-end?**
   - [ ] Yes, full pipeline executes

6. **Is the codebase clean and documented?**
   - [ ] Yes, no legacy code remains

---

**Checklist Version**: 1.0  
**Last Updated**: November 20, 2025  
**Project**: Are You Not Entertained?
