"""Safe, reproducible code/prompt/config hashes, without ever copying .env."""
from __future__ import annotations

from pathlib import Path
import subprocess

from common import ROOT, HERE, digest, json_hash, utcnow, write_new

SAFE_CONFIG_FIELDS = ("llm_model", "llm_timeout_seconds", "llm_max_attempts", "llm_request_max_attempts", "llm_max_tokens", "llm_thinking",
                      "catalog_path", "statement_timeout_ms", "max_rows", "sql_repair_attempts",
                      "rag_handler", "bge_model_path", "rag_ocr_model_path", "rag_embedding_max_length",
                      "rag_embedding_batch_size", "rag_embedding_device", "rag_embedding_quantization",
                      "rag_index_path", "rag_manifest_path", "rag_top_k", "rag_candidate_k", "rag_rrf_k", "rag_answer_mode",
                      "nlu_enabled", "value_index_path", "nlu_fuzzy_threshold", "nlu_fuzzy_margin",
                      "nlu_vector_threshold", "nlu_vector_margin", "aw_catalog_path", "aw_schema_index_path")


def code_hashes(settings=None) -> dict[str, str]:
    if settings is None:
        from qa_agent.config import get_settings
        settings = get_settings()
    paths = []
    for directory in (ROOT / "qa_agent", ROOT / "api"):
        paths.extend(path for path in directory.rglob("*") if path.is_file() and path.suffix in {".py", ".txt", ".yaml", ".yml", ".json"}
                     and "__pycache__" not in path.parts and not any(part.startswith(".") for part in path.relative_to(ROOT).parts))
    paths.extend(HERE.glob("*.py"))
    paths.append(ROOT / "eval" / "metrics.py")
    paths.append(ROOT / "requirements.txt")
    # These are catalog/index artifacts, not evaluation examples or credentials.
    directories = [ROOT / "data/catalog", ROOT / "data/business", ROOT / "data/aliases", ROOT / "data/rules",
                   ROOT / "data/indexes/values"]
    # A historical default index is insufficient: hash the settings actually loaded by this version.
    # Only index artifacts are included; model weight directories are never traversed.
    for field in ("value_index_path", "rag_index_path", "aw_schema_index_path"):
        if getattr(settings, field, None):
            directories.append(Path(getattr(settings, field)))
    for directory in directories:
        if directory.exists():
            paths.extend(path for path in directory.rglob("*") if path.is_file()
                         and path.suffix in {".yaml", ".yml", ".json", ".jsonl", ".csv", ".npz", ".npy", ".faiss", ".index", ".pkl", ".pickle"}
                         and path.name != ".env")
    for field in ("catalog_path", "aw_catalog_path", "rag_manifest_path"):
        if getattr(settings, field, None):
            path = Path(getattr(settings, field))
            if path.is_file() and path.name != ".env":
                paths.append(path)
    # Use absolute keys for an explicitly configured external index, while all current active artifacts are project-local.
    return {(path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path.resolve())): digest(path)
            for path in sorted(set(paths))}


def snapshot() -> dict:
    from qa_agent.config import get_settings
    settings = get_settings()
    public = {name: str(value) if isinstance((value := getattr(settings, name)), Path) else value for name in SAFE_CONFIG_FIELDS if hasattr(settings, name)}
    hashes = code_hashes(settings)
    def git(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False).stdout.strip()
    from hashlib import sha256
    from qa_agent.sql.generator import SQL_SYSTEM_PROMPT
    observed_sql = {"single_table_loaded": sha256(SQL_SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
                    "multi_table_file": hashes.get("qa_agent/sql/prompts/multi_table.txt")}
    return {"created_at": utcnow(), "git_head": git("rev-parse", "HEAD"),
            "git_status": git("status", "--porcelain=v1"), "files": hashes, "files_sha256": json_hash(hashes),
            "prompt_files": {key: value for key, value in hashes.items() if "/prompts/" in key or "prompt" in Path(key).name},
            "safe_config": public, "safe_config_sha256": json_hash(public), "sql_prompt_sha256": observed_sql,
            "credentials_included": False, "prediction_calls": 0}


def resolve(root: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else root / candidate


def verify_freeze(path: Path, labels: Path) -> dict:
    import json
    frozen = json.loads(path.read_text(encoding="utf-8-sig"))
    if frozen.get("status") != "frozen":
        raise ValueError("Formal root freeze is required; a proposal does not authorize API prediction")
    if frozen.get("label_sha256") != digest(labels):
        raise ValueError("Dataset differs from the formally frozen labels")
    base = path.parent
    for file_key, hash_key in (("scoring_protocol_file", "scoring_protocol_sha256"), ("code_snapshot_file", "code_snapshot_sha256")):
        target = resolve(base, frozen[file_key])
        if digest(target) != frozen[hash_key]:
            raise ValueError(f"Frozen artifact changed: {file_key}")
    prior = json.loads(resolve(base, frozen["code_snapshot_file"]).read_text(encoding="utf-8-sig"))
    current = snapshot()
    if prior["files"] != current["files"] or prior["safe_config"] != current["safe_config"]:
        raise ValueError("Current code/prompt/config is not the frozen version")
    return {"freeze": frozen, "freeze_sha256": digest(path), "current_snapshot": current}


def service_evidence(health: dict, current: dict, restart_record: Path | None) -> dict:
    """Require actual server load hashes, or a timestamped root restart attestation."""
    observed = health.get("runtime_snapshot") or health.get("observability") or health.get("runtime") or {}
    prompts = observed.get("prompt_files") or observed.get("prompt_sha256") or health.get("prompt_sha256")
    if prompts == current["prompt_files"]:
        return {"method": "health_prompt_hashes", "observed": observed}
    if restart_record:
        import json
        record = json.loads(restart_record.read_text(encoding="utf-8-sig"))
        if record.get("files_sha256") != current["files_sha256"] or not record.get("restarted_at") or not record.get("pid"):
            raise ValueError("Restart record must attest PID, time, and the current complete snapshot files_sha256")
        sql_hash = health.get("sql_prompt_sha256")
        if sql_hash and sql_hash != current.get("sql_prompt_sha256"):
            raise ValueError("Loaded SQL prompt hash differs from frozen local runtime prompt")
        return {"method": "root_restart_record", "record": record, "record_sha256": digest(restart_record),
                "observed_loaded_sql_prompt_hashes": sql_hash}
    raise ValueError("Service has no matching prompt-load hash or valid root restart record")
