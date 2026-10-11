"""Actual D3 dense recall/Steiner evaluation on development cases only."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings
from qa_agent.rag.embeddings import get_embedder
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.schema_linker import SchemaLinker, complete_steiner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "eval/datasets/d3/aw_schema_link.dev.v2.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "eval/reports/d3-aw-schema-dev-v2")
    parser.add_argument("--index", type=Path, default=ROOT / "data/indexes/schema-aw-d3-v2")
    args = parser.parse_args()
    cases = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    if any(case["split"] != "dev" for case in cases):
        raise ValueError("This D3 development runner refuses a file containing any protected holdout case")
    if (args.output / "report.json").exists():
        raise ValueError("Choose a new output directory; original results are never overwritten")
    args.output.mkdir(parents=True, exist_ok=True)
    path = ROOT / "data/catalog/adventureworks.yaml"
    catalog = load_catalog(path)
    embedder = get_embedder(get_settings())
    linker = SchemaLinker(catalog, args.index, embedder.encode, catalog_path=path)
    results = []
    with (args.output / "responses.jsonl").open("w", encoding="utf-8") as stream:
        for case in cases:
            started = perf_counter()
            bundle = linker.link(case["question"])
            selected, gold = set(bundle.selected_tables), set(case["gold_tables"])
            record = {"id":case["id"],"question":case["question"], "split":"dev", "gold_tables":case["gold_tables"],
                      "bundle":bundle.as_dict(), "recall":len(selected & gold)/len(gold),
                      "precision":len(selected & gold)/len(selected), "all_gold_recalled":gold <= selected,
                      "missing_gold":sorted(gold-selected), "candidate_count":len(selected),
                      "latency_ms":round((perf_counter()-started)*1000), "system_sql_prediction":"not part of this module evaluation"}
            results.append(record)
            stream.write(json.dumps(record,ensure_ascii=False)+"\n")
    nodes, paths, components = complete_steiner(linker.graph, ["sales.salesorderdetail","production.productcategory"])
    bridge = {"terminals":["sales.salesorderdetail","production.productcategory"],"actual_fk_completed_tables":sorted(nodes), "join_paths":paths,"components":components}
    (args.output / "actual-steiner-bridge.json").write_text(json.dumps(bridge,ensure_ascii=False,indent=2),encoding="utf-8")
    summary = {"status":"ACTUALLY_RUN_MODULE_DEV", "label_status":"pending_human_review", "created_at":datetime.now(timezone.utc).isoformat(),
               "case_count":len(results), "holdout_predictions":0, "configured_model":"local verified BGE-M3 ONNX int8",
               "dataset":str(args.dataset.relative_to(ROOT)), "dataset_sha256":hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
               "catalog_sha256":hashlib.sha256(path.read_bytes()).hexdigest(), "index":str(args.index.relative_to(ROOT)),
               "mean_table_recall":sum(r["recall"] for r in results)/len(results),
               "mean_table_precision":sum(r["precision"] for r in results)/len(results),
               "all_gold_recalled_cases":sum(r["all_gold_recalled"] for r in results),
               "average_candidate_table_count":sum(r["candidate_count"] for r in results)/len(results),
               "average_latency_ms":sum(r["latency_ms"] for r in results)/len(results),
               "missing_gold_cases":[{"id":r["id"],"missing_gold":r["missing_gold"]} for r in results if r["missing_gold"]],
               "stage_scope":"D3 dual dense + column votes + value hints/RRF + Steiner; D4 pruning/ablation intentionally absent"}
    (args.output / "report.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    (args.output / "report.md").write_text("# D3 AW schema 开发集实际模块评测\n\n"+"```json\n"+json.dumps(summary,ensure_ascii=False,indent=2)+"\n```\n\n逐题候选、入选理由与缺失表在 responses.jsonl。该报告不计算NL2SQL EX，也不代替人工gold审核。\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
