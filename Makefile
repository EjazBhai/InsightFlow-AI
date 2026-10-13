.PHONY: prepare test evaluate lint run-api run-ui
prepare:
	python scripts/prepare_data.py
test:
	pytest -m "not performance" --cov=insightflow
evaluate:
	python scripts/run_evaluation.py
lint:
	ruff check .
run-api:
	uvicorn insightflow.api.app:app --reload
run-ui:
	streamlit run apps/streamlit_app/app.py
