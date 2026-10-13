"""Deterministic SQL boundary for model-generated analytical queries."""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {"transactions"}
ALLOWED_COLUMNS = {
    "invoice_no",
    "stock_code",
    "description",
    "quantity",
    "invoice_date",
    "unit_price",
    "customer_id",
    "country",
    "is_cancellation",
    "revenue",
}
FORBIDDEN = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Command,
    exp.Copy,
)


class SQLSafetyError(ValueError):
    pass


def validate_readonly_sql(sql: str, max_rows: int = 500) -> str:
    """Return normalized SELECT SQL with enforced limit or raise SQLSafetyError."""
    if not sql or ";" in sql.strip().rstrip(";"):
        raise SQLSafetyError("Exactly one SQL statement is allowed.")
    if re.search(
        r"\b(read_csv|read_parquet|read_json|httpfs|pragma|attach|install|load)\b", sql, re.I
    ):
        raise SQLSafetyError("External file, extension, and configuration access are prohibited.")
    try:
        parsed = sqlglot.parse_one(sql, read="duckdb")
    except sqlglot.errors.ParseError as exc:
        raise SQLSafetyError("SQL could not be parsed.") from exc
    if not isinstance(parsed, (exp.Select, exp.Union, exp.Subquery)) or parsed.find(*FORBIDDEN):
        raise SQLSafetyError("Only read-only SELECT queries are allowed.")
    for table in parsed.find_all(exp.Table):
        if table.name.lower() not in ALLOWED_TABLES:
            raise SQLSafetyError(f"Table '{table.name}' is not approved.")
    aliases = {alias.alias.lower() for alias in parsed.find_all(exp.Alias) if alias.alias}
    for column in parsed.find_all(exp.Column):
        if (
            column.name != "*"
            and column.name.lower() not in ALLOWED_COLUMNS
            and column.name.lower() not in aliases
        ):
            raise SQLSafetyError(f"Column '{column.name}' is not approved.")
    limit = parsed.args.get("limit")
    if limit is None:
        parsed = parsed.limit(max_rows)
    elif int(limit.expression.name) > max_rows:
        parsed = parsed.limit(max_rows)
    return parsed.sql(dialect="duckdb")
