"""Execute reproducible golden-set status checks against the deterministic agent."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from insightflow.agent import AnalyticsAgent  # noqa: E402
from insightflow.config import get_settings  # noqa: E402
from insightflow.database import AnalyticsRepository  # noqa: E402

cases = json.loads((ROOT / "evaluations/datasets/golden_questions.json").read_text())
agent = AnalyticsAgent(AnalyticsRepository(get_settings()))
results = []
for case in cases:
    response = agent.query(case["question"])
    results.append(
        {
            "id": case["id"],
            "expected": case["expected_status"],
            "actual": response.status,
            "passed": response.status == case["expected_status"],
            "latency_ms": response.latency_ms,
        }
    )
summary = {
    "run_at": datetime.now(timezone.utc).isoformat(),
    "total": len(results),
    "passed": sum(r["passed"] for r in results),
    "results": results,
}
(ROOT / "reports").mkdir(exist_ok=True)
(ROOT / "reports/evaluation_latest.json").write_text(json.dumps(summary, indent=2))
print(json.dumps({k: summary[k] for k in ("run_at", "total", "passed")}, indent=2))
raise SystemExit(0 if summary["passed"] == summary["total"] else 1)
