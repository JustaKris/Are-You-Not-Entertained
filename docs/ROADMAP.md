# Roadmap: Are You Not Entertained

## Objective

Turn the existing movie data collector into a reproducible, grounded AI application that
demonstrates data engineering, agent design, retrieval-augmented generation, API
development, CI/CD, and Kubernetes delivery.

The roadmap is dependency-aware, not strictly sequential. The agent and deployment tracks
can start before the full PySpark and Airflow platform exists. The first portfolio focus is
an agentic application built with LangChain, LangGraph, FastAPI, Docker, Kubernetes, and
a repeatable CI/CD path. Kubernetes should be runnable locally as the primary deployment
example; Azure is an optional hosting target only if it can be used within the available
cost budget.

## Starting Point

The project currently collects data asynchronously from TMDB, OMDB, and The Numbers, stores it in `data/db/movies.duckdb`, and provides CLI commands for collection, database management, and validation. The database schema is defined by numbered migrations in `src/ayne/database/migrations/`, with query helpers available for analysis.

## Recommended Order

### 1. Data foundation (complete)

Establish the contracts that allow every later component to evolve safely.

- [x] Add numbered DuckDB migrations and a schema version table
- [x] Define the movie, ratings, and box-office data contract, including identifiers, types, and null behavior
- [x] Strengthen schema, relational-integrity, freshness, and domain-quality checks
- [x] Keep a small sanitized demo database or fixture in Git
- [x] Record dataset manifests with schema version, source commit, generation time, row counts, and input hashes

**Outcome:** A reproducible, inspectable data source for local development and tests.

### 2. Agentic movie assistant with LangChain and LangGraph

Build a useful, inspectable vertical slice over the current DuckDB data. Keep the data
access and agent contracts replaceable so the structured source or model provider can
evolve later.

- Create a read-only `MovieQueryService` with parameterized, bounded DuckDB queries
- Wrap title lookup, movie details, comparisons, and aggregations as typed LangChain tools
- Build a stateful LangGraph workflow with explicit nodes, transitions, failure handling,
  and a configurable chat-model provider
- Add tool-calling guardrails so the graph can select approved tools but cannot execute
  unrestricted SQL, arbitrary code, or unbounded retrieval
- Keep structured facts and retrieved context distinct, cite the evidence returned by each,
  and distinguish missing data from zero values or no matches
- Add evaluation cases for tool selection, factuality, citation quality, ambiguity, empty
  results, prompt injection, and unsupported questions
- Define model-quality contracts for groundedness, answer completeness, citation accuracy,
  abstention, and structured-output validity
- Add a small golden evaluation set with deterministic tool and retrieval fixtures, then
  run it as a regression gate for prompt, graph, model, and retriever changes
- Measure latency, token usage, cost, tool-call success, retrieval quality, and refusal
  behavior where applicable; document thresholds and known failure modes
- Add optional LangSmith-compatible tracing and evaluation hooks without making the agent
  depend on a hosted observability service
- Expose the agent through a versioned FastAPI application with Pydantic request/response
  models, generated OpenAPI documentation, and health/readiness endpoints

**Outcome:** A tested LangChain/LangGraph agent API with bounded tool calling and grounded
structured queries, without unrestricted SQL or unsupported claims.

### 3. FastAPI container and local Kubernetes delivery

Package and operate the working FastAPI agent locally. Kubernetes is the primary deployment
example for this milestone; it should not depend on a paid cloud cluster.

- Add a small, multi-stage, non-root Docker image with environment-based configuration
- Run FastAPI behind an appropriate ASGI server and expose the OpenAPI/Swagger interface
- Define a read-only data strategy for DuckDB and Parquet
- Add Kubernetes `Deployment`, `Service`, `ConfigMap`, and Secret examples
- Configure resource requests/limits, liveness/readiness probes, graceful shutdown, and
  structured logs
- Add a local `kind` or `minikube` workflow and smoke tests for the API and tool-calling path
- Test failure recovery, configuration errors, and the single-replica constraint when the
  database is local and writable

**Outcome:** A repeatable local Kubernetes deployment of a documented, observable FastAPI
agent with a clear read-only data strategy.

### 4. CI/CD and portable Docker delivery

Connect the tested application to a promotion pipeline that treats the container image,
configuration, data assets, and Kubernetes manifests as versioned release inputs. The
portable Docker deployment is the fallback when Kubernetes is unavailable. Azure remains an
optional target and must pass a cost and resource feasibility check first.

- Run pull-request gates for Python quality, agent evaluations, Docker builds, image
  vulnerability scanning, and Kubernetes manifest/schema validation
