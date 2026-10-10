"""Check Git candidates for this machine's real credentials without printing them."""
from __future__ import annotations

import subprocess
import argparse
import json
from pathlib import Path

from dotenv import dotenv_values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", action="store_true", help="Also inspect every reachable Git blob")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    values = dotenv_values(root / ".env")
    secrets = [value.encode("utf-8") for name, value in values.items()
               if value and (name.endswith("PASSWORD") or name.endswith("API_KEY")
                             or name == "DB_URL" or name.endswith("_DB_URL"))]
    ignored = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=root).returncode == 0
    candidates = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root
    ).decode("utf-8").split("\0")
    hits = []
    oversized = []
    scanned = 0
    for relative in sorted(set(filter(None, candidates))):
        path = root / relative
        if not path.is_file():
            continue
        content = path.read_bytes()
        if len(content) >= 100 * 1024 * 1024:
            oversized.append(relative)
        scanned += 1
        if any(secret in content for secret in secrets):
            hits.append(relative)
    history_hits = []
    history_count = 0
    if args.history:
        objects = subprocess.check_output(["git", "rev-list", "--objects", "--all"], cwd=root).decode("utf8")
        object_paths = {line.partition(" ")[0]: line.partition(" ")[2] for line in objects.splitlines()}
        with subprocess.Popen(["git", "cat-file", "--batch"], cwd=root,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE) as process:
            assert process.stdin is not None and process.stdout is not None
            for oid, relative in object_paths.items():
                process.stdin.write((oid + "\n").encode("ascii"))
                process.stdin.flush()
                header = process.stdout.readline().decode("ascii").split()
                if len(header) != 3:
                    raise RuntimeError("Git history object could not be inspected")
                size = int(header[2])
                content = process.stdout.read(size)
                process.stdout.read(1)
                if header[1] == "blob":
                    history_count += 1
                    if any(secret in content for secret in secrets):
                        history_hits.append({"path": relative, "object": oid})
                    if size >= 100 * 1024 * 1024:
                        oversized.append("history:" + relative)
            process.stdin.close()
            if process.wait() != 0:
                raise RuntimeError("Git history inspection failed")
    tracked_env = subprocess.check_output(["git", "ls-files", "--", ".env"], cwd=root).strip() != b""
    record = {"candidate_files_scanned": scanned, "env_ignored": ignored,
              "env_tracked": tracked_env, "candidate_credential_hits": hits,
              "history_enabled": args.history, "history_blobs_scanned": history_count,
              "history_credential_hits": history_hits, "oversized_files": sorted(set(oversized)),
              "scope": "Exact matches of configured API keys, database passwords and URLs; no credential values recorded"}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(f"Checked {scanned} Git candidate files and {history_count} history blobs; .env ignored={ignored}; credential matches={len(hits) + len(history_hits)}")
    for relative in hits:
        print(f"Credential found in: {relative}")
    return 0 if ignored and not tracked_env and not hits and not history_hits and not oversized else 1


if __name__ == "__main__":
    raise SystemExit(main())
