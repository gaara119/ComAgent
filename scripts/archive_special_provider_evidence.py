"""Supplement an observer-only capture gap without changing frozen run evidence.

The runtime runner accepts 36-character UUID file names; JsonLLM actually writes
UUID.hex (32 characters). Both are valid UUID forms. This offline tool copies only
trace-matching, server-referenced captures under explicit project-local roots.
Original scores, checkpoints and provider-evidence.json are never rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "eval/experiments/after_d2_01_03/runtime_eval"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def new_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def verified_capture(reference: str, trace_id: str) -> Path:
    source = (ROOT / reference).resolve()
    allowed = (EXPERIMENT / "provider-captures", ROOT / ".runtime/provider-captures")
    if not any(source.is_relative_to(base.resolve()) for base in allowed):
        raise ValueError("capture outside explicit roots")
    if not re.fullmatch(r"(?:[0-9a-fA-F]{32}|[0-9a-fA-F-]{36})\.json", source.name):
        raise ValueError("invalid UUID capture filename")
    UUID(source.stem)
    value = json.loads(source.read_text(encoding="utf-8"))
    if not trace_id or value.get("trace_id") != trace_id:
        raise ValueError("capture trace_id mismatch")
    if not isinstance(value.get("request"), dict):
        raise ValueError("capture has no original request")
    return source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_dir, output = args.run_dir.resolve(), args.output.resolve()
    if not run_dir.is_relative_to(EXPERIMENT / "runs") or not output.is_relative_to(EXPERIMENT):
        parser.error("explicit experiment run/output paths required")
    if output.exists():
        parser.error("new output required; historical evidence cannot be overwritten")
    if not (run_dir / "run-manifest.json").is_file():
        parser.error("actual run manifest required")
    protected = [run_dir / "run-manifest.json", *sorted((run_dir / "cases").glob("*/checkpoint.json")),
                 *sorted((run_dir / "cases").glob("*/turns/*/provider-evidence.json"))]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in protected}
    records, failures = [], []
    for checkpoint in sorted((run_dir / "cases").glob("*/checkpoint.json")):
        case = json.loads(checkpoint.read_text(encoding="utf-8"))
        for turn in case.get("turns", []):
            turn_dir = checkpoint.parent / "turns" / f"{turn['index']:03d}"
            response = turn.get("response") or {}
            observed = []
            for step_index, step in enumerate(response.get("steps") or []):
                if step.get("name") != "llm":
                    continue
                reference = (step.get("output_summary") or {}).get("provider_capture")
                row = {"case_id": case.get("id", checkpoint.parent.name), "turn": turn["index"],
                       "step": step_index, "trace_id": response.get("trace_id"), "source": reference}
                try:
                    if not isinstance(reference, str):
                        raise ValueError("server reference missing")
                    source = verified_capture(reference, response.get("trace_id"))
                    target = turn_dir / "provider" / source.name
                    source_sha = sha(source)
                    if not args.dry_run:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if target.exists():
                            if sha(target) != source_sha:
                                raise ValueError("existing copy differs; no overwrite")
                        else:
                            with target.open("xb") as handle:
                                handle.write(source.read_bytes())
                    row.update(status="verified" if args.dry_run else "supplement_archived",
                               source_sha256=source_sha, copy=target.relative_to(ROOT).as_posix(),
                               copy_sha256=None if args.dry_run else sha(target))
                except Exception as exc:
                    row.update(status="not_verified", reason=str(exc))
                    failures.append(row)
                observed.append(row)
                records.append(row)
            if not args.dry_run and observed:
                supplement = turn_dir / "provider-evidence-supplement.json"
                new_json(supplement, {"created_at": datetime.now(timezone.utc).isoformat(),
                         "reason": "UUID.hex32 writer vs UUID36 observer filename mismatch",
                         "original_evidence_unchanged": True, "records": observed})
    after = {p.relative_to(ROOT).as_posix(): sha(p) for p in protected}
    if before != after:
        raise RuntimeError("historical observer evidence changed")
    value = {"created_at": datetime.now(timezone.utc).isoformat(), "dry_run": args.dry_run,
             "run_dir": run_dir.relative_to(ROOT).as_posix(), "observed_attempts": len(records),
             "verified_captures": len(records) - len(failures), "unverified_captures": len(failures),
             "protected_before_sha256": before, "protected_evidence_unchanged": before == after,
             "model_calls": 0, "api_calls": 0, "database_queries": 0,
             "records": records, "failures": failures}
    new_json(output, value)
    print(json.dumps({key: value[key] for key in ("dry_run", "observed_attempts", "verified_captures",
                      "unverified_captures", "protected_evidence_unchanged", "api_calls")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
