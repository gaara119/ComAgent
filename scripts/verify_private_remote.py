"""Verify the authenticated private repository and pushed HEAD; never log tokens."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    record = json.loads((ROOT / "notes/github-repository.json").read_text(encoding="utf8"))
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"}
    result = subprocess.run(["git", "credential", "fill"],
                            input="protocol=https\nhost=github.com\n\n",
                            capture_output=True, text=True, env=env, timeout=30)
    credential = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    if result.returncode or not credential.get("password"):
        raise SystemExit("Authenticated GitHub credential is unavailable.")
    with httpx.Client(base_url="https://api.github.com", timeout=30,
                      headers={"Authorization": "Bearer " + credential["password"],
                               "Accept": "application/vnd.github+json",
                               "X-GitHub-Api-Version": "2022-11-28"}) as client:
        response = client.get("/repos/" + record["full_name"])
        if response.status_code != 200:
            raise SystemExit(f"Private repository verification failed: HTTP {response.status_code}")
        repo = response.json()
        if repo.get("private") is not True or repo["id"] != record["id"]:
            raise SystemExit("Repository identity or privacy verification failed.")
        response = client.get("/repos/" + record["full_name"] + "/commits/main")
        if response.status_code != 200:
            raise SystemExit(f"Remote commit verification failed: HTTP {response.status_code}")
        remote_sha = response.json()["sha"]
    local_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ls_remote = subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/main"],
                                        cwd=ROOT, text=True, env=env, timeout=60).split()[0]
    if not (remote_sha == local_sha == ls_remote):
        raise SystemExit("The GitHub API, remote main and local HEAD do not match.")
    receipt = {"verified_at_utc": datetime.now(timezone.utc).isoformat(), "private": True,
               "repository": record["html_url"], "branch": "main", "commit": local_sha,
               "api_remote_local_heads_match": True,
               "git_worktree_clean": not bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip())}
    path = ROOT / ".runtime/github-publish.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
