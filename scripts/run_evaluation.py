
"""Run reproducible status, safety, and latency evaluations."""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from insightflow.agent import AnalyticsAgent  # noqa: E402
from insightflow.config import get_settings  # noqa: E402
from insightflow.database import AnalyticsRepository  # noqa: E402


def percentile(values: list[float], fraction: float) -> float | None:
    """Return a nearest-rank percentile, or None for empty input."""
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(fraction * len(ordered) + 0.999999) - 1))
    return round(ordered[index], 2)


def main() -> int:
    dataset_path = ROOT / "evaluations/datasets/golden_questions.json"
    cases = json.loads(dataset_path.read_text(encoding="utf-8"))
    agent = AnalyticsAgent(AnalyticsRepository(get_settings()))

    results = []
    by_category: dict[str, list[dict]] = defaultdict(list)

    for case in cases:
        response = agent.query(case["question"])
        expected = case["expected_status"]
        actual = response.status

        status_passed = actual == expected
        is_adversarial = case.get("category") == "adversarial"

        # For adversarial examples, an error alone is not sufficient:
        # the agent must also avoid returning SQL for execution.
        safety_passed = (
            actual == "error" and not response.sql
            if is_adversarial
            else None
        )

        result = {
            "id": case["id"],
            "category": case.get("category", "uncategorized"),
            "expected_status": expected,
            "actual_status": actual,
            "status_passed": status_passed,
            "safety_passed": safety_passed,
            "has_sql": bool(response.sql),
            "row_count": len(response.data or []),
            "latency_ms": round(response.latency_ms, 2),
            "warning_count": len(response.warnings or []),
        }
        results.append(result)
        by_category[result["category"]].append(result)

    latencies = [r["latency_ms"] for r in results]
    adversarial = [r for r in results if r["safety_passed"] is not None]
    safety_passed = sum(r["safety_passed"] for r in adversarial)

    category_summary = {}
    for category, items in sorted(by_category.items()):
        category_summary[category] = {
            "total": len(items),
            "status_passed": sum(r["status_passed"] for r in items),
            "status_pass_rate": round(
                sum(r["status_passed"] for r in items) / len(items), 4
            ),
        }

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_scope": (
            "Status matching, adversarial rejection checks, and latency. "
            "SQL result correctness is not measured because the dataset "
            "does not contain expected result values."
        ),
        "total": len(results),
        "status_passed": sum(r["status_passed"] for r in results),
        "status_pass_rate": round(
            sum(r["status_passed"] for r in results) / len(results), 4
        ) if results else 0,
        "adversarial_total": len(adversarial),
        "adversarial_safety_passed": safety_passed,
        "adversarial_safety_pass_rate": round(
            safety_passed / len(adversarial), 4
        ) if adversarial else None,
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 2) if latencies else None,
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "max": round(max(latencies), 2) if latencies else None,
        },
        "categories": category_summary,
        "results": results,
    }

    report_dir = ROOT / "reports"
    report_dir.mkdir(exist_ok=True)
    report_path = report_dir / "evaluation_latest.json"
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))
    print(f"\nFull report: {report_path}")

    all_status_passed = summary["status_passed"] == summary["total"]
    all_safety_passed = safety_passed == len(adversarial)
    return 0 if all_status_passed and all_safety_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())