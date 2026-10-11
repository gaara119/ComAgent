"""Validate D2 labels, source paths and preserved holdout; never call the model."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eval.dataset import load_dataset
from eval.d2_rag_eval import load_d2_rag


def audit(datasets_dir: Path, manifest: Path) -> dict:
    errors=[]
    sql=load_dataset(datasets_dir/"nl2sql_chinook_d2.jsonl")
    robust=load_dataset(datasets_dir/"robust.jsonl")
    rag=load_d2_rag(datasets_dir/"rag_single.jsonl")
    checks={}
    for name,rows,counts in [("nl2sql",sql,{"dev":35,"holdout":15}),
                             ("robust",robust,{"dev":21,"holdout":9}),
                             ("rag",rag,{"dev":21,"holdout":9})]:
        checks[name+"_counts"]={"total":len(rows),"split":dict(Counter(r["split"] for r in rows))}
        if Counter(r["split"] for r in rows)!=counts:
            errors.append(name+": wrong split counts")
    base={r["id"]:r for r in sql}
    for row in robust:
        original=base.get(row.get("base_id"))
        if not original or row["split"]!=original["split"] or row["family_id"]!=original["family_id"]:
            errors.append(row["id"]+": base group mismatch")
        elif any(row[key]!=original[key] for key in ("gold_sql","gold_result","gold_columns","ordered")):
            errors.append(row["id"]+": variant changed business gold")
    if Counter(r["variant_type"] for r in robust)!={k:5 for k in ("typo","alias","pinyin","mixed_language","colloquial","extra_words")}:
        errors.append("robust: six perturbation categories must each contain five")
    baseline_sql=load_dataset(ROOT/"eval/datasets/nl2sql_chinook_d1_acceptance.jsonl")
    baseline_rag=load_d2_rag(ROOT/"eval/datasets/rag_ohr.jsonl")
    for previous,current in [(baseline_sql,sql),(baseline_rag,rag)]:
        lookup={r["id"]:r for r in current}
        for row in previous:
            new=lookup.get(row["id"])
            if not new or any(new.get(k)!=v for k,v in row.items() if k in
                              {"question","split","gold_sql","gold_result","answer","reference_text","physical_pages","doc_id"}):
                errors.append(row["id"]+": original D1 label changed")
    for row in sql+robust+rag:
        if row["split"]=="holdout" and row.get("exposure_history",{}).get("d1_model_exposed"):
            errors.append(row["id"]+": exposed question assigned to holdout")
    if sum(not r.get("answerable",True) for r in rag)!=3:
        errors.append("RAG must contain exactly three insufficient-evidence questions within 30")
    if sum(r["id"] in {x["id"] for x in baseline_rag} for r in rag)!=20:
        errors.append("RAG does not preserve 20 original OHR questions")
    with manifest.open(encoding="utf-8-sig",newline="") as stream:
        documents=list(csv.DictReader(stream))
    if len(documents)!=13 or len({r["doc_id"] for r in documents})!=13:
        errors.append("Manifest must enumerate 13 distinct materials")
    document_checks=[]
    for row in documents:
        relative=row.get("relative_path") or row.get("path","")
        path=(ROOT/relative).resolve()
        exists=path.is_relative_to(ROOT) and path.is_file() and not Path(relative).is_absolute()
        actual=hashlib.sha256(path.read_bytes()).hexdigest() if exists else None
        expected=row.get("content_sha256") or row.get("content_hash")
        valid=exists and actual==expected
        document_checks.append({"doc_id":row["doc_id"],"format":row.get("format"),"exists":exists,"sha256_matches":valid})
        if not valid:
            errors.append(row["doc_id"]+": missing file or source hash mismatch")
        if not row.get("source_document_id") or not row.get("license_note"):
            errors.append(row["doc_id"]+": missing source identity or license note")
    ids={r["doc_id"] for r in documents}
    for row in rag:
        if row["doc_id"] not in ids:
            errors.append(row["id"]+": document absent from manifest")
    holdout_ids={r["id"] for r in sql+robust+rag if r["split"]=="holdout"}
    detected=[]
    for path in (ROOT/"eval/artifacts/d2").rglob("responses.jsonl"):
        for line in path.read_text(encoding="utf8").splitlines():
            if line.strip():
                record=json.loads(line)
                if record.get("id") in holdout_ids:
                    detected.append({"id":record["id"],"path":path.relative_to(ROOT).as_posix()})
    if detected:
        errors.append("Holdout prediction records found before D5")
    return {"created_at_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS" if not errors else "FAIL",
            "checks":checks,"documents":document_checks,"document_count":len(documents),
            "holdout_prediction_records":detected,"errors":errors,
            "model_calls":0,"human_review":"not performed by this structure audit",
            "datasets_sha256":{name:hashlib.sha256((datasets_dir/name).read_bytes()).hexdigest()
                                for name in ("nl2sql_chinook_d2.jsonl","robust.jsonl","rag_single.jsonl")}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets-dir",type=Path,default=ROOT/"eval/datasets")
    parser.add_argument("--manifest",type=Path,default=ROOT/"data/docs/manifest.csv")
    parser.add_argument("--output",type=Path,default=ROOT/"eval/artifacts/d2/input-audit.json")
    args=parser.parse_args()
    result=audit(args.datasets_dir,args.manifest)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"status":result["status"],"checks":result["checks"],"document_count":result["document_count"],"errors":result["errors"]},ensure_ascii=False))
    return 0 if result["status"]=="PASS" else 1


if __name__=="__main__": raise SystemExit(main())
