"""Run unchanged, explicitly DEV-only D2 views under the new Oct12 code/metric."""
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
    "sql": ("nl2sql", "eval/artifacts/d2-final/review/sql-dev-v1.jsonl", 35, "7b4c18f203ce0d88f38837f0c788cbcff142b559dc70d3f281990a2d47175f35"),
    "robust": ("robust", "eval/artifacts/d2-final/review/robust-dev-v1.jsonl", 21, "1d6c7732b5196e7146e3b3f01fe4f9ccb24ad354c6b20776631192c605d213f7"),
    "rag": ("rag", "eval/artifacts/d2-final/review/rag-dev-view.jsonl", 21, "12b8cc7de87ea73bc60a2e9b7d527d0721956ef1bf4256ccf6a70331a7f57f63"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    directory = (ROOT / args.output).resolve()
    if not directory.is_relative_to(ROOT / "eval/artifacts/oct12") or directory.exists():
        raise SystemExit("Choose fresh Oct12 directory")
    directory.mkdir(parents=True)
    record = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "measurement": "Oct12 live DEV exploratory regression; original labels/status/results unchanged", "holdout_prediction_count": 0, "results": {}}
    for name, (suite, path, count, digest) in SPECS.items():
        source = ROOT / path
        if sha256(source.read_bytes()).hexdigest() != digest:
            raise SystemExit("Historical DEV view changed: " + path)
        items = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(items) != count or any(item["split"] != "dev" for item in items):
            raise SystemExit("Incorrect DEV view")
        target = directory / name
        command = [sys.executable, "-B", "-m", "eval.run_eval", "--suite", suite, "--dataset", path,
                   "--split", "dev", "--draft-gold", "--run-id", directory.name + "-" + name,
                   "--output", target.relative_to(ROOT).as_posix(), "--timeout", "240"]
        (directory / (name + "-command.json")).write_text(json.dumps({"command": command, "cwd": ".", "dataset_sha256": digest}, ensure_ascii=False, indent=2), encoding="utf-8")
        with (directory / (name + "-output.txt")).open("w", encoding="utf-8") as handle:
            process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding="utf-8", errors="replace")
            for line in process.stdout:
                handle.write(line); handle.flush(); print(name + " " + line.rstrip(), flush=True)
            exit_code = process.wait()
        report = json.loads((target / "report.json").read_text(encoding="utf-8")) if (target / "report.json").exists() else {}
        record["results"][name] = {"exit_code": exit_code, "report": target.relative_to(ROOT).as_posix() + "/report.json",
                                   "summary": {key: value for key, value in report.items() if key != "provenance"},
                                   "original_dev_sha_unchanged": sha256(source.read_bytes()).hexdigest() == digest}
        (directory / "report.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        if exit_code or report.get("status") != "COMPLETED":
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
