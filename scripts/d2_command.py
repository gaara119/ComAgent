"""Run an actual D2 command and retain redacted output, exit code and timing."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings


def redact(text: str) -> str:
    settings = get_settings()
    for secret in (settings.llm_api_key, settings.db_url, settings.aw_db_url):
        if secret:
            text = text.replace(secret, "[REDACTED]")
    text = re.sub(r"(?i)Bearer\s+\S+", "Bearer [REDACTED]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[REDACTED]", text)
    text = re.sub(r"(?i)postgres(?:ql)?://[^\s\"']+", "[REDACTED_DSN]", text)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--directory", type=Path, default=ROOT / "eval/artifacts/d2/commands")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    args.directory = args.directory.resolve()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command after -- is required")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.name):
        parser.error("name must be a simple filename")
    args.directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    stem = args.directory / f"{timestamp}-{args.name}"
    started = time.perf_counter()
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding="utf-8", errors="replace",
                               env=__import__("os").environ | {"PYTHONIOENCODING": "utf-8"})
    with stem.with_suffix(".txt").open("w", encoding="utf-8") as stream:
        for line in process.stdout:
            safe_line = redact(line)
            stream.write(safe_line)
            stream.flush()
            print(safe_line, end="", flush=True)
    exit_code = process.wait()
    record = {"command": [redact(x) for x in command], "cwd": ".", "started_at_utc": timestamp,
              "elapsed_seconds": round(time.perf_counter() - started, 3),
              "exit_code": exit_code, "output": stem.with_suffix(".txt").relative_to(ROOT).as_posix()}
    stem.with_suffix(".json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    with (args.directory / "commands.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Recorded exit={exit_code}: {stem.relative_to(ROOT).as_posix()}", flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
