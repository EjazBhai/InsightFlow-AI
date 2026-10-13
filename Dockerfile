FROM python:3.12-slim
WORKDIR /app
RUN useradd --create-home appuser
COPY src ./src
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .
COPY apps ./apps
COPY data/fixtures ./data/fixtures
COPY scripts ./scripts
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"
CMD ["uvicorn", "insightflow.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
