# Implementation checklist

## Completed in the local core

- [x] Git repository with `main`, `develop`, and scoped feature branches
- [x] Pyproject dependency definition and environment template
- [x] Deterministic fixture ingestion to Parquet with quality report
- [x] DuckDB analytical repository and documented metric semantics
- [x] LangGraph controlled planner/executor/summarizer flow
- [x] SQLGlot-based SELECT-only allowlist policy and security tests
- [x] FastAPI health, analytics, agent, feedback, and evaluation endpoints
- [x] Streamlit executive, analyst, explorer, quality, and settings views
- [x] Version-controlled 50-case deterministic evaluation corpus
- [x] Docker Compose, CI workflow, smoke-test script, and core documentation

## Requires execution or further implementation

- [ ] Install Python, install dependencies, run tests/coverage/evaluation
- [ ] Start Docker Desktop and verify image build/Compose smoke test
- [ ] Download and validate the full UCI source dataset after network approval
- [ ] Connect an optional Ollama or hosted tool-model adapter
- [ ] Add optional Chroma/SentenceTransformers retrieval and its metrics
- [ ] Capture real UI screenshots after a successful local run
- [ ] Configure remote, create PRs, and deploy only with credentials/platform access
