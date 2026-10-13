from pathlib import Path

from fastapi.testclient import TestClient

from insightflow.api.app import app
from insightflow.config import get_settings
from insightflow.data.pipeline import prepare_data
from insightflow.database import AnalyticsRepository


def test_health_and_agent(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("INSIGHTFLOW_DATABASE_PATH", str(tmp_path / "test.duckdb"))
    monkeypatch.setenv("INSIGHTFLOW_DATA_DIR", str(tmp_path))
    settings = get_settings()
    parquet = tmp_path / "data.parquet"
    prepare_data(Path("data/fixtures/online_retail_fixture.csv"), parquet)
    AnalyticsRepository(settings).initialize(parquet)
    with TestClient(app) as client:
        assert client.get("/health/ready").status_code == 200
        response = client.post("/api/v1/agent/query", json={"question": "sales by country"})
        assert response.status_code == 200
        assert response.json()["status"] == "success"
