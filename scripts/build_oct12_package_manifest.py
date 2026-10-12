"""Prepare only the runtime delta and verified DEV evidence for the human ZIP."""
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"eval/reports/oct12/acceptance/delivery-manifest.json"

def main():
    safe=json.loads((ROOT/"eval/reports/oct12/manual-review/evidence-package-paths.json").read_text(encoding="utf-8"))
    include={"qa_agent","api","ui","notes/oct12","notes/references/oct12","eval/artifacts/oct12","eval/datasets/oct12","eval/reports/oct12",
             ".env.example","requirements.txt","docker-compose.yml","docker-compose.aw.yml","README-10月12日交付说明.md",
             "eval/__init__.py","eval/dataset.py","eval/metrics.py","eval/run_eval.py","eval/d2_rag_eval.py","eval/rag_run_eval.py","eval/rag_dataset.py","eval/rag_metrics.py",
             "data/aliases/aliases-oct12-approved.csv","data/docs/manifest.csv","data/catalog/chinook.yaml","data/catalog/adventureworks.yaml","data/rules/metric_definitions.json",
             "scripts/d2_command.py","scripts/d2_capture_api.py","scripts/restart_services.ps1","scripts/package_stage_delivery.py","scripts/run_d3_shared_regression.py",
             "scripts/build_value_index.py","scripts/build_schema_index.py"}
    include.update(safe["safe_dev_files"])
    include.update(path.relative_to(ROOT).as_posix() for path in (ROOT/"scripts").glob("*oct12*.py"))
    include.update(path.relative_to(ROOT).as_posix() for path in (ROOT/"scripts").glob("*oct12*.ps1"))
    include.update(path.relative_to(ROOT).as_posix() for path in (ROOT/"tests").glob("test_oct12*.py"))
    include.update(subprocess.check_output(["git","diff","--name-only","--","tests"],cwd=ROOT,text=True).splitlines())
    excluded=[f"eval/artifacts/oct12/runtime-snapshot-00{i}/source/eval/" for i in range(1,5)]
    excluded += ["eval/reports/oct12/acceptance/package-verification", "eval/reports/oct12/acceptance/extracted-links-verification", "eval/reports/oct12/acceptance/protected-and-links-verification"]
    banned_names={"build_gold.py","build_d2_sql_datasets.py","rag_build_gold.py","revise_d1_gold.py","build_d3_aw_dataset.py","build_d3_clarify_cases.py"}
    for name in include:
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or not path.exists():
            raise ValueError("Missing package source: "+name)
        if path.name in banned_names or any(part in {"protected_holdout","holdout","heldout"} for part in path.parts):
            raise ValueError("Forbidden developer attachment: "+name)
    record={"stage":"oct12-final","entry_document":"eval/reports/oct12/acceptance/10月12日任务逐项验收与证据.html",
            "include":sorted(include),"exclude_prefixes":excluded,
            "scope":"Portable human review and runtime delta package; all links use safe DEV files. Historical held builders/mixed datasets/offline eval snapshot bodies omitted. Full historical environment/test reproduction requires the existing repository; no database/models/secrets bundled."}
    OUT.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"explicit_include_entries":len(include),"held_predictions":0}))

if __name__=="__main__":
    main()
