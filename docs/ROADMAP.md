# Roadmap: Are You Not Entertained

This document outlines the planned evolution of the project from a data collection tool into a full-stack data engineering, agentic AI, and MLOps showcase. Each phase is scoped to be independently useful and independently deployable, while building toward a cohesive end-to-end system.

## Current State

The project currently handles asynchronous data collection from TMDB, OMDB, and The Numbers APIs, storing structured results in a local DuckDB database, with a CLI tool for triggering and managing collection runs. Predictive modeling and downstream analysis have not yet been built.

## Phase 1 — Data Processing with PySpark

**Goal:** Transform raw, collected API data into clean, structured, analysis-ready tables suitable for both querying and modeling.

- Define a clear schema for cleaned movie, cast, and box office data
- Implement PySpark jobs to deduplicate, normalize, and join data across the three source APIs
- Handle missing values, inconsistent formatting, and mismatched identifiers between sources
- Output cleaned tables in a format suitable for downstream querying (e.g., Parquet)
- Document data quality decisions and known limitations

**Skills demonstrated:** distributed data processing, PySpark DataFrame API, data cleaning and normalization at scale, ETL design.

## Phase 2 — Pipeline Orchestration with Airflow

**Goal:** Automate and orchestrate the full pipeline from raw collection through to cleaned output as a scheduled, monitored workflow.

- Define a DAG covering: API collection → raw storage → PySpark cleaning → cleaned storage
- Add retry logic, failure alerting, and basic data validation checks between stages
- Document the DAG structure and scheduling approach

**Skills demonstrated:** workflow orchestration, pipeline reliability and monitoring, production data engineering practices.

## Phase 3 — Conversational Agent with LangGraph

**Goal:** Build an agent capable of answering natural language questions about the movie dataset by reasoning over the cleaned data.

- Design an agent graph with distinct tools (e.g., query database, run aggregation, compare titles, look up a specific film)
- Implement grounding and guardrails to reduce hallucinated or incorrect answers, consistent with the approach used in the [Trump Rally Speeches RAG chatbot](https://github.com/JustaKris/Trump-Rally-Speeches-NLP-Chatbot)
- Add evaluation cases covering a range of question types and edge cases
- Expose the agent through a simple API (FastAPI)

**Skills demonstrated:** agentic AI system design, LangGraph, tool-calling, grounding and hallucination mitigation, API development.

## Phase 4 — Predictive Modeling

**Goal:** Build and evaluate models predicting box office performance based on the cleaned dataset.

- Feature engineering from cleaned data (cast, budget, release timing, genre, etc.)
- Train and compare candidate models with appropriate evaluation metrics
- Document model limitations and performance honestly, consistent with the project's overall approach to transparency

**Skills demonstrated:** feature engineering, model selection and evaluation, applied machine learning.

## Phase 5 — Deployment with Docker and Kubernetes

**Goal:** Containerize and deploy the conversational agent as a production-style service.

- Containerize the FastAPI service with Docker
- Write Kubernetes manifests (Deployment, Service, ConfigMap) for the service
- Document the deployment process and configuration

**Skills demonstrated:** containerization, Kubernetes fundamentals, production deployment practices.

## Guiding Principles

- Each phase should be independently functional and documented before moving to the next.
- Prioritize honest documentation of limitations over polish — this project favors transparency about what works and what doesn't.
- Reuse patterns and practices already established in other projects in this portfolio where applicable, rather than reinventing them.
