"""Create this project's private GitHub remote using Git's existing credential.

Credentials stay in memory. Only public repository metadata is printed or saved.
Run after the project owner has authorized repository creation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"}
    result = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, env=env, timeout=30,
    )
    credential = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    token = credential.get("password")
    if result.returncode or not token:
        raise SystemExit("No non-interactive GitHub credential is available.")
    headers = {"Authorization": "Bearer " + token,
               "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    with httpx.Client(base_url="https://api.github.com", headers=headers, timeout=30) as client:
        profile = client.get("/user")
        if profile.status_code != 200:
            raise SystemExit(f"GitHub profile request failed: HTTP {profile.status_code}")
        owner = profile.json()["login"]
        if owner != "gaara119":
            raise SystemExit("Credential account differs from the confirmed project owner.")
        name = "china-electronics-cup-task8-comagent"
        existing = client.get(f"/repos/{owner}/{name}")
        if existing.status_code == 404:
            response = client.post("/user/repos", json={
                "name": name, "private": True, "auto_init": False,
                "description": "中国电子杯赛题八：多模态精准问数问答智能体，D1 A/B实现与验收资料",
            })
            if response.status_code != 201:
                raise SystemExit(f"Private repository creation failed: HTTP {response.status_code}")
            repo = response.json()
        elif existing.status_code == 200:
            repo = existing.json()
            # A rerun may reuse only the private repository created by this script.
            receipt = ROOT / "notes/github-repository.json"
            if not receipt.exists() or json.loads(receipt.read_text(encoding="utf8")).get("id") != repo["id"]:
                raise SystemExit("Repository name is already in use; existing content was left untouched.")
        else:
            raise SystemExit(f"Repository lookup failed: HTTP {existing.status_code}")
        if repo.get("private") is not True:
            raise SystemExit("Repository privacy verification failed.")
        record = {"id": repo["id"], "full_name": repo["full_name"],
                  "html_url": repo["html_url"], "clone_url": repo["clone_url"],
                  "private": True, "created_at": repo["created_at"],
                  "upload_status": "pending_final_acceptance"}
        (ROOT / "notes/github-repository.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
