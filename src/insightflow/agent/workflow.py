
"""Bounded LangGraph workflow for safe analytical SQL generation."""

from __future__ import annotations

import time
import uuid
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from insightflow.analytics.metrics import METRIC_DEFINITIONS
from insightflow.database.repository import AnalyticsRepository
from insightflow.llm.providers import ProviderError, generate_sql
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
    attempts: int
    correction: str


def _unsafe_request(question: str) -> bool:
    """Reject clear mutation or system-access requests, not incidental keywords."""
    import re

    patterns = (
        r"^\s*(?:please\s+)?(?:drop|delete|update|insert|create|alter|truncate)\b",
        r"^\s*(?:please\s+)?(?:attach|detach|install|load|copy)\b",
        r"\bread_(?:csv|parquet|json)\s*\(",
        r"\bpragma\b",
        r"\bwrite\s+(?:a\s+)?file\b",
        r"\bread\s+(?:a\s+)?(?:csv|parquet|json)\s+"
        r"(?:file|from|on|at|in)\b",
        r"\b(?:my\s+)?(?:desktop|downloads|documents)\b",
        r"\b(?:local|filesystem|file\s+system)\s+"
        r"(?:file|path|directory|folder)\b",
        r"\bexecute\s+(?:a\s+)?shell\b",
    )
    return any(re.search(pattern, question, re.IGNORECASE) for pattern in patterns)

def _mock_plan(question: str) -> dict[str, Any]:
    """Preserve deterministic planning for tests and the no-API demo."""
    if "country" in question:
        return {
            "sql": (
                "SELECT country, SUM(revenue) AS net_sales FROM transactions "
                "GROUP BY country ORDER BY net_sales DESC"
            ),
            "definitions": [METRIC_DEFINITIONS["net_sales"]],
            "chart": ChartSpec(
                kind="bar", x="country", y="net_sales", title="Net sales by country"
            ),
        }
    if "product" in question or "stock" in question:
        return {
            "sql": (
                "SELECT description, SUM(revenue) AS net_sales, "
                "SUM(quantity) AS units FROM transactions "
                "GROUP BY description ORDER BY net_sales DESC"
            ),
            "definitions": [METRIC_DEFINITIONS["net_sales"]],
            "chart": ChartSpec(
                kind="bar", x="description", y="net_sales", title="Product revenue"
            ),
        }
    if any(word in question for word in ("monthly", "trend", "month")):
        return {
            "sql": (
                "SELECT date_trunc('month', invoice_date) AS month, "
                "SUM(revenue) AS net_sales FROM transactions "
                "GROUP BY month ORDER BY month"
            ),
            "definitions": [METRIC_DEFINITIONS["net_sales"]],
            "chart": ChartSpec(
                kind="line", x="month", y="net_sales", title="Monthly net sales"
            ),
        }
    if "cancel" in question or "return" in question:
        return {
            "sql": (
                "SELECT COUNT(*) AS transaction_lines, "
                "SUM(CASE WHEN is_cancellation THEN 1 ELSE 0 END) "
                "AS cancellation_lines, "
                "100.0 * SUM(CASE WHEN is_cancellation THEN 1 ELSE 0 END) "
                "/ NULLIF(COUNT(*), 0) AS cancellation_pct FROM transactions"
            ),
            "definitions": [
                "Cancellation lines are invoices beginning with C or negative-quantity records."
            ],
        }
    if "customer" in question:
        return {
            "sql": (
                "SELECT customer_id, SUM(revenue) AS net_sales FROM transactions "
                "WHERE customer_id IS NOT NULL GROUP BY customer_id "
                "ORDER BY net_sales DESC"
            ),
            "definitions": [METRIC_DEFINITIONS["net_sales"]],
        }
    return {
        "sql": (
            "SELECT SUM(CASE WHEN quantity > 0 THEN revenue ELSE 0 END) AS gross_sales, "
            "SUM(revenue) AS net_sales, COUNT(DISTINCT invoice_no) AS invoices "
            "FROM transactions"
        ),
        "definitions": [
            METRIC_DEFINITIONS["gross_sales"],
            METRIC_DEFINITIONS["net_sales"],
        ],
    }


