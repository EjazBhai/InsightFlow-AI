# Architecture

The Streamlit workspace renders user-facing analytics. FastAPI exposes health and analytic endpoints. `AnalyticsAgent` is a LangGraph state machine with explicit `plan`, `execute_readonly_sql`, and `summarize` nodes. The repository is the sole DuckDB access point. Ingestion produces Parquet and a quality report before database initialization.

The model boundary is deliberately narrow: the deterministic demo planner supplies analytical SQL. A future provider adapter must return typed plans only and may never bypass `validate_readonly_sql`.
