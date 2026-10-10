"""Check Git candidates for this machine's real credentials without printing them."""
from __future__ import annotations

import subprocess
from pathlib import Path

from dotenv import dotenv_values


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    values = dotenv_values(root / ".env")
    secrets = [value.encode("utf-8") for name, value in values.items()
               if value and (name.endswith("PASSWORD") or name.endswith("API_KEY") or name == "DB_URL")]
    ignored = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=root).returncode == 0
    candidates = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root
    ).decode("utf-8").split("\0")
    hits = []
    scanned = 0
    for relative in sorted(set(filter(None, candidates))):
        path = root / relative
        if not path.is_file():
            continue
        content = path.read_bytes()
        scanned += 1
        if any(secret in content for secret in secrets):
            hits.append(relative)
    print(f"Checked {scanned} Git candidate files; .env ignored={ignored}; credential matches={len(hits)}")
    for relative in hits:
        print(f"Credential found in: {relative}")
    return 0 if ignored and not hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
