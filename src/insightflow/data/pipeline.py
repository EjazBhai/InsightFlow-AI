"""Deterministic UCI Online Retail ingestion with documented quality decisions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"}
PIPELINE_VERSION = "1.0"


@dataclass(frozen=True)
class QualityReport:
    source: str
    processed_at: str
    input_rows: int
    output_rows: int
    duplicates_removed: int
    invalid_rows_rejected: int
    cancellation_rows: int
    missing_customer_ids: int
    pipeline_version: str = PIPELINE_VERSION

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def prepare_data(source: Path, output: Path) -> QualityReport:
    """Clean input without suppressing negative quantities or cancellation invoices."""
    frame = pd.read_csv(source, encoding="latin1")
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    original_count = len(frame)
    frame["InvoiceNo"] = frame["InvoiceNo"].astype("string").str.strip()
    frame["StockCode"] = frame["StockCode"].astype("string").str.strip()
    frame["InvoiceDate"] = pd.to_datetime(frame["InvoiceDate"], errors="coerce")
    frame["Quantity"] = pd.to_numeric(frame["Quantity"], errors="coerce")
    frame["UnitPrice"] = pd.to_numeric(frame["UnitPrice"], errors="coerce")
    invalid = (
        frame["InvoiceNo"].isna() | (frame["InvoiceNo"] == "") | frame["InvoiceDate"].isna()
        | frame["Quantity"].isna() | frame["UnitPrice"].isna() | (frame["UnitPrice"] < 0)
    )
    rejected = int(invalid.sum())
    frame = frame.loc[~invalid].copy()
    before_dedupe = len(frame)
    frame = frame.drop_duplicates()
    frame["is_cancellation"] = frame["InvoiceNo"].str.startswith("C", na=False) | (frame["Quantity"] < 0)
    frame["revenue"] = frame["Quantity"] * frame["UnitPrice"]
    frame = frame.rename(columns={
        "InvoiceNo": "invoice_no", "StockCode": "stock_code", "Description": "description",
        "Quantity": "quantity", "InvoiceDate": "invoice_date", "UnitPrice": "unit_price",
        "CustomerID": "customer_id", "Country": "country",
    })
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    return QualityReport(
        source=str(source), processed_at=datetime.now(timezone.utc).isoformat(), input_rows=original_count,
        output_rows=len(frame), duplicates_removed=before_dedupe - len(frame), invalid_rows_rejected=rejected,
        cancellation_rows=int(frame["is_cancellation"].sum()), missing_customer_ids=int(frame["CustomerID"].isna().sum()),
    )
