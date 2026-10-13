from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request

from insightflow.agent import AnalyticsAgent
from insightflow.config import get_settings
from insightflow.database import AnalyticsRepository
from insightflow.schemas import FeedbackRequest, QueryRequest


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    repository = AnalyticsRepository(settings)
    app.state.repository = repository
    app.state.agent = AnalyticsAgent(repository)
    yield


app = FastAPI(title="InsightFlow AI", version="0.1.0", lifespan=lifespan)


def _repository(request: Request) -> AnalyticsRepository:
    return cast(AnalyticsRepository, request.app.state.repository)


@app.middleware("http")
async def correlation_id(request: Request, call_next: Any) -> Any:
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "generated-by-api")
    return response


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready")
def ready(request: Request) -> dict[str, str]:
    try:
        _repository(request).summary()
        return {"status": "ready"}
    except Exception as exc:
        raise HTTPException(
            503, "Dataset has not been initialized. Run scripts/prepare_data.py."
        ) from exc


@app.get("/api/v1/analytics/summary")
def summary(request: Request) -> dict[str, Any]:
    return _repository(request).summary()


@app.get("/api/v1/analytics/trends")
def trends(request: Request) -> list[dict[str, Any]]:
    return _repository(request).execute(
        "SELECT date_trunc('month', invoice_date) AS month, SUM(revenue) AS net_sales FROM transactions GROUP BY month ORDER BY month"
    )


@app.get("/api/v1/analytics/products")
def products(request: Request) -> list[dict[str, Any]]:
    return _repository(request).execute(
        "SELECT description, SUM(revenue) AS net_sales FROM transactions GROUP BY description ORDER BY net_sales DESC"
    )


@app.get("/api/v1/analytics/countries")
def countries(request: Request) -> list[dict[str, Any]]:
    return _repository(request).execute(
        "SELECT country, SUM(revenue) AS net_sales FROM transactions GROUP BY country ORDER BY net_sales DESC"
    )


@app.post("/api/v1/analytics/query")
def analytics_query(payload: QueryRequest, request: Request) -> Any:
    return request.app.state.agent.query(payload.question)


@app.post("/api/v1/agent/query")
def agent_query(payload: QueryRequest, request: Request) -> Any:
    return request.app.state.agent.query(payload.question)


@app.post("/api/v1/agent/feedback", status_code=202)
def feedback(payload: FeedbackRequest) -> dict[str, Any]:
    return {"accepted": True, "request_id": payload.request_id}


@app.get("/api/v1/evaluation/summary")
def evaluation_summary() -> dict[str, str]:
    return {
        "status": "not_run",
        "message": "Run scripts/run_evaluation.py to generate measured results.",
    }