- Build immutable, tagged container images and publish them to a registry such as GitHub
  Container Registry or Azure Container Registry
- Document and test the portable fallback with `docker run` or Docker Compose, including
  environment configuration, mounted read-only data, health checks, and graceful shutdown
- Deploy automatically to a disposable or development Kubernetes environment, then run
  API health, readiness, agent tool-calling, and grounded-response smoke tests
- Optionally promote a tested image and matching manifests to Azure only after confirming
  that the selected service's free or low-cost limits cover compute, storage, networking,
  model/API usage, and uptime; otherwise retain the local Kubernetes and Docker examples
- If Azure is used, require explicit environment protection, approvals, and a documented
  rollback procedure
- Use GitHub Actions environments and short-lived federated identity/OIDC credentials where
  supported; never store model keys, provider keys, or cluster credentials in the repository
- Keep secrets and configuration separate from the image through Kubernetes Secrets,
  ConfigMaps, and the selected Azure secret/configuration service
- Verify rollout status, probe behavior, logs, resource usage, and failure recovery after
  deployment; retain test, evaluation, and release artifacts for inspection
- Document the boundary between CI (test and package), CD (deploy and verify), and the
  Kubernetes cluster (schedule, expose, restart, and scale the workload)

**Outcome:** A repeatable, auditable release path from pull request to local Kubernetes or
portable Docker deployment, with an optional cost-gated Azure path.

### 5. Deferred RAG extension

Add retrieval-augmented generation only when the project has a meaningful unstructured
corpus and a question set that benefits from semantic retrieval. RAG is an extension to the
tool-grounded agent, not a prerequisite for the first agent or Kubernetes milestone.

- Curate a permitted corpus such as scripts, reviews, interviews, production notes, or
  source metadata, and record provenance, licensing, and update expectations
- Define document cleaning, chunking, metadata, embedding, indexing, and refresh workflows
- Add LangChain retrievers and a replaceable vector index behind an explicit retrieval tool
- Route questions deliberately between exact DuckDB tools and semantic retrieval; use both
  only when the question genuinely requires both sources
- Evaluate retrieval recall, answer groundedness, citation accuracy, prompt-injection
  resistance, latency, and cost against the tool-only baseline
- Keep RAG optional until the corpus quality and evaluation results justify making it part of
  the default agent path

**Outcome:** An evidence-backed retrieval extension whose corpus, costs, limitations, and
quality benefit are demonstrable rather than assumed.

### 6. Clean data processing with PySpark

Add a scalable transformation path without breaking the current DuckDB workflow.

- Preserve raw API responses as immutable inputs
- Deduplicate, normalize, join, and validate the source data
- Publish cleaned movie, cast, and box-office tables as Parquet
- Make the published tables conform to the data contract from Step 1
- Point the query service at the cleaned output when it is stable

**Outcome:** A documented and reproducible batch-processing pipeline suitable for querying and modeling.

### 7. Orchestration with Airflow

Automate the data lifecycle after the collection and processing commands are independently reliable.

- Define a DAG for collection, transformation, validation, and publishing
- Add retries, task-level logging, freshness checks, and failure notifications
- Publish the dataset manifest as an artifact of each successful run

**Outcome:** A scheduled, observable pipeline with clear stage boundaries.

### 8. Predictive modeling

Use the cleaned contract for box-office prediction and honest model evaluation.

- Engineer features from budget, release timing, genres, ratings, and cast data
- Train and compare baseline and candidate models with appropriate metrics
- Track experiments and model artifacts
- Document leakage risks, missing-data effects, limitations, and intended use
- Optionally expose predictions as a separate API or agent tool

**Outcome:** A reproducible modeling workflow that builds on the same published data used by the agent.

## Dependency Map

```text
Data foundation -> LangChain/LangGraph agent -> FastAPI -> Docker -> local Kubernetes
local Kubernetes -> CI/CD -> optional Azure deployment
LangChain/LangGraph agent -> deferred RAG extension
Data foundation -> PySpark processing -> Airflow orchestration
PySpark processing -> Predictive modeling
```

The first portfolio milestone is the path from **data foundation to LangChain/LangGraph
agent to FastAPI to local Kubernetes, with Docker as the portable fallback and CI/CD as the
release path**. Azure hosting, RAG, PySpark, Airflow, and predictive modeling can be added
incrementally afterward.

## Definition of Done

Every milestone should include:

- Working code and focused tests
- A documented local run path
- Explicit data and operational limitations
- Reproducible configuration without committed secrets
- A small validation or evaluation result that can be shown in an interview

Prefer a smaller system that is demonstrably grounded, testable, and operable over a larger system whose behavior cannot be explained.
