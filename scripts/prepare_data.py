import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from insightflow.config import get_settings
from insightflow.data.pipeline import prepare_data
from insightflow.database import AnalyticsRepository

settings = get_settings()
source = ROOT / "data" / "fixtures" / "online_retail_fixture.csv"
parquet = settings.data_dir / "processed" / "transactions.parquet"
report = prepare_data(source, parquet)
(settings.data_dir / "processed").mkdir(parents=True, exist_ok=True)
(settings.data_dir / "processed" / "quality_report.json").write_text(json.dumps(report.to_dict(), indent=2))
AnalyticsRepository(settings).initialize(parquet)
print(f"Prepared {report.output_rows} rows from {source}")
