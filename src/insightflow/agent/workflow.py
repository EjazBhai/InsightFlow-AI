"""A bounded LangGraph workflow with deterministic local planning for the demo mode."""
from __future__ import annotations

import time
import uuid
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from insightflow.analytics.metrics import METRIC_DEFINITIONS
from insightflow.database.repository import AnalyticsRepository
from insightflow.schemas import AgentResponse, ChartSpec
from insightflow.security import SQLSafetyError, validate_readonly_sql


class AgentState(TypedDict, total=False):
    question: str
    sql: str
    rows: list[dict[str, Any]]
    answer: str
    definitions: list[str]
    chart: ChartSpec | None
    warnings: list[str]
    status: str


def _plan(state: AgentState) -> AgentState:
    question = state["question"].lower()
    if any(word in question for word in ("drop ", "delete ", "update ", "insert ", "attach ")):
        return {"answer": "I can only run approved, read-only analytical queries.", "status": "error", "warnings": ["Unsafe request rejected."]}
    if "country" in question:
        return {"sql": "SELECT country, SUM(revenue) AS net_sales FROM transactions GROUP BY country ORDER BY net_sales DESC", "definitions": [METRIC_DEFINITIONS["net_sales"]], "chart": ChartSpec(kind="bar", x="country", y="net_sales", title="Net sales by country")}
    if "product" in question or "stock" in question:
        return {"sql": "SELECT description, SUM(revenue) AS net_sales, SUM(quantity) AS units FROM transactions GROUP BY description ORDER BY net_sales DESC", "definitions": [METRIC_DEFINITIONS["net_sales"]], "chart": ChartSpec(kind="bar", x="description", y="net_sales", title="Product revenue")}
    if any(word in question for word in ("monthly", "trend", "month")):
        return {"sql": "SELECT date_trunc('month', invoice_date) AS month, SUM(revenue) AS net_sales FROM transactions GROUP BY month ORDER BY month", "definitions": [METRIC_DEFINITIONS["net_sales"]], "chart": ChartSpec(kind="line", x="month", y="net_sales", title="Monthly net sales")}
    if "cancel" in question or "return" in question:
        return {"sql": "SELECT COUNT(*) AS transaction_lines, SUM(CASE WHEN is_cancellation THEN 1 ELSE 0 END) AS cancellation_lines, 100.0 * SUM(CASE WHEN is_cancellation THEN 1 ELSE 0 END) / COUNT(*) AS cancellation_pct FROM transactions", "definitions": ["Cancellation lines are invoices beginning with C or negative-quantity records."]}
    if "customer" in question:
        return {"sql": "SELECT customer_id, SUM(revenue) AS net_sales FROM transactions WHERE customer_id IS NOT NULL GROUP BY customer_id ORDER BY net_sales DESC", "definitions": [METRIC_DEFINITIONS["net_sales"]]}
    return {"sql": "SELECT SUM(CASE WHEN quantity > 0 THEN revenue ELSE 0 END) AS gross_sales, SUM(revenue) AS net_sales, COUNT(DISTINCT invoice_no) AS invoices FROM transactions", "definitions": [METRIC_DEFINITIONS["gross_sales"], METRIC_DEFINITIONS["net_sales"]]}


def _execute(repository: AnalyticsRepository, state: AgentState) -> AgentState:
    if state.get("status") == "error":
        return state
    try:
        safe_sql = validate_readonly_sql(state["sql"], repository.settings.max_query_rows)
        return {"sql": safe_sql, "rows": repository.execute(safe_sql), "status": "success"}
    except (SQLSafetyError, OSError) as exc:
        return {"answer": "The requested analysis could not be run safely.", "warnings": [str(exc)], "status": "error"}


def _summarize(state: AgentState) -> AgentState:
    if state.get("status") != "success":
        return state
    rows = state.get("rows", [])
    if not rows:
        return {"answer": "No records matched this analysis.", "warnings": ["Empty result set."]}
    first = rows[0]
    summary = ", ".join(f"{key}={value}" for key, value in first.items())
    return {"answer": f"Analysis completed from the local retail dataset. First result: {summary}."}


class AnalyticsAgent:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository
        graph = StateGraph(AgentState)
        graph.add_node("plan", _plan)
        graph.add_node("execute_readonly_sql", lambda state: _execute(self.repository, state))
        graph.add_node("summarize", _summarize)
        graph.add_edge(START, "plan")
        graph.add_edge("plan", "execute_readonly_sql")
        graph.add_edge("execute_readonly_sql", "summarize")
        graph.add_edge("summarize", END)
        self.graph = graph.compile()

    def query(self, question: str) -> AgentResponse:
        started = time.perf_counter()
        result = self.graph.invoke({"question": question, "warnings": []})
        return AgentResponse(
            answer=result.get("answer", "Analysis could not be completed."), metric_definitions=result.get("definitions", []),
            sql=result.get("sql"), data=result.get("rows", []), chart=result.get("chart"),
            warnings=result.get("warnings", []), latency_ms=round((time.perf_counter() - started) * 1000, 2),
            status=result.get("status", "error"), request_id=str(uuid.uuid4()),
        )
