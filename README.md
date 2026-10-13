# InsightFlow AI

**A local-first, safety-focused business intelligence analyst that turns natural-language questions into validated SQL and actionable analytics.**

InsightFlow AI is a demonstration application for exploring business data through a Streamlit dashboard and a FastAPI backend. Its workflow combines agent orchestration, SQL validation, DuckDB, and Parquet-based data processing to make analytical questions easier to ask and their results easier to inspect.

> **Project status:** Runnable local application and development project. Cloud deployment has not yet been verified. Run the supplied tests and evaluation scripts to obtain measurements for your environment.

## Table of contents

- [InsightFlow AI](#insightflow-ai)
  - [Table of contents](#table-of-contents)
  - [Problem statement](#problem-statement)
  - [Solution](#solution)
  - [Features](#features)
  - [Architecture](#architecture)
  - [Technology stack](#technology-stack)
  - [Repository structure](#repository-structure)
  - [Prerequisites](#prerequisites)
  - [Getting started](#getting-started)
    - [1. Clone the repository](#1-clone-the-repository)
    - [2. Create a virtual environment](#2-create-a-virtual-environment)
    - [3. Install dependencies](#3-install-dependencies)
    - [4. Prepare the fixture data](#4-prepare-the-fixture-data)
    - [5. Start the API](#5-start-the-api)
    - [6. Start the dashboard](#6-start-the-dashboard)
  - [Run with Docker Compose](#run-with-docker-compose)
  - [API documentation](#api-documentation)
  - [Testing and evaluation](#testing-and-evaluation)
  - [Data provenance and metric definitions](#data-provenance-and-metric-definitions)
  - [Security design](#security-design)
  - [Limitations](#limitations)
  - [Deployment considerations](#deployment-considerations)
  - [Roadmap](#roadmap)
  - [License](#license)

## Problem statement

Business users often need answers to questions such as:

- How are sales changing over time?
- Which products or customer groups contribute to sales?
- How should returns and cancellations be reflected in reporting?
- Can an analytical result be explained and reproduced?

Traditional workflows may require users to understand SQL, navigate multiple tools, or rely on dashboards that do not make metric definitions and data assumptions clear.

Natural-language analytics can simplify this workflow, but executing model-generated SQL without strict controls can introduce incorrect queries, misleading results, or unsafe database access.

## Solution

InsightFlow AI demonstrates a controlled analytics workflow:

1. Accept an analytical question through the application.
2. Process the question through the configured workflow.
3. Construct or select an analytical query.
4. Validate the SQL against an explicit safety policy.
5. Execute permitted read-only queries against approved DuckDB data.
6. Present the results and visualizations in the dashboard.

The application includes a deterministic local demo mode that does not require a paid model API. Optional model integration is configuration-dependent and should be tested separately.

## Features

- **Interactive analytics dashboard:** A Streamlit interface for exploring analytical results.
- **API backend:** FastAPI endpoints for application operations.
- **Agent workflow:** LangGraph-based workflow organization.
- **SQL safety boundary:** SQLGlot parsing and policy checks before query execution.
- **Local analytical storage:** DuckDB and Parquet for analytical data workflows.
- **Data preparation:** A script to prepare the included deterministic fixture data.
- **Metric handling:** Explicit treatment of sales, returns, and cancellations.
- **Automated checks:** Pytest, coverage, Ruff, and GitHub Actions configuration.
- **Container support:** Dockerfile and Docker Compose configuration for local multi-service execution.

## Architecture

```text
User
  |
  v
Streamlit dashboard
  |
  v
FastAPI backend
  |
  v
LangGraph workflow
  |
  v
SQLGlot validation and safety policy
  |
  v
DuckDB query execution
  |
  v
Approved analytical data (Parquet)
  |
  v
Results and visualizations
```

The SQL safety policy is an essential boundary between query generation and database execution. Queries should be rejected when they exceed the supported SQL policy.

## Technology stack

| Component | Technology | Purpose |
|---|---|---|
| User interface | Streamlit | Dashboard and interaction |
| API | FastAPI | Backend HTTP endpoints |
| Workflow orchestration | LangGraph | Organize analytical steps |
| SQL parsing and validation | SQLGlot | Parse and validate SQL |
| Analytical engine | DuckDB | Local analytical query execution |
| Data processing | pandas, PyArrow | Tabular processing and Parquet support |
| Visualization | Plotly | Interactive charts |
| Configuration and schemas | Pydantic, pydantic-settings | Settings and data validation |
| Testing | Pytest, pytest-cov | Automated tests and coverage |
| Code quality | Ruff | Linting and import checks |
| Packaging and deployment | Python packaging, Docker | Installation and container execution |

## Repository structure

```text
InsightFlow-AI/
├── .github/
│   └── workflows/          # CI workflow
├── apps/
│   └── streamlit_app/      # Dashboard application and UI helpers
├── data/
│   └── fixtures/           # Small deterministic fixture data
├── docs/                   # Project documentation
├── evaluations/             # Evaluation inputs and related assets
├── scripts/
│   ├── prepare_data.py      # Prepare fixture data
│   ├── run_evaluation.py    # Run the evaluation suite
│   └── smoke_test.py        # API smoke test
├── src/
│   └── insightflow/
│       ├── agent/           # Analytical workflow
│       ├── analytics/       # Metrics
│       ├── api/             # FastAPI application
│       ├── data/            # Data pipeline
│       ├── database/        # Data repository
│       ├── schemas/         # Data models
│       └── security/        # SQL safety policy
├── tests/                   # Automated tests
├── .env.example             # Example configuration
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml            # Package metadata and dependencies
├── requirements.txt          # Runtime dependency installation
└── README.md
```

## Prerequisites

For local development:

- Python 3.11 or newer
- Git
- PowerShell on Windows, or a compatible shell on Linux/macOS

For container execution:

- Docker Desktop on Windows/macOS, or Docker Engine with the Compose plugin on Linux

## Getting started

### 1. Clone the repository

```powershell
git clone https://github.com/EjazBhai/InsightFlow-AI.git
cd InsightFlow-AI
```

The default GitHub branch may not yet contain the latest application code. Until the release is published to `main`, check out the branch containing the application:

```powershell
git switch feature/evaluation
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks virtual-environment activation, use the environment's Python executable directly or follow your organization's script execution policy.

### 3. Install dependencies

Install the project and its development tools:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Alternatively, install the runtime dependencies listed in `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

### 4. Prepare the fixture data

```powershell
python scripts/prepare_data.py
```

### 5. Start the API

In the first terminal:

```powershell
uvicorn insightflow.api.app:app --reload --host 127.0.0.1 --port 8000
```

### 6. Start the dashboard

In a second terminal, activate the same virtual environment and run:

```powershell
streamlit run apps/streamlit_app/app.py --server.port 8501
```

Open the dashboard at `http://localhost:8501`.

## Run with Docker Compose

Docker Compose provides the API and dashboard services. From the project root:

```powershell
docker compose config
docker compose up -d --build
docker compose ps
```

With the current local port mapping, the intended addresses are:

| Service | Local address |
|---|---|
| Dashboard | `http://localhost:8502` |
| API | `http://localhost:8000` |
| Interactive API documentation | `http://localhost:8000/docs` |
| API health check | `http://localhost:8000/health/live` |

Confirm the actual health response before considering the containers ready.

View service logs:

```powershell
docker compose logs --tail 100 api dashboard
```

Stop the services:

```powershell
docker compose down
```

The named Docker volume is intended to preserve data across container recreation. Inspect the Compose configuration before removing volumes, because deleting a volume may delete stored data.

## API documentation

When the API is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`
- Liveness endpoint: `http://localhost:8000/health/live`

Endpoint availability and request schemas should be verified against the running version of the application.

## Testing and evaluation

Run the automated test suite, excluding tests marked as performance tests:

```powershell
python -m pytest -v -m "not performance" --cov=insightflow
```

Run lint checks:

```powershell
python -m ruff check .
```

Check the installed environment for dependency conflicts:

```powershell
python -m pip check
```

Run the project evaluation:

```powershell
python scripts/run_evaluation.py
```

Run the smoke test after starting the API:

```powershell
python scripts/smoke_test.py
```

Report the actual test counts, coverage, and evaluation results produced by these commands. Do not treat a successful lint check as evidence that runtime behavior or deployment has been verified.

## Data provenance and metric definitions

The project references the [UCI Online Retail dataset](https://archive.ics.uci.edu/dataset/352/online+retail), hosted by the UCI Machine Learning Repository. The included fixture is a small deterministic test dataset and is not representative of a production deployment.

The intended metric conventions are:

- **Gross sales:** positive quantity multiplied by unit price.
- **Net sales:** quantity multiplied by unit price, including negative return or cancellation records.
- **Cancellations:** records identified by invoice IDs beginning with `C` or by negative quantities, according to the pipeline's implemented rules.
- **Profit:** not calculated from sales alone; cost and margin information is required.
- **Missing customer IDs:** should remain missing rather than being invented.

Use these definitions consistently when comparing results. Confirm the implemented transformations before using outputs for business decisions.

## Security design

The project's SQL safety policy is designed to constrain database access:

- Permit only supported read-only `SELECT` queries.
- Validate query structure before execution.
- Restrict access to approved tables and columns.
- Reject unsupported statements and prohibited operations.
- Apply result-size limits.
- Avoid exposing filesystem, shell, or database-write tools to the analytical interface.

These controls are application-level safeguards, not a substitute for production security review. Before exposing the service to a network, validate the policy against adversarial SQL, configure network access and authentication appropriately, and use least-privilege deployment settings.

## Limitations

The current project is a development and demonstration foundation. The following capabilities are not claimed as completed:

- Automatic downloading and production ingestion of the full source dataset.
- Persistent chat history.
- Optional Chroma-based retrieval.
- A verified hosted-model integration.
- A verified cloud deployment with production monitoring and authentication.

Model integration and deployment depend on configuration and require separate validation.

## Deployment considerations

Before deploying outside a local development environment:

1. Verify API and dashboard health checks in the built image.
2. Configure secrets through the hosting platform's secret manager or environment settings.
3. Restrict network access and enable suitable authentication and TLS at the deployment boundary.
4. Configure persistent storage and backups for data that must survive restarts.
5. Review container resource limits, logs, restart policy, and monitoring.
6. Re-run automated tests and smoke tests against the release image.
7. Pin or lock dependency versions for reproducible production builds.
8. Verify all endpoints and security controls in the target environment.

The supplied Docker configuration supports local container execution; production readiness should be claimed only after these checks are completed in the intended hosting environment.

## Roadmap

Potential next steps include:

- Complete and verify a production-oriented Docker deployment.
- Add reproducible dependency locking.
- Expand evaluation cases for ambiguous natural-language questions and SQL safety.
- Add integration tests for container startup and health checks.
- Implement optional model-provider integration with explicit configuration.
- Add operational observability and deployment documentation.
- Publish the validated application code on the default GitHub branch.

## License

See the repository's `LICENSE` file for licensing terms.
