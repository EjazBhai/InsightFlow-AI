from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration; secrets are always supplied through environment variables."""

    model_config = SettingsConfigDict(env_prefix="INSIGHTFLOW_", env_file=".env", extra="ignore")
    data_dir: Path = Path("data")
    database_path: Path = Path("data/insightflow.duckdb")
    model_provider: str = "mock"
    model_name: str = "configure-an-ollama-tool-model"
    max_query_rows: int = 500
    query_timeout_seconds: int = 10


def get_settings() -> Settings:
    return Settings()