def _plan(state: AgentState, repository: AnalyticsRepository) -> AgentState:
    question = state["question"].strip()

    if _unsafe_request(question):
        return {
            "answer": "I can only run approved, read-only analytical queries.",
            "status": "error",
            "warnings": ["Unsafe or unsupported request rejected."],
        }

    attempts = state.get("attempts", 0) + 1
    settings = repository.settings

    try:
        if settings.model_provider == "mock":
            plan = _mock_plan(question)
        else:
            sql = generate_sql(
                question,
                settings,
                correction=state.get("correction"),
            )
            plan = {
                "sql": sql,
                "definitions": (
                    [METRIC_DEFINITIONS["net_sales"]]
                    if "sales" in question.lower() or "revenue" in question.lower()
                    else []
                ),
                "chart": None,
            }
    except ProviderError:
        return {
            "status": "error",
            "answer": "The configured language model is unavailable.",
            "warnings": ["Check provider configuration, connectivity, model access, and rate limits."],
            "attempts": attempts,
        }

    return {
        **plan,
        "attempts": attempts,
        "status": "pending",
        "answer": "",
        "warnings": [],
    }


def _execute(repository: AnalyticsRepository, state: AgentState) -> AgentState:
    if state.get("status") == "error":
        return state

    try:
        safe_sql = validate_readonly_sql(
            state["sql"],
            repository.settings.max_query_rows,
        )
        rows = repository.execute(safe_sql)
        return {
            "sql": safe_sql,
            "rows": rows,
            "status": "success",
            "correction": "",
        }
    except Exception as exc:
        attempts = state.get("attempts", 1)
        max_retries = repository.settings.max_llm_retries

        if (
            repository.settings.model_provider != "mock"
            and attempts <= max_retries
        ):
            reason = (
                "SQL validation failed."
                if isinstance(exc, SQLSafetyError)
                else "SQL execution failed."
            )
            return {
                "status": "retry",
                "correction": (
                    f"{reason} Generate a corrected query using only the "
                    "approved transactions table and approved columns. "
                    "Return one read-only SELECT query."
                ),
                "warnings": [
                    "Model output failed validation or execution; "
                    "the query was not accepted."
                ],
            }

        return {
            "answer": "The requested analysis could not be run safely.",
            "warnings": [
                f"Query failed validation or execution ({type(exc).__name__})."
            ],
            "status": "error",
        }
def _summarize(state: AgentState) -> AgentState:
    if state.get("status") != "success":
        return state

    rows = state.get("rows", [])
    if not rows:
        return {
            "answer": "No records matched this analysis.",
            "warnings": ["Empty result set."],
        }

    summary = ", ".join(f"{key}={value}" for key, value in rows[0].items())
    return {
        "answer": f"Analysis completed from the local retail dataset. First result: {summary}."
    }


def _after_execution(state: AgentState) -> str:
    return "plan" if state.get("status") == "retry" else "summarize"


class AnalyticsAgent:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository
        graph = StateGraph(AgentState)
        graph.add_node("plan", lambda state: _plan(state, self.repository))
        graph.add_node(
            "execute_readonly_sql",
            lambda state: _execute(self.repository, state),
        )
        graph.add_node("summarize", _summarize)
        graph.add_edge(START, "plan")
        graph.add_edge("plan", "execute_readonly_sql")
        graph.add_conditional_edges(
            "execute_readonly_sql",
            _after_execution,
            {"plan": "plan", "summarize": "summarize"},
        )
        graph.add_edge("summarize", END)
        self.graph = graph.compile()

    def query(self, question: str) -> AgentResponse:
        started = time.perf_counter()
        result = self.graph.invoke({"question": question, "warnings": []})
        return AgentResponse(
            answer=result.get("answer", "Analysis could not be completed."),
            metric_definitions=result.get("definitions", []),
            sql=result.get("sql"),
            data=result.get("rows", []),
            chart=result.get("chart"),
            warnings=result.get("warnings", []),
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            status=result.get("status", "error"),
            request_id=str(uuid.uuid4()),
        )
