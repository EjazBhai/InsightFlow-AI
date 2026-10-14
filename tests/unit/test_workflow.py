
from pathlib import Path

import pytest

from insightflow.agent.workflow import AnalyticsAgent
from insightflow.config import Settings
from insightflow.data.pipeline import prepare_data
from insightflow.database import AnalyticsRepository
from insightflow.llm.providers import ProviderError


@pytest.fixture
def repository(tmp_path: Path) -> AnalyticsRepository:
    settings = Settings(
        database_path=tmp_path / "test.duckdb",
        data_dir=tmp_path,
        model_provider="groq",
        groq_api_key="test-key",
        model_name="test-model",
        max_llm_retries=2,
    )
    parquet = tmp_path / "data.parquet"
    prepare_data(Path("data/fixtures/online_retail_fixture.csv"), parquet)
    repo = AnalyticsRepository(settings)
    repo.initialize(parquet)
    return repo


def test_invalid_model_sql_is_corrected(
    repository: AnalyticsRepository,
    monkeypatch: pytest.MonkeyPatch,
):
    from insightflow.agent import workflow

    responses = iter(
        [
            "SELECT secret FROM transactions",
            "SELECT country, SUM(revenue) AS net_sales "
            "FROM transactions GROUP BY country",
        ]
    )
    corrections = []

    def fake_generate_sql(question, settings, correction=None):
        corrections.append(correction)
        return next(responses)

    monkeypatch.setattr(workflow, "generate_sql", fake_generate_sql)

    result = AnalyticsAgent(repository).query("Show sales by country")

    assert result.status == "success"
    assert len(corrections) == 2
    assert corrections[0] is None
    assert corrections[1]


def test_retry_count_is_bounded(
    repository: AnalyticsRepository,
    monkeypatch: pytest.MonkeyPatch,
):
    from insightflow.agent import workflow

    calls = []

    def always_invalid_sql(question, settings, correction=None):
        calls.append(correction)
        return "SELECT secret FROM transactions"

    monkeypatch.setattr(workflow, "generate_sql", always_invalid_sql)

    result = AnalyticsAgent(repository).query("Show sales by country")

    # One initial generation plus at most two correction generations.
    assert len(calls) == 3
    assert result.status == "error"


def test_provider_failure_returns_controlled_error(
    repository: AnalyticsRepository,
    monkeypatch: pytest.MonkeyPatch,
):
    from insightflow.agent import workflow

    def fail_provider(question, settings, correction=None):
        raise ProviderError("simulated provider failure")

    monkeypatch.setattr(workflow, "generate_sql", fail_provider)

    result = AnalyticsAgent(repository).query("Show sales by country")

    assert result.status == "error"
    assert "unavailable" in result.answer.lower()


def test_unsafe_request_does_not_call_provider(
    repository: AnalyticsRepository,
    monkeypatch: pytest.MonkeyPatch,
):
    from insightflow.agent import workflow

    def unexpected_provider_call(*args, **kwargs):
        pytest.fail("Provider must not be called for an unsafe request")

    monkeypatch.setattr(workflow, "generate_sql", unexpected_provider_call)

    result = AnalyticsAgent(repository).query("DROP TABLE transactions")

    assert result.status == "error"
def test_incidental_update_word_is_not_blocked(
    repository: AnalyticsRepository,
    monkeypatch: pytest.MonkeyPatch,
):
    from insightflow.agent import workflow

    def fake_generate_sql(question, settings, correction=None):
        return (
            "SELECT country, SUM(revenue) AS net_sales "
            "FROM transactions GROUP BY country"
        )

    monkeypatch.setattr(workflow, "generate_sql", fake_generate_sql)

    result = AnalyticsAgent(repository).query(
        "Show the update rate by country"
    )

    assert result.status == "success"