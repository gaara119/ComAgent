"""Read-only second review of six new DEV labels; no HTTP, model, held source."""
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings
from qa_agent.documents import load_documents, verify_document_hash
from qa_agent.fusion.planner import MetricDefinition, _definition_context, validate_fusion_sql
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql

settings = get_settings()
catalog = load_catalog(settings.catalog_path)
retrieval = json.loads((ROOT / "eval/artifacts/d4/fusion/source-retrieval-001/source-retrieval.json").read_text(encoding="utf-8"))
manual_retrieval = next(record for record in retrieval["records"] if record["doc_id"] == "project-metric-manual")
definition_chunk = next(chunk for chunk in manual_retrieval["chunks"] if chunk["chunk_id"] == "ca07b3c089c99383c97a3600")
quote = "本项目将客单价主口径写全为平均每张发票金额，表达式 AVG(invoice.total)，每张发票权重相同。"
documents = {doc["doc_id"]: doc for doc in load_documents(settings.rag_manifest_path)}
verified_sources = []
for name in ("project-metric-manual", "artist-iron-maiden", "artist-u2"):
    document = documents[name]
    verified_sources.append({"doc_id": name, "entity_ref": document["entity_ref"],
                             "actual_source_sha256": verify_document_hash(document)})
definition = MetricDefinition(metric_name="平均每张发票金额", aggregate="AVG", column="invoice.total",
    grain="invoice", unit="数据库金额单位", evidence_id=definition_chunk["evidence_id"], definition_quote=quote)
context, evidence = _definition_context(definition, manual_retrieval["chunks"], catalog, settings, documents["project-metric-manual"])
records = []
for number in range(1, 7):
    case_id = f"cross-{number:02d}"
    source = ROOT / f"eval/artifacts/d4/fusion/reference-only-001/{case_id}-reference.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    validate_fusion_sql(data["gold_sql"], catalog, {"kind": "sql_to_doc"} if number <= 3 else context)
    records.append({"id": case_id, "source": source.relative_to(ROOT).as_posix(),
                    "source_sha256": sha256(source.read_bytes()).hexdigest(),
                    "reference_plan_guard": "passed", "system_prediction": "not_run"})
probes = []
for number in (1, 2):
    label = json.loads((ROOT / f"eval/artifacts/d4/fusion/reference-only-001/cross-{number:02d}-reference.json").read_text(encoding="utf-8"))
    query = label["gold_sql"].replace("LIMIT 1", "LIMIT 2")
    result = execute_sql(query, settings.db_url, settings.statement_timeout_ms)
    unique_winner = len(result.rows) == 2 and Decimal(str(result.rows[0][2])) > Decimal(str(result.rows[1][2]))
    probes.append({"purpose": f"cross-{number:02d}: verify unique winner in current snapshot", "sql": query,
                   "rows": result.rows, "columns": result.columns, "unique_winner": unique_winner})
for case_id, year, country in (("cross-04", 2024, "USA"), ("cross-05", 2023, "Canada")):
    query = ("SELECT COUNT(*) AS invoice_count,COUNT(DISTINCT i.customer_id) AS buying_customers,"
             "SUM(i.total) AS total_amount,AVG(i.total) AS average_invoice_amount "
             "FROM public.invoice i JOIN public.customer c ON c.customer_id=i.customer_id "
             f"WHERE c.country='{country}' AND i.invoice_date>=DATE '{year}-01-01' "
             f"AND i.invoice_date<DATE '{year+1}-01-01'")
    result = execute_sql(query, settings.db_url, settings.statement_timeout_ms)
    count, customers, amount, avg = result.rows[0]
    expected = Decimal(str(avg))
    recomputed = (Decimal(str(amount)) / int(count)).quantize(Decimal(1).scaleb(expected.as_tuple().exponent))
    probes.append({"purpose": case_id + ": verify per-invoice equal weight", "sql": query,
        "columns": result.columns, "rows": result.rows, "independent_sum_div_count": str(recomputed),
        "average_matches": recomputed == expected,
        "different_customer_grain_amount": str(Decimal(str(amount)) / int(customers))})
payload = {"command": [sys.executable, *sys.argv], "sources": verified_sources, "definition_quote": quote,
           "definition_chunk": definition_chunk["chunk_id"], "reference_checks": records, "readonly_probes": probes,
           "model_calls": 0, "http_questions": 0, "held_predictions": 0,
           "human_review_status": "pending_human_review", "production_changes": False,
           "method": "Second source-and-query check; handcrafted definition guard input, not model extraction/prediction"}
target = Path(__file__).with_name("material-checks.json")
if target.exists():
    raise ValueError("Preserve prior verification")
target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps({"reference_guards": len(records), "readonly_probes": probes, "model_calls": 0}, ensure_ascii=False, default=str))
