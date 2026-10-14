
"""LLM providers for SQL generation."""

from __future__ import annotations

import httpx
from groq import Groq

from insightflow.config import Settings


class ProviderError(RuntimeError):
    """Raised when an LLM provider cannot return a usable response."""


SYSTEM_PROMPT = """You generate DuckDB SQL for business analytics.
Return only one SQL query, without Markdown fences or explanation.
Only query the approved transactions table.
Use only these columns:
invoice_no, stock_code, description, quantity, invoice_date, unit_price,
customer_id, country, is_cancellation, revenue.
Only generate read-only SELECT queries.
Never use external files, extensions, ATTACH, PRAGMA, or system commands.
The application validates all SQL independently before execution."""


def generate_sql(
    question: str,
    settings: Settings,
    correction: str | None = None,
) -> str:
    """Generate SQL with the configured provider."""
    prompt = f"Business question: {question}"
    if correction:
        prompt += f"\nPrevious query failed validation or execution: {correction}"
        prompt += "\nProduce a corrected read-only query."

    if settings.model_provider == "mock":
        return (
            "SELECT country, SUM(revenue) AS net_sales "
            "FROM transactions GROUP BY country ORDER BY net_sales DESC"
            if "country" in question.lower()
            else "SELECT SUM(revenue) AS net_sales FROM transactions"
        )

    if settings.model_provider == "ollama":
        url = settings.ollama_base_url.rstrip("/") + "/api/generate"
        try:
            response = httpx.post(
                url,
                json={
                    "model": settings.model_name,
                    "system": SYSTEM_PROMPT,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            sql = response.json().get("response", "")
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError("Ollama request failed.") from exc

    elif settings.model_provider == "groq":
        if not settings.groq_api_key:
            raise ProviderError("Groq API key is not configured.")
        try:
            client = Groq(api_key=settings.groq_api_key)
            response = client.chat.completions.create(
                model=settings.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            sql = response.choices[0].message.content or ""
        except Exception as exc:
            raise ProviderError("Groq request failed.") from exc
    else:
        raise ProviderError("Unsupported model provider.")

    # Strip optional Markdown fences; SQL policy remains the security boundary.
    sql = sql.strip()
    if sql.startswith("```"):
        lines = sql.splitlines()
        sql = "\n".join(lines[1:-1]).strip()
    if not sql:
        raise ProviderError("The model returned an empty response.")
    return sql
