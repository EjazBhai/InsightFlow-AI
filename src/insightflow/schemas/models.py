from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    start_date: date | None = None
    end_date: date | None = None


class ChartSpec(BaseModel):
    kind: Literal["bar", "line", "scatter"]
    x: str
    y: str
    title: str


class AgentResponse(BaseModel):
    answer: str
    metric_definitions: list[str] = []
    sql: str | None = None
    data: list[dict[str, Any]] = []
    chart: ChartSpec | None = None
    warnings: list[str] = []
    latency_ms: float
    status: Literal["success", "clarification_needed", "error"]
    request_id: str


class FeedbackRequest(BaseModel):
    request_id: str
    helpful: bool
    comment: str | None = Field(default=None, max_length=1_000)
