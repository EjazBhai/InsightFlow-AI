from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb

from insightflow.config import Settings


class AnalyticsRepository:
    """Small analytical data gateway; callers never get direct database connections."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def initialize(self, parquet_path: Path) -> None:
        self.settings.database_path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(self.settings.database_path)) as con:
            con.execute(
                "CREATE OR REPLACE TABLE transactions AS SELECT * FROM read_parquet(?)",
                [str(parquet_path)],
            )

    def execute(self, sql: str, parameters: list[Any] | None = None) -> list[dict[str, Any]]:
        with duckdb.connect(str(self.settings.database_path), read_only=True) as con:
            result = con.execute(sql, parameters or [])
            columns = [entry[0] for entry in result.description]
            return [
                dict(zip(columns, row, strict=True))
                for row in result.fetchmany(self.settings.max_query_rows)
            ]

    def summary(self) -> dict[str, Any]:
        sql = """SELECT coalesce(sum(CASE WHEN quantity > 0 THEN revenue ELSE 0 END),0) gross_sales,
            coalesce(sum(revenue),0) net_sales, count(DISTINCT invoice_no) invoices,
            count(DISTINCT stock_code) products, count(DISTINCT customer_id) customers,
            coalesce(sum(revenue) / nullif(count(DISTINCT invoice_no),0),0) average_order_value,
            sum(CASE WHEN is_cancellation THEN 1 ELSE 0 END) cancellation_lines FROM transactions"""
        return self.execute(sql)[0]

    def quality(self) -> dict[str, Any]:
        report_path = self.settings.data_dir / "processed" / "quality_report.json"
        return (
            json.loads(report_path.read_text())
            if report_path.exists()
            else {"status": "not_ingested"}
        )
