# InsightFlow AI

InsightFlow AI is a local-first, agentic business-intelligence analyst for small e-commerce teams. It turns bounded natural-language questions into validated read-only DuckDB queries, then shows evidence, definitions, results, and charts.

## Architecture

`Streamlit → FastAPI → LangGraph workflow → SQLGlot safety policy → DuckDB/Parquet`

The deterministic demo mode works without a paid API. Configure an Ollama-compatible provider in `.env` for a local tool-capable model; model integration is intentionally not auto-downloaded or started.

## Quick start

Python 3.11+ is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python scripts/prepare_data.py
uvicorn insightflow.api.app:app --reload
# in a second terminal
streamlit run apps/streamlit_app/app.py
```

Open `http://localhost:8501`; FastAPI docs are at `http://localhost:8000/docs`.

## Tests and evaluation

```powershell
pytest -m "not performance" --cov=insightflow
python scripts/run_evaluation.py
ruff check .
docker compose up --build
```

Run `python scripts/smoke_test.py` once the API is running. Evaluation reports are generated rather than claimed in advance.

## Data provenance and metric treatment

The primary source is the [UCI Online Retail dataset](https://archive.ics.uci.edu/dataset/352/online+retail), UCI Machine Learning Repository (Chen, 2015). The included fixture is a tiny deterministic test dataset, not production data. Source data must remain outside Git by default.

- Gross sales: positive quantity × unit price.
- Net sales: all quantity × unit price, including negative return/cancellation records.
- Cancellations: invoice IDs beginning `C` or negative-quantity records; they are retained.
- Revenue is not profit: the source contains no costs or margins.
- Customer IDs are never invented when missing.

## Security model

Only one parsed `SELECT` statement over approved tables/columns is permitted. File readers, extension/configuration statements, unapproved tables, DDL/DML, and oversized result sets are rejected deterministically before DuckDB execution. The UI and agent never receive filesystem, shell, or write-database tools.

## Known limitations

This first runnable core includes a deterministic local planner, fixture ingestion, dashboard, FastAPI, safety boundary, tests, and golden set. It does not yet download the full UCI file, persist chat history, implement optional Chroma retrieval, use a hosted-model adapter, or provide a verified cloud deployment. Run the supplied test/evaluation commands to produce truthful measurements for your environment.

## Resume-ready description

Built InsightFlow AI, a local-first agentic BI app using FastAPI, Streamlit, LangGraph, DuckDB, Parquet, and SQL AST validation; include measured test coverage and golden-set results after running the project evaluation.
