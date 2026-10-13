from pathlib import Path

import pandas as pd

from insightflow.data.pipeline import prepare_data


def test_pipeline_retains_return_lines(tmp_path: Path):
    source = Path("data/fixtures/online_retail_fixture.csv")
    out = tmp_path / "transactions.parquet"
    report = prepare_data(source, out)
    data = pd.read_parquet(out)
    assert report.output_rows == 7
    assert report.cancellation_rows == 1
    assert data["quantity"].lt(0).sum() == 1
    assert data["customer_id"].isna().sum() == 1
