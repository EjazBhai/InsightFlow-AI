# Evaluation

`evaluations/datasets/golden_questions.json` contains 50 version-controlled cases spanning aggregation, time series, rankings, returns, ambiguity, out-of-scope prompts, and adversarial requests. `scripts/run_evaluation.py` measures deterministic expected-status success and writes machine-readable results to `reports/evaluation_latest.json`. It deliberately does not pre-populate outcomes.
