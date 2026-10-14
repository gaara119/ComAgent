"""Local-only D4 A readiness evidence; no DB connection or model inference."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))
import sqlglot
from sqlglot import exp
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from scripts.d4_sql_scale import load_cases

settings = get_settings()
source = ROOT / "eval/datasets/d3/aw_schema_link.dev.v2.jsonl"
aw = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
assert len(aw) == 21 and all(case["split"] == "dev" for case in aw)
catalog = load_catalog(settings.aw_catalog_path)
assert len(catalog.tables) == 68
assert sum(len(table.columns) for table in catalog.tables) == 456
cases, sql_sources = load_cases()
categories = {"expanded_invoice_line": [], "expanded_invoice": [], "nonexpanded_dimension_control": []}
for case in cases:
    tables = {table.name for table in sqlglot.parse_one(case["gold_sql"], read="postgres").find_all(exp.Table)}
    group = "expanded_invoice_line" if "invoice_line" in tables else (
        "expanded_invoice" if "invoice" in tables else "nonexpanded_dimension_control")
    categories[group].append(case["id"])
assert {key: len(value) for key, value in categories.items()} == {
    "expanded_invoice_line": 3, "expanded_invoice": 7, "nonexpanded_dimension_control": 10}
manifest_path = ROOT / "eval/artifacts/d4/sql-scale-data-001/manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
assert manifest["original_public_unchanged"]
assert {scale["line_count"] for scale in manifest["scales"]} == {10000, 100000}
assert all(scale["orphan_lines"] == 0 for scale in manifest["scales"])
assert all(Path(ROOT / scale["catalog"]).is_file() for scale in manifest["scales"])
files = [source, settings.aw_catalog_path, manifest_path, *sql_sources,
         ROOT / "scripts/d4_bench_utils.py", ROOT / "scripts/d4_aw_ablation.py",
         ROOT / "scripts/d4_sql_scale.py", ROOT / "eval/metrics.py"]
result = {
    "at_utc": datetime.now(timezone.utc).isoformat(),
    "status": "LOCAL_READINESS_VERIFIED_NOT_MODEL_BENCHMARK",
    "external_requests": 0, "model_calls": 0, "database_connections": 0,
    "held_content_read": False, "holdout_predictions": 0,
    "aw": {"catalog_tables": 68, "catalog_columns": 456, "dev_cases": len(aw),
           "expected_predictions": 42, "completed_predictions": 0,
           "same_questions_two_arms": True, "arms": ["full", "subgraph"]},
    "sql": {"dev_cases": len(cases), "scales": [2240, 10000, 100000], "repetitions": 3,
            "expected_predictions": 180, "completed_predictions": 0,
            "scope_counts": {key: len(value) for key, value in categories.items()},
            "question_groups": categories, "manifest_status": manifest["status"],
            "original_public_unchanged_at_copy_verification": manifest["original_public_unchanged"]},
    "current_blocker": "Docker engine unavailable; authorization already received; do not send model requests until DB readiness and exclusive-start confirmation.",
    "source_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in files},
    "claims_limit": "Past copy/gold evidence is retained; this preflight does not revalidate current engine availability, SQL results or model accuracy/latency."
}
target = ROOT / "eval/artifacts/d4/a-readiness-001/local-preflight.json"
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
