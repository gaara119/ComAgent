"""Capture pytest commands/results with credentials removed before logging."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import dotenv_values
from qa_agent.config import get_settings


def redact(text):
    settings = get_settings()
    secrets = [settings.llm_api_key, settings.db_url, settings.aw_db_url]
    for url in (settings.db_url, settings.aw_db_url):
        secrets.append(unquote(urlsplit(url).password or ""))
    for path in (ROOT / ".env", ROOT / ".runtime/aw.env"):
        secrets.extend(str(value) for key, value in dotenv_values(path).items()
                       if value and ("PASSWORD" in key.upper() or "API_KEY" in key.upper()))
    for secret in sorted(set(secrets), key=len, reverse=True):
        if secret:
            text = text.replace(secret, "[redacted]")
    text = re.sub(r"postgres(?:ql)?://[^\s'\"]+", "postgresql://[redacted]", text)
    return re.sub(r"\bsk-[A-Za-z0-9_-]+", "[redacted]", text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args, pytest_args = parser.parse_known_args()
    target = args.output.resolve()
    if target.exists():
        raise RuntimeError("Choose a fresh result directory")
    target.mkdir(parents=True)
    command = [sys.executable, "-B", "-m", "pytest", *pytest_args]
    record = {"at_utc": datetime.now(timezone.utc).isoformat(), "argv": command,
              "holdout_predictions": 0, "capture": "actual stdout/stderr, credential redaction only"}
    (target / "command.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), "utf-8")
    child_env = dict(os.environ)
    child_env["LLM_CAPTURE_DIR"] = str(target / "provider-fixtures")
    record["provider_capture_scope"] = "module fixtures; not real model benchmark predictions"
    process = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True,
                             env=child_env)
    raw = process.stdout + process.stderr
    safe = redact(raw)
    (target / "output.txt").write_text(safe, "utf-8")
    record.update(exit_code=process.returncode, raw_output_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                  credential_redaction_applied=safe != raw)
    (target / "result.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), "utf-8")
    print(safe, end="")
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
