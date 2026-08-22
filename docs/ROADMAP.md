# Roadmap: Are You Not Entertained

## Objective

Turn the existing movie data collector into a reproducible, grounded AI application that demonstrates data engineering, agent design, API development, and Kubernetes delivery.

The roadmap is dependency-aware, not strictly sequential. The chatbot and deployment tracks can start before the full PySpark and Airflow platform exists.

## Starting Point

The project currently collects data asynchronously from TMDB, OMDB, and The Numbers, stores it in `data/db/movies.duckdb`, and provides CLI commands for collection, database management, and validation. The database schema is defined in `src/ayne/database/schema.sql`, with query helpers available for analysis.

## Recommended Order

### 1. Data foundation

Establish the contracts that allow every later component to evolve safely.

- Add numbered DuckDB migrations and a schema version table
- Define the movie, ratings, and box-office data contract, including identifiers, types, and null behavior
- Strengthen schema, relational-integrity, freshness, and domain-quality checks
- Keep a small sanitized demo database or fixture in Git
- Record dataset manifests with schema version, source commit, generation time, row counts, and input hashes

**Outcome:** A reproducible, inspectable data source for local development and tests.

### 2. Grounded conversational agent

Build a useful vertical slice over the current DuckDB data. Replace the data source later without changing the agent contract.

- Create a read-only `MovieQueryService` with parameterized and bounded queries
- Add tools for title lookup, movie details, comparisons, and aggregations
- Build the LangGraph workflow and keep the model provider configurable
- Return evidence fields and distinguish missing data from zero values or no matches
- Add evaluation cases for factuality, ambiguity, empty results, and unsupported questions
- Expose the agent through FastAPI with health and readiness endpoints

**Outcome:** A tested API that answers questions from the dataset without unrestricted SQL or unsupported claims.

### 3. Container and Kubernetes delivery

Deploy the working API locally before targeting a hosted cluster.

- Add a small, non-root Docker image with environment-based configuration
- Define a read-only data strategy for DuckDB or Parquet
- Add Kubernetes `Deployment`, `Service`, `ConfigMap`, and Secret examples
- Configure resource limits, liveness/readiness probes, and structured logs
- Run the service on `kind` or `minikube`, then test scaling and failure recovery
- Document the single-replica constraint if the database file is local or writable

**Outcome:** A repeatable local Kubernetes deployment of the grounded agent.

### 4. Clean data processing with PySpark

Add a scalable transformation path without breaking the current DuckDB workflow.

- Preserve raw API responses as immutable inputs
- Deduplicate, normalize, join, and validate the source data
- Publish cleaned movie, cast, and box-office tables as Parquet
- Make the published tables conform to the data contract from Step 1
- Point the query service at the cleaned output when it is stable

**Outcome:** A documented and reproducible batch-processing pipeline suitable for querying and modeling.

### 5. Orchestration with Airflow

Automate the data lifecycle after the collection and processing commands are independently reliable.

- Define a DAG for collection, transformation, validation, and publishing
- Add retries, task-level logging, freshness checks, and failure notifications
- Publish the dataset manifest as an artifact of each successful run

**Outcome:** A scheduled, observable pipeline with clear stage boundaries.

### 6. Predictive modeling

Use the cleaned contract for box-office prediction and honest model evaluation.

- Engineer features from budget, release timing, genres, ratings, and cast data
- Train and compare baseline and candidate models with appropriate metrics
- Track experiments and model artifacts
- Document leakage risks, missing-data effects, limitations, and intended use
- Optionally expose predictions as a separate API or agent tool

**Outcome:** A reproducible modeling workflow that builds on the same published data used by the agent.

## Dependency Map

```text
Data foundation -> Grounded agent -> Docker -> Kubernetes
Data foundation -> PySpark processing -> Airflow orchestration
PySpark processing -> Predictive modeling
```

The first portfolio milestone is the path from **data foundation to grounded agent to local Kubernetes**. PySpark, Airflow, and predictive modeling can be added incrementally afterward.

## Definition of Done

Every milestone should include:

- Working code and focused tests
- A documented local run path
- Explicit data and operational limitations
- Reproducible configuration without committed secrets
- A small validation or evaluation result that can be shown in an interview

Prefer a smaller system that is demonstrably grounded, testable, and operable over a larger system whose behavior cannot be explained.
