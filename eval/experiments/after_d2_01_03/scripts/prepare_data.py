"""Bounded synthetic-dev generation and two independent-context AI label checks.

No tested-system call, no business-file mutation, no evaluation holdout contents.
All files are owned by this experiment; checkpoints prevent repeated paid calls.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timezone
from hashlib import sha256
import csv
import json
from pathlib import Path
import platform
import re
import sys
from time import perf_counter
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from pydantic import BaseModel, ConfigDict, Field, model_validator
from qa_agent.config import get_settings, sanitize_error
from qa_agent.llm import JsonLLM
from qa_agent.trace import TraceRecorder
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql

def now():
    return datetime.now(timezone.utc).isoformat()

def dump(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

def jsonl(path: Path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(v, ensure_ascii=False) + "\n" for v in values), encoding="utf-8")

def digest(path: Path):
    return sha256(path.read_bytes()).hexdigest()

class CaseBatch(BaseModel):
    cases: list[dict[str, Any]] = Field(min_length=1, max_length=5)
    notes: list[str] = Field(default_factory=list)

class CompleteCase(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    family_id: str
    task: str
    category: str
    input: str = Field(min_length=1)
    scope: dict[str, Any]
    history: list[Any]
    expected_behavior: str
    allowed_interpretations: list[Any]
    expected_bindings: list[dict[str, Any]]
    missing_conditions: list[str]
    business_basis: list[Any] = Field(min_length=1)
    reference_intent: dict[str, Any]
    gold_sql: str | None = Field(min_length=1)
    controller: dict[str, Any] | None
    @model_validator(mode="after")
    def completeness(self):
        if self.category != "multi_candidate" and self.gold_sql is None:
            raise ValueError("Executable or L2-final reference requires SQL")
        if self.task == "03" and self.category == "L2" and not self.controller:
            raise ValueError("L2 requires offline controller")
        if self.id in {"sp03-23", "sp03-24", "sp03-25"} and not (self.controller or {}).get("post_completion_turns"):
            raise ValueError("Assigned year/region/metric modification requires a real post_completion_turn")
        return self

class CompleteBatch(BaseModel):
    cases: list[CompleteCase] = Field(min_length=5, max_length=5)
    notes: list[str] = Field(default_factory=list)

class SQLRequiredCase(CompleteCase):
    gold_sql: str = Field(min_length=1, description="Fully specified final intent SQL, also required for L2 after the allowed user supplements; never initial unresolved-query SQL")

class SQLRequiredBatch(BaseModel):
    cases: list[SQLRequiredCase] = Field(min_length=5, max_length=5)
    notes: list[str] = Field(default_factory=list)

class SQLAnnotation(BaseModel):
    id: str
    gold_sql: str = Field(min_length=1)
    business_basis: list[Any] = Field(min_length=1)
    issues: list[str] = Field(default_factory=list)

class SQLAnnotations(BaseModel):
    annotations: list[SQLAnnotation] = Field(min_length=1, max_length=5)

class ReviewItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    verdict: Literal["pass", "disputed", "reject"]
    semantic_sql_check: Literal["pass", "disputed", "not_applicable"]
    classification_check: Literal["pass", "disputed"]
    binding_check: Literal["pass", "disputed"]
    controller_check: Literal["pass", "disputed", "not_applicable"]
    reason: str = Field(min_length=1)
    evidence: list[Any] = Field(min_length=1)
    issues: list[Any]
    suggested_corrections: Any = None

class ReviewBatch(BaseModel):
    reviews: list[ReviewItem]
    notes: list[str] = Field(default_factory=list)

class RecordingClient:
    """Capture every provider attempt while retaining JsonLLM's owned retry loop."""
    def __init__(self, client, directory, settings):
        self.client, self.directory, self.settings = client, directory, settings
        self.chat = self
        self.completions = self
        self.attempts = []
    def __enter__(self):
        self.client.__enter__()
        return self
    def __exit__(self, *args):
        return self.client.__exit__(*args)
    def create(self, **kwargs):
        started = perf_counter()
        attempt = {"number": len(self.attempts)+1, "started_at": now()}
        try:
            response = self.client.chat.completions.create(**kwargs)
            attempt.update({"ok": True, "response_id": response.id,
                            "model": response.model,
                            "usage": response.usage.model_dump() if response.usage else {},
                            "choices": [c.model_dump() for c in response.choices]})
            return response
        except Exception as exc:
            attempt.update({"ok": False, "error": sanitize_error(exc, self.settings)})
            raise
        finally:
            attempt["latency_ms"] = round((perf_counter()-started)*1000)
            self.attempts.append(attempt)
            dump(self.directory / "provider_attempts.json", self.attempts)

class AuditedLLM(JsonLLM):
    def __init__(self, directory):
        # Max two additional attempts; generation needs enough JSON output tokens.
        settings = replace(get_settings(), llm_max_attempts=min(3, get_settings().llm_max_attempts),
                           llm_max_tokens=12000, llm_timeout_seconds=180)
        super().__init__(settings)
        self.directory = directory
    def _client(self):
        return RecordingClient(super()._client(), self.directory, self.settings)

def model_call(call_id, prompt_name, payload, response_model):
    directory = EXP / "calls" / call_id
    result_path = directory / "result.json"
    if result_path.is_file():
        return response_model.model_validate_json(result_path.read_text(encoding="utf-8"))
    if (directory / "complete.json").is_file():
        raise RuntimeError(f"Completed failed call {call_id}; no automatic restart beyond attempt budget")
    directory.mkdir(parents=True, exist_ok=True)
    prompt_path = EXP / "prompts" / prompt_name
    llm = AuditedLLM(directory)
    dump(directory / "request.json", {"call_id": call_id, "prompt_file": f"prompts/{prompt_name}",
                                     "prompt_sha256": digest(prompt_path),
                                     "system_prompt": prompt_path.read_text(encoding="utf-8"), "payload": payload,
                                     "response_schema": response_model.model_json_schema(),
                                     "generation_config": {"model": llm.settings.llm_model,
                                         "max_attempts": llm.settings.llm_max_attempts,
                                         "max_tokens": llm.settings.llm_max_tokens,
                                         "timeout_seconds": llm.settings.llm_timeout_seconds,
                                         "thinking": llm.settings.llm_thinking}})
    trace = TraceRecorder(settings=llm.settings)
    try:
        result = llm.complete_json(prompt_path.read_text(encoding="utf-8"),
                                   json.dumps(payload, ensure_ascii=False), response_model, trace)
        dump(result_path, result.model_dump())
        dump(directory / "complete.json", {"ok": True, "finished_at": now(), "latency_ms": trace.latency_ms,
                                           "attempts": trace.llm_attempts})
        return result
    except Exception as exc:
        dump(directory / "complete.json", {"ok": False, "finished_at": now(), "latency_ms": trace.latency_ms,
                                           "attempts": trace.llm_attempts, "error": sanitize_error(exc, llm.settings)})
        raise
    finally:
        dump(directory / "trace.json", [s.model_dump() for s in trace.steps])

SOURCE_PATHS = [
    "data/catalog/chinook.yaml", "data/db/source_manifest.json", "data/db/db_check.json",
    "data/rules/metric_definitions.json", "data/aliases/aliases-d2-reviewed.csv",
    "notes/d2/业务指标口径提案.md", "notes/references/d3-and-special/方案.md",
    "notes/references/d3-and-special/D2-可执行技术方案.md",
    "notes/references/d3-and-special/01-要素精准识别与问题改写-技术方案.md",
    "notes/references/d3-and-special/03-智能语义校验与澄清-技术方案.md",
    "notes/references/d3-and-special/专项造题.txt", "README.md",
    "qa_agent/clarify/rules.py", "qa_agent/clarify/state.py", "qa_agent/clarify/service.py",
    "qa_agent/clarify/extractor.py", "qa_agent/clarify/clarify_rules.yaml",
    "qa_agent/llm.py", "qa_agent/config.py", "qa_agent/trace.py",
]

def setup():
    for dirname in ["prompts", "materials", "data", "checks", "reports", "calls"]:
        (EXP / dirname).mkdir(parents=True, exist_ok=True)
    # Snapshot approved materials before any model generation; clarify implementation
    # is hashed for version observation only and does not determine gold behavior.
    hashes = {name: digest(ROOT / name) for name in SOURCE_PATHS if (ROOT / name).is_file()}
    missing = [name for name in SOURCE_PATHS if not (ROOT / name).is_file()]
    settings = get_settings()
    manifest = {"created_at": now(), "python": platform.python_version(), "model": settings.llm_model,
                "source_hashes": hashes, "missing": missing, "db_id": "chinook", "timeout_ms": 5000,
                "requested_call_concurrency": 1, "per_call_max_attempts": min(3, settings.llm_max_attempts),
                "evidence_status": "synthetic_dev_ai_prechecked_not_human_accepted",
                "holdout_policy": "No holdout question/answer read by this subagent. Root historical context may have seen holdout; a new context does not erase historical exposure.",
                "no_tested_system_calls": True}
    manifest_path = EXP / "materials" / "source_manifest.json"
    if not manifest_path.exists():
        dump(manifest_path, manifest)
    catalog = load_catalog(settings.catalog_path)
    schemas = [{"table": t.name, "description": t.description,
                "columns": {c.name: c.data_type for c in t.columns},
                "foreign_keys": list(t.foreign_keys)} for t in catalog.tables]
    aliases = list(csv.DictReader((ROOT / "data/aliases/aliases-d2-reviewed.csv").open(encoding="utf-8-sig")))
    plan = (ROOT / "notes/references/d3-and-special/方案.md").read_text(encoding="utf-8-sig")
    start = plan.index("#### 3.6.4")
    end = plan.index("#### 3.6.5", start)
    rules = json.loads((ROOT / "data/rules/metric_definitions.json").read_text(encoding="utf-8-sig"))
    queries = {
        "reader": "SELECT current_user AS reader_user, current_setting('default_transaction_read_only') AS read_only, current_setting('statement_timeout') AS timeout;",
        "countries": "SELECT DISTINCT country FROM public.customer ORDER BY country;",
        "billing_countries": "SELECT DISTINCT billing_country FROM public.invoice ORDER BY billing_country;",
        "genres": "SELECT genre_id, name FROM public.genre ORDER BY genre_id;",
        "media_types": "SELECT media_type_id, name FROM public.media_type ORDER BY media_type_id;",
        "artist_catalog": "SELECT artist_id, name FROM public.artist ORDER BY artist_id LIMIT 40;",
        "named_artist_values": "SELECT artist_id, name FROM public.artist WHERE name IN ('Iron Maiden','Led Zeppelin','Metallica','U2','AC/DC','Queen','Deep Purple','Pink Floyd') ORDER BY artist_id;",
        "date_evidence": "SELECT MIN(invoice_date) AS first_date, MAX(invoice_date) AS last_date, COUNT(*) AS invoices FROM public.invoice;",
        "billing_customer_difference": "SELECT COUNT(*) AS differences FROM public.invoice i JOIN public.customer c ON i.customer_id=c.customer_id WHERE i.billing_country IS DISTINCT FROM c.country;",
    }
    live_path = EXP / "materials" / "readonly_live_facts.json"
    if live_path.is_file():
        live = json.loads(live_path.read_text(encoding="utf-8"))
    else:
        live = {}
        for name, sql in queries.items():
            result = execute_sql(sql, settings.db_url, 5000, 200)
            live[name] = {"sql": sql, "result": asdict(result)}
        if live["reader"]["result"]["rows"][0][0] != "qa_reader":
            raise RuntimeError("Expected the existing qa_reader role")
        dump(live_path, live)
    materials = {"data_version": hashes["data/db/source_manifest.json"], "schema": schemas,
                 "confirmed_business_rules": rules,
                 "approved_proposal": (ROOT / "notes/d2/业务指标口径提案.md").read_text(encoding="utf-8-sig"),
                 "total_plan_semantic_gate": plan[start:end],
                 "approved_aliases_and_candidate_relations": aliases,
                 "live_database_facts": live,
                 "adjudication_notes": [
                     "Plan table's blanket L2 comparison wording is read with its explicit required/derivable fields: fully specified comparison is L0, missing current period/denominator is L2.",
                     "Approved metric definitions require explicit period for repeat customers/popular tracks; missing period is not silently filled even when plan examples omit it.",
                     "Top10 is the technical default explicitly present in total plan 3.6.4 ranking.defaults.top_n; record this basis on any such L1 case.",
                     "No global object-free purchase/popularity default; customer-object buy-most is amount, track-object popular is purchased quantity.",
                     "approved_candidate is a candidate relationship only, never an automatic unique binding; pending aliases disabled.",
                     "Residence and billing countries have different meanings even though current 412-invoice snapshot shows no differences.",
                     "Dates 2021-2025 are available, not evidence of complete years. Explicit outside-date or outside-entity queries remain exact no-match boundaries.",
                 ]}
    dump(EXP / "materials" / "generation_materials.json", materials)
    payload_text = json.dumps(materials, ensure_ascii=False)
    for secret in (settings.llm_api_key, settings.db_url, settings.aw_db_url):
        if secret and secret in payload_text:
            raise RuntimeError("Outbound materials unexpectedly contain configured secret; refused")
    dump(EXP / "materials" / "outbound_payload_audit.json", {
        "checked_at": now(), "materials_sha256": digest(EXP / "materials" / "generation_materials.json"),
        "contains_configured_secret": False,
        "schema_contains_types_and_descriptions_not_customer_records": True,
        "outbound_db_queries": list(queries),
        "outbound_values": "Public Chinook music artists/genres/media types/country catalog/date range; no customer names, addresses, emails, phone numbers or employee records",
        "business_materials": "Project-authored music sample metric definitions and synthetic alias review table; not private enterprise records",
        "public_source_evidence": "data/db/source_manifest.json: official github.com/lerocha/chinook-database v1.4.5, MIT license",
        "explicit_task_authorization": "专项造题.txt §三 explicitly requires prompts to state schema/catalog/confirmed rules and to actually use them with the existing model; §四 explicitly identifies existing Chinook as this round's source",
    })
    return materials

QUOTAS = {"01": {"standard": 3, "alias": 6, "typo": 6, "pinyin": 3,
                 "mixed_language": 3, "colloquial": 3, "multi_candidate": 3, "explicit_absent": 3},
          "03": {"L0": 10, "L1": 5, "L2": 15}}
PILOT_CATEGORIES = {"01": ["standard", "alias", "alias", "typo", "typo", "pinyin", "mixed_language", "colloquial", "multi_candidate", "explicit_absent"],
                    "03": ["L0", "L0", "L0", "L1", "L1", "L2", "L2", "L2", "L2", "L2"]}

def planned_batches():
    plans = []
    counters = Counter()
    for task in ("01", "03"):
        pilot = PILOT_CATEGORIES[task]
        remaining = [category for category, total in QUOTAS[task].items() for _ in range(total-pilot.count(category))]
        for stage, categories in [("pilot", pilot), ("expansion", remaining)]:
            for offset in range(0, len(categories), 5):
                items = []
                for category in categories[offset:offset+5]:
                    counters[task] += 1
                    item = {"id": f"sp{task}-{counters[task]:02}", "category": category}
                    changes = {"sp03-23": "year", "sp03-24": "region", "sp03-25": "metric"}
                    if item["id"] in changes:
                        item["required_post_completion_change"] = changes[item["id"]]
                    items.append(item)
                plans.append({"call_id": f"generate-{task}-{stage}-{offset//5+1:02}",
                              "stage": stage, "task": task, "items": items})
    return sorted(plans, key=lambda b: (b["stage"] != "pilot", b["task"], b["call_id"]))

REQUIRED = {"id", "family_id", "task", "category", "input", "scope", "history", "expected_behavior",
            "allowed_interpretations", "expected_bindings", "missing_conditions", "business_basis",
            "gold_sql", "reference_intent", "controller"}

def check_sql(sql, catalog):
    expressions = sqlglot.parse(sql, read="postgres")
    if len(expressions) != 1 or not isinstance(expressions[0], exp.Query):
        raise ValueError("One SELECT/CTE query required")
    expression = expressions[0]
    # The experiment's allowed outbound scope is music/countries/anonymous
    # aggregate statistics. Prevent generated references from selecting contact
    # records; these fields are unnecessary for the authorized entity quotas.
    contact_columns = {"first_name", "last_name", "email", "phone", "fax", "address",
                       "postal_code", "company", "birth_date", "hire_date"}
    if any(column.name in contact_columns for column in expression.find_all(exp.Column)):
        raise ValueError("Contact/person-record column outside this experiment's payload scope")
    if expression.find(exp.Into) or expression.find(exp.Lock):
        raise ValueError("Read-only SQL required")
    ctes = {c.alias_or_name for c in expression.find_all(exp.CTE)}
    for table in expression.find_all(exp.Table):
        if table.name in ctes:
            continue
        if table.db not in ("", "public"):
            raise ValueError("Only actual public business schema allowed")
        catalog.get_table(table.name, "public")
    # Independently qualify all real fields against the catalog; keep original SQL.
    qualify(expression.copy(), dialect="postgres", schema=catalog.sqlglot_schema(),
            validate_qualify_columns=True, identify=False)
    from qa_agent.sql.validator import ALLOWED_FUNCTIONS, _function_name
    for function in expression.find_all(exp.Func):
        if _function_name(function) not in ALLOWED_FUNCTIONS:
            raise ValueError("Function not allowed: " + _function_name(function))
    return sorted({t.name for t in expression.find_all(exp.Table) if t.name not in ctes})

def program_check(cases, stage):
    settings = get_settings()
    catalog = load_catalog(settings.catalog_path)
    seen_inputs, seen_ids = {}, set()
    families = {}
    family_updates = []
    for case in cases:
        sql = case.get("gold_sql")
        if not sql:
            continue
        try:
            tree = sqlglot.parse_one(sql, read="postgres")
            # Conservative structural fingerprint: normalize identifier/table
            # aliases and ignore projected column aliases, never infer intent
            # from result equality (many unrelated no-data queries return 0).
            aliases = {t.alias_or_name: t.name for t in tree.find_all(exp.Table)}
            for column in tree.find_all(exp.Column):
                if column.table in aliases:
                    column.set("table", exp.to_identifier(aliases[column.table]))
            for table in tree.find_all(exp.Table):
                table.set("alias", None)
            for alias in list(tree.find_all(exp.Alias)):
                alias.replace(alias.this)
            signature = tree.sql(dialect="postgres", normalize=True)
            if signature in families and case["family_id"] != families[signature]:
                old = case["family_id"]
                case["generated_family_id"] = old
                case["family_id"] = families[signature]
                case["family_normalization_basis"] = "Same canonical SQL structure and complete query conditions; no result-based grouping"
                family_updates.append({"id": case["id"], "before": old, "after": case["family_id"]})
            else:
                families[signature] = case["family_id"]
        except Exception:
            pass  # Invalid SQL remains an explicit check issue below.
    outcomes = []
    for case in cases:
        issues = []
        missing = REQUIRED - case.keys()
        if missing:
            issues.append("missing_fields:" + ",".join(sorted(missing)))
        if case.get("id") in seen_ids:
            issues.append("duplicate_id")
        seen_ids.add(case.get("id"))
        key = "".join(str(case.get("input", "")).casefold().split())
        if key in seen_inputs:
            issues.append("duplicate_input:" + seen_inputs[key])
        seen_inputs[key] = case.get("id", "")
        if case.get("category") not in QUOTAS.get(case.get("task"), {}):
            issues.append("invalid_category")
        if case.get("scope") != {"route": "sql", "db_id": "chinook", "doc_ids": []}:
            issues.append("invalid_scope")
        if not case.get("business_basis"):
            issues.append("no_business_basis")
        for binding in case.get("expected_bindings", []):
            if binding.get("operator", "=").upper() not in {"=", "!=", "<>", "IN", "NOT IN", ">=", "<=", ">", "<", "LIKE", "ILIKE", "BETWEEN", "IS NULL", "IS NOT NULL"}:
                issues.append("illegal_binding_operator:" + str(binding.get("operator")))
            try:
                table_name, column_name = binding.get("column", "").split(".")
                if column_name not in catalog.get_table(table_name).column_names:
                    issues.append("unknown_binding_column:" + binding["column"])
            except Exception:
                issues.append("unknown_binding_column:" + str(binding.get("column")))
        if case.get("task") == "03" and case.get("category") == "L2":
            controller = case.get("controller") or {}
            if not case.get("missing_conditions") or not controller.get("allowed_user_supplements") or not controller.get("hidden_goal") or not controller.get("final_intent"):
                issues.append("incomplete_offline_controller")
        elif case.get("missing_conditions") and case.get("category") != "multi_candidate":
            issues.append("unexpected_missing_for_executable_case")
        sql_checks = []
        sqls = [("final", case.get("gold_sql"))]
        candidate_sqls = case.get("candidate_sql") or {}
        if isinstance(candidate_sqls, dict):
            sqls.extend(("candidate:" + str(key), value) for key, value in candidate_sqls.items())
        for i, interpretation in enumerate(case.get("allowed_interpretations", []), 1):
            if isinstance(interpretation, dict) and interpretation.get("candidate_sql"):
                sqls.append((f"interpretation_candidate:{i}", interpretation["candidate_sql"]))
        for i, turn in enumerate((case.get("controller") or {}).get("post_completion_turns", []), 1):
            sqls.append((f"post_completion_{i}", turn.get("gold_sql")))
        for label, sql in sqls:
            if sql is None:
                if case.get("category") != "multi_candidate":
                    issues.append("missing_sql:" + label)
                continue
            try:
                tables = check_sql(sql, catalog)
                result = execute_sql(sql, settings.db_url, 5000, 200)
                sql_checks.append({"label": label, "sql": sql, "tables": tables,
                                   "result": asdict(result), "status": "executed_readonly"})
                if label == "final":
                    case["gold_result"] = asdict(result)
            except Exception as exc:
                message = sanitize_error(exc, settings)
                issues.append("sql_check:" + label + ":" + message)
                sql_checks.append({"label": label, "sql": sql, "status": "failed", "error": message})
        case["auto_status"] = "passed" if not issues else "disputed"
        case["auto_issues"] = issues
        case["human_review_status"] = "pending_human_review"
        outcomes.append({"id": case.get("id"), "status": case["auto_status"], "issues": issues, "sql_checks": sql_checks})
    dump(EXP / "checks" / f"program-{stage}.json", {"checked_at": now(), "checks": outcomes,
         "counts": dict(Counter(c["status"] for c in outcomes)), "sql_role": "qa_reader", "timeout_ms": 5000,
         "conservative_family_updates": family_updates})
    jsonl(EXP / "data" / f"cases-{stage}-auto.jsonl", cases)
    return outcomes

def generate(stage, materials):
    all_cases = []
    repair_file = EXP / "data" / "pilot-repairs-v2.json"
    repairs = json.loads(repair_file.read_text(encoding="utf-8")) if repair_file.exists() else {}
    for plan in planned_batches():
        if stage == "pilot" and plan["stage"] != "pilot":
            continue
        prior = [{"id": c["id"], "family_id": c["family_id"], "input": c["input"]} for c in all_cases]
        payload = {"source_materials": materials, "batch_plan": plan, "all_quotas": QUOTAS,
                   "earlier_generated_inputs": prior,
                   "generation_version": "special-dev-v1-before-v0"}
        recovered = EXP / "calls" / plan["call_id"] / "recovered-invalid-candidates.json"
        if recovered.is_file():
            result = CaseBatch.model_validate_json(recovered.read_text(encoding="utf-8"))
        else:
            result = model_call(plan["call_id"], f"generate-{plan['task']}.txt", payload,
                                CaseBatch if plan["stage"] == "pilot" else
                                SQLRequiredBatch if plan["task"] == "03" and not (EXP / "calls" / plan["call_id"] / "result.json").exists() else CompleteBatch)
        case_values = result.model_dump()["cases"]
        expected = [(c["id"], c["category"]) for c in plan["items"]]
        actual = [(c.get("id"), c.get("category")) for c in case_values]
        if actual != expected:
            dump(EXP / "data" / f"rejected-{plan['call_id']}.json", {"expected": expected, "actual": actual, "cases": case_values})
            raise RuntimeError("Generator failed fixed quota/ID contract; original attempts saved")
        for c in case_values:
            c.update({"generation_call_id": plan["call_id"], "generation_stage": plan["stage"],
                      "data_version": materials["data_version"], "dataset_label": "本轮合成开发数据",
                      "split": "dev", "reference_version": "special-dev-v1", "ai_status": "not_yet_reviewed",
                      "human_review_status": "pending_human_review"})
            if c["id"] in repairs:
                replacement = repairs[c["id"]]
                c.update(replacement)
                c["reference_version"] = "special-dev-v2-pilot-repaired-before-v0"
                c["original_generation_call_id"] = plan["call_id"]
        all_cases.extend(case_values)
        jsonl(EXP / "data" / f"cases-{stage}-generated.jsonl", all_cases)
        print(json.dumps({"completed_batch": plan["call_id"], "cases_so_far": len(all_cases)}, ensure_ascii=False), flush=True)
    outcomes = program_check(all_cases, stage)
    dump(EXP / "data" / f"generation-{stage}-summary.json", {
        "count": len(all_cases), "quotas": QUOTAS,
        "actual_categories": {t: dict(Counter(c["category"] for c in all_cases if c["task"] == t)) for t in QUOTAS},
        "program_counts": dict(Counter(c["status"] for c in outcomes)),
        "duplicates": [c for c in outcomes if any("duplicate" in issue for issue in c["issues"])],
        "rejected_attempts": [str(p.relative_to(EXP)) for p in (EXP / "data").glob("rejected-*.json")],
        "unlimited_replacements": False})
    return all_cases

def recover_invalid_candidates():
    recovered = []
    for plan in planned_batches():
        directory = EXP / "calls" / plan["call_id"]
        completion = directory / "complete.json"
        target = directory / "recovered-invalid-candidates.json"
        if target.exists() or not completion.exists() or json.loads(completion.read_text(encoding="utf-8")).get("ok"):
            continue
        attempt_file = directory / "provider_attempts.json"
        attempts = json.loads(attempt_file.read_text(encoding="utf-8")) if attempt_file.exists() else []
        expected = [(c["id"], c["category"]) for c in plan["items"]]
        for attempt in attempts:
            try:
                content = attempt["choices"][0]["message"]["content"]
                candidate = json.loads(content)
                values = candidate["cases"]
                if [(c.get("id"), c.get("category")) for c in values] != expected:
                    continue
                for c in values:
                    c["generation_protocol_recovery"] = "Earliest syntactically valid provider JSON with the fixed 5 IDs/categories, after failed protocol attempts; original failure preserved; no claim of valid labels"
                dump(target, candidate)
                recovered.append({"call_id": plan["call_id"], "source_attempt": attempt["number"],
                                  "cases": [c["id"] for c in values], "selection_rule": "earliest_matching_json_not_best_labels"})
                break
            except Exception:
                continue
    dump(EXP / "data" / "invalid-protocol-recovery.json", recovered)
    print(json.dumps(recovered, ensure_ascii=False), flush=True)

def complete_missing_gold(materials):
    path = EXP / "data" / "cases-full-auto.jsonl"
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    targets = [c for c in cases if c.get("task") == "03" and c.get("category") == "L2" and not c.get("gold_sql")]
    if len(targets) > 10:
        raise RuntimeError("Bounded reference-completion limit is 10 labels in 2 calls; preserve excess as disputed")
    annotations = {}
    for offset in range(0, len(targets), 5):
        selected = targets[offset:offset+5]
        payload = {"source_materials": materials,
                   "cases_with_incomplete_reference": [{k:c.get(k) for k in ["id", "input", "scope", "business_basis", "reference_intent", "controller"]} for c in selected],
                   "constraint": "Only complete SQL for the already explicitly defined offline final intent. No new question, intent, binding choice, category, supplementary answer or business default. Disagreement remains disputed. No tested-system response exists."}
        result = model_call(f"complete-reference-sql-{offset//5+1:02}", "complete-reference-sql.txt", payload, SQLAnnotations)
        values = result.model_dump()["annotations"]
        if sorted(a["id"] for a in values) != sorted(c["id"] for c in selected):
            raise RuntimeError("SQL annotation did not preserve exact affected IDs")
        for a in values:
            annotations[a["id"]] = a
    for c in cases:
        if c["id"] in annotations:
            a = annotations[c["id"]]
            c["original_missing_gold_sql"] = c.get("gold_sql")
            c["gold_sql"] = a["gold_sql"]
            c["gold_completion_business_basis"] = a["business_basis"]
            c["gold_completion_issues"] = a["issues"]
            c["reference_version"] = "special-dev-v3-pre-v0-sql-completed"
            c["gold_revision_reason"] = "Generation returned empty/null L2 gold; separate context supplied SQL for unchanged already explicit offline final intent before any tested-system run. Original preserved. Both AI passes must still independently verify semantics."
        c["dataset_version"] = "special-dev-v3-full-before-v0"
    program_check(cases, "gold-completed-v3")
    dump(EXP / "data" / "gold-completion-manifest.json", {"created_at": now(), "affected_ids": list(annotations),
         "old_file": "data/cases-full-auto.jsonl", "new_file": "data/cases-gold-completed-v3-auto.jsonl",
         "originals_preserved": True, "max_completion_calls": 2, "no_question_or_target_rewrite": True,
         "change_is_pre_first_v0": True})
    print(json.dumps({"gold_sql_completed": len(annotations), "ids": list(annotations)}, ensure_ascii=False), flush=True)

def normalize_annotation_format():
    source = EXP / "data" / "cases-gold-completed-v3-auto.jsonl"
    cases = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    changes = []
    for c in cases:
        original = c.get("expected_bindings", [])
        bindings, predicates, aggregations, unresolved = [], [], [], []
        for record in original:
            operator = str(record.get("operator", "=")).upper()
            column = record.get("column", "")
            if operator == "GROUP BY" or operator.startswith(("COUNT", "SUM", "AVG", "MIN", "MAX")):
                aggregations.append(record)
            elif operator == "HALF-OPEN-RANGE":
                unresolved.append(record)
            elif column.endswith(".invoice_date"):
                predicates.append(record)
            elif isinstance(record.get("value"), str) and "待澄清" in record["value"]:
                unresolved.append(record)
            else:
                bindings.append(record)
        c["raw_expected_bindings"] = original
        c["expected_bindings"] = bindings
        c["expected_predicates"] = predicates
        c["expected_aggregations"] = aggregations
        c["expected_unresolved_constraints"] = unresolved
        c["binding_annotation_basis"] = "Deterministic format normalization only: value predicates, date predicates, aggregation/grouping and unresolved placeholders separately preserved. No condition/value inferred, no input/category/SQL/target changed."
        c["expected_final_intent"] = (c.get("controller") or {}).get("final_intent", c.get("reference_intent"))
        c["dataset_version"] = "special-dev-v4-format-normalized-before-v0"
        if predicates or aggregations or unresolved:
            changes.append({"id": c["id"], "predicate_count": len(predicates), "aggregation_count": len(aggregations), "unresolved_count": len(unresolved)})
    program_check(cases, "normalized-v4")
    dump(EXP / "data" / "format-normalization-manifest.json", {"created_at": now(), "source": "data/cases-gold-completed-v3-auto.jsonl",
         "output": "data/cases-normalized-v4-auto.jsonl", "source_sha256": digest(source), "changes": changes,
         "source_fields_fully_preserved": True, "no_question_sql_category_or_target_change": True})
    print(json.dumps({"normalized": len(cases), "changed_format": len(changes)}, ensure_ascii=False), flush=True)

def repair_pilot(materials):
    original = [json.loads(line) for line in (EXP / "data" / "cases-pilot-auto.jsonl").read_text(encoding="utf-8").splitlines() if line]
    issues = {
        "sp01-03": "德国发票没有说账单国/住址国；请生成明确同一国家语义的alias案例，不暗定客户所在地。",
        "sp01-06": "Yin Ma是新造pinyin与Iron Maiden无合法唯一依据；请改为已approved中文国名的清晰拼音表达，不编新别名。",
        "sp03-04": "L1却明确写Top10又missing top_n矛盾；若用Top10技术默认应原题未给数量，basis明确计划来源，默认执行后missing_conditions应为空。",
        "sp03-06": "gold_sql与business_basis为空。销售额已已审明确定义，不应把metric也列缺失；缺时期同比L2需要具体后续目标及真实SQL。",
        "sp03-07": "gold_sql与business_basis为空；美国销售额未明确住址/账单国，不能无依据选择。请生成清楚原始分子语义但缺分母的L2，合法补充分母后的SQL。",
        "sp03-08": "gold_sql与business_basis为空；缺对象不globaldefault；补充只回答被问对象，若同时说明金额须明确该语义是补充条件，真实最终SQL。",
        "sp03-09": "gold_sql与business_basis为空；摇滚有Rock/Rock And Roll，不应初次expected_bindings唯一选Rock；允许解释全保留，补充才绑定，真实最终SQL。",
        "sp03-10": "客户数已明确customer对象，不能仅因出现国家就误标缺region_scope；请生成真正缺关键条件的L2，保留原类别配额，真实完整gold与basis。",
    }
    repairs = {}
    ids = list(issues)
    for offset in range(0, len(ids), 5):
        selected = [c for c in original if c["id"] in ids[offset:offset+5]]
        payload = {"source_materials": materials, "original_candidates": selected,
                   "specific_evidence_issues": {c["id"]: issues[c["id"]] for c in selected},
                   "correction_limit": "One pre-V0 pilot correction round only; preserve IDs/categories/tasks and full required fields. Realistically fix evidence errors, do not force a pass.",
                   "required_fields": sorted(REQUIRED)}
        result = model_call(f"repair-pilot-{offset//5+1:02}", "repair-pilot.txt", payload, CaseBatch)
        expected = sorted((c["id"], c["category"], c["task"]) for c in selected)
        actual = sorted((c.get("id"), c.get("category"), c.get("task")) for c in result.cases)
        if actual != expected:
            raise RuntimeError("Pilot correction violates fixed ID/category/task contract")
        for c in result.cases:
            c["generation_call_id"] = f"repair-pilot-{offset//5+1:02}"
            c["revision_reason"] = issues[c["id"]]
            repairs[c["id"]] = c
    dump(EXP / "data" / "pilot-repairs-v2.json", repairs)
    revised = [{**c, **repairs.get(c["id"], {})} for c in original]
    for c in revised:
        if c["id"] in repairs:
            c["reference_version"] = "special-dev-v2-pilot-repaired-before-v0"
    program_check(revised, "pilot-v2")
    dump(EXP / "data" / "pilot-revision-manifest.json", {"created_at": now(), "reason": "Pre-V0 one bounded correction round after actual pilot checks; originals and original model attempts preserved", "affected_ids": ids,
         "original_file": "data/cases-pilot-generated.jsonl", "revised_file": "data/cases-pilot-v2-auto.jsonl", "extra_logical_calls": 2, "max_more_repair_rounds": 0})

def review(materials):
    completed = EXP / "data" / "cases-gold-completed-v3-auto.jsonl"
    normalized = EXP / "data" / "cases-normalized-v4-auto.jsonl"
    path = normalized if normalized.exists() else completed if completed.exists() else EXP / "data" / "cases-full-auto.jsonl"
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    check_path = EXP / "checks" / ("program-normalized-v4.json" if normalized.exists() else "program-gold-completed-v3.json" if completed.exists() else "program-full.json")
    checks = json.loads(check_path.read_text(encoding="utf-8"))
    by_check = {c["id"]: c for c in checks["checks"]}
    by_review = {1: {}, 2: {}}
    for pass_id in (1, 2):
        for start in range(0, len(cases), 5):
            batch = cases[start:start+5]
            # Pass2 receives original cases and actual approved sources, never pass1
            # judgments. Each call is a fresh two-message JsonLLM context.
            clean = [{k: v for k, v in c.items() if k not in {"ai_status", "ai_reviews", "scorable"}} for c in batch]
            payload = {"source_materials": materials, "cases": clean,
                       "actual_program_checks": [by_check[c["id"]] for c in batch],
                       "independent_pass": pass_id, "other_pass_judgments": "withheld"}
            result = model_call(f"review-p{pass_id}-{start//5+1:02}", f"review-p{pass_id}.txt", payload, ReviewBatch)
            review_values = result.model_dump()["reviews"]
            if sorted(c.get("id") for c in review_values) != sorted(c["id"] for c in batch):
                raise RuntimeError("Reviewer missing or duplicating an item")
            for item in review_values:
                by_review[pass_id][item["id"]] = item
            print(json.dumps({"review_pass": pass_id, "completed_cases": start+len(batch)}, ensure_ascii=False), flush=True)
        dump(EXP / "checks" / f"ai-pass-{pass_id}.json", {"review_type": "AI", "independent_call_context": True,
             "no_human_signature": True, "reviews": list(by_review[pass_id].values())})
    for case in cases:
        reviews = [by_review[1][case["id"]], by_review[2][case["id"]]]
        good = all(r.get("verdict") == "pass" and not r.get("issues") and
                   all(r.get(field) in {"pass", "not_applicable"} for field in
                       ("semantic_sql_check", "classification_check", "binding_check", "controller_check"))
                   for r in reviews)
        case["ai_reviews"] = reviews
        case["ai_status"] = "ai_suggested_pass_two_contexts" if good else "disputed_or_evidence_insufficient"
        case["scorable"] = case["auto_status"] == "passed" and good
    reviewed_name = "cases-v4-reviewed.jsonl" if normalized.exists() else "cases-v3-reviewed.jsonl" if completed.exists() else "cases-v1-reviewed.jsonl"
    jsonl(EXP / "data" / reviewed_name, cases)
    summary = {"created_at": now(), "dataset_total": len(cases),
               "scorable": sum(c["scorable"] for c in cases), "pending_confirmation": sum(not c["scorable"] for c in cases),
               "all_human_pending": len(cases), "by_task": {t: {"total": sum(c["task"] == t for c in cases),
               "scorable": sum(c["task"] == t and c["scorable"] for c in cases)} for t in QUOTAS},
               "ai_is_not_human_acceptance": True, "historical_exposure_disclosure":
               "Root historical context may have seen holdout; this new context does not erase that exposure. All 60 are synthetic development cases, not independent generalization tests."}
    dump(EXP / "reports" / "data-preparation-summary.json", summary)
    dump(EXP / "data" / "freeze-proposal.json", {"status": "proposal_awaiting_root_formal_v0_freeze",
         "created_at": now(), "label_file": "data/" + reviewed_name, "label_sha256": digest(EXP / "data" / reviewed_name),
         "source_manifest_sha256": digest(EXP / "materials" / "source_manifest.json"),
         "scoring_protocol": "reports/scoring-protocol-draft.md", **summary})
    print(json.dumps(summary, ensure_ascii=False), flush=True)

def usage():
    attempts = []
    for p in sorted((EXP / "calls").glob("*/provider_attempts.json")):
        for a in json.loads(p.read_text(encoding="utf-8")):
            attempts.append({"call_id": p.parent.name, **a})
    tokens = Counter()
    for a in attempts:
        for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
            tokens[k] += a.get("usage", {}).get(k, 0)
    summary = {"provider_requests": len(attempts), "logical_calls": len({a["call_id"] for a in attempts}),
               "actual_tokens": dict(tokens), "provider_latency_ms_sum": sum(a["latency_ms"] for a in attempts),
               "errors": [{"call_id": a["call_id"], "attempt": a["number"], "error": a["error"]} for a in attempts if not a["ok"]],
               "cost": "not_available_do_not_estimate", "model_usage_is_actual": True}
    summary["logical_protocol_failures"] = [
        {"call_id": p.parent.name, **json.loads(p.read_text(encoding="utf-8"))}
        for p in sorted((EXP / "calls").glob("*/complete.json"))
        if not json.loads(p.read_text(encoding="utf-8")).get("ok")]
    dump(EXP / "reports" / "preparation-usage.json", summary)
    return summary

def final_source_guards():
    """Generic approved-source checks beyond the AI suggestions; no label rewrite."""
    source = EXP / "data" / "cases-v4-reviewed.jsonl"
    cases = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    aliases = list(csv.DictReader((ROOT / "data/aliases/aliases-d2-reviewed.csv").open(encoding="utf-8-sig")))
    pending = {(a["alias"], a["column"], a["standard_value"]) for a in aliases if a["review_status"] == "pending"}
    results = []
    for c in cases:
        question = c["input"]
        explicit_metric = bool(re.search(r"购买数量|销量|销售额|金额|歌单|收录|quantity|revenue", question, re.I))
        popular_default = any(w in question for w in ("最受欢迎", "最热门", "最火", "热门曲目", "热门歌曲", "卖得最好")) and not explicit_metric
        customer_default = "客户" in question and any(w in question for w in ("谁买得最多", "买得最多")) and not explicit_metric
        explicit_n = bool(re.search(r"(?:top\s*|前\s*)\d+|\d+\s*(?:首|名|个)\s*(?:曲目|客户|艺术家|歌)|哪首|是谁|哪个", question, re.I))
        ranking = bool(re.search(r"排名|排行|前\s*\d+|top\s*\d+", question, re.I))
        top_default = ranking and not explicit_n
        issues = []
        if c["task"] == "03" and c["category"] == "L0" and (popular_default or customer_default):
            issues.append("L0_uses_registered_default: approved defaults require L1 disclosure, not unqualified L0")
        if c["task"] == "03" and c["category"] == "L1" and not (popular_default or customer_default or top_default):
            issues.append("L1_has_no_applicable_registered_default: explicit metric/object/count do not invoke an omitted-count default")
        for b in c.get("expected_bindings", []):
            values = b.get("value") if isinstance(b.get("value"), list) else [b.get("value")]
            surface = b.get("surface")
            for value in values:
                if isinstance(value, str) and (surface, b.get("column"), value) in pending:
                    issues.append("pending_alias_used_as_reference_candidate:" + str(surface) + ":" + b["column"])
            if "流派" in question and not any(w in question for w in ("艺术家", "乐队", "artist")) and b.get("column") == "artist.name":
                issues.append("explicit_genre_scope_conflicts_with_artist_candidate")
        controller = c.get("controller") or {}
        final = controller.get("final_intent") or {}
        final_genre = final.get("genre")
        if isinstance(final_genre, dict):
            final_genre = final_genre.get("value") or final_genre.get("name") or final_genre.get("standard_value")
        if isinstance(final_genre, str):
            for key, supplement in controller.get("allowed_user_supplements", {}).items():
                if key not in {"value", "genre", "genre_value"}:
                    continue
                value = supplement.get("value")
                if isinstance(value, dict):
                    value = value.get("value") or value.get("name") or value.get("standard_value")
                if isinstance(value, str) and value != final_genre:
                    issues.append("controller_genre_supplement_conflicts_with_explicit_final_target:" + key)
        c["final_source_guard_issues"] = list(dict.fromkeys(issues))
        if issues:
            c["auto_status_before_final_source_guard"] = c["auto_status"]
            c["auto_status"] = "disputed"
            c["auto_issues"] = list(dict.fromkeys(c.get("auto_issues", []) + issues))
            c["scorable"] = False
        c["dataset_version"] = "special-dev-v6-source-and-controller-guard-before-v0"
        results.append({"id": c["id"], "issues": c["final_source_guard_issues"]})
    target = EXP / "data" / "cases-v6-reviewed.jsonl"
    jsonl(target, cases)
    dump(EXP / "checks" / "final-source-guards.json", {"checked_at": now(),
         "source_rules": ["data/rules/metric_definitions.json popular/customer distinct-object defaults",
                          "notes/references/d3-and-special/方案.md 3.6.4 L0/L1 and ranking top_n=10",
                          "data/aliases/aliases-d2-reviewed.csv pending disabled"],
         "generic_guards_no_case_id_rules": True, "reviews": results})
    summary = {"created_at": now(), "dataset_total": len(cases), "unique_inputs": len({"".join(c["input"].casefold().split()) for c in cases}),
               "scorable": sum(c["scorable"] for c in cases), "pending_confirmation": sum(not c["scorable"] for c in cases),
               "all_human_pending": len(cases), "scorable_by_task": {t:sum(c["task"] == t and c["scorable"] for c in cases) for t in QUOTAS},
               "intended_categories": {t:dict(Counter(c["category"] for c in cases if c["task"] == t)) for t in QUOTAS},
               "scorable_categories": {t:dict(Counter(c["category"] for c in cases if c["task"] == t and c["scorable"])) for t in QUOTAS},
               "disputed_ids": [c["id"] for c in cases if not c["scorable"]], "source_guard_affected_ids": [r["id"] for r in results if r["issues"]],
               "ai_is_not_human_acceptance": True,
               "historical_exposure_disclosure": "Root historical context may have seen holdout; this context does not erase historical exposure. All 60 are synthetic development cases, not independent generalization tests."}
    dump(EXP / "reports" / "data-preparation-summary.json", summary)
    dump(EXP / "data" / "freeze-proposal.json", {"status": "proposal_awaiting_root_formal_v0_freeze", "created_at": now(),
         "label_file": "data/cases-v6-reviewed.jsonl", "label_sha256": digest(target),
         "source_manifest_sha256": digest(EXP / "materials" / "source_manifest.json"),
         "scoring_protocol": "reports/scoring-protocol-draft.md", "scoring_protocol_sha256": digest(EXP / "reports" / "scoring-protocol-draft.md"), **summary})
    print(json.dumps(summary, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["setup", "pilot", "repair-pilot", "recover-invalid", "full", "complete-gold", "normalize", "review", "final-guards", "usage"])
    args = parser.parse_args()
    try:
        if args.stage == "usage":
            print(json.dumps(usage(), ensure_ascii=False))
        elif args.stage == "recover-invalid":
            recover_invalid_candidates()
        elif args.stage == "final-guards":
            final_source_guards()
        else:
            materials = setup()
            if args.stage in ("pilot", "full"):
                generate(args.stage, materials)
            elif args.stage == "repair-pilot":
                repair_pilot(materials)
            elif args.stage == "complete-gold":
                complete_missing_gold(materials)
            elif args.stage == "normalize":
                normalize_annotation_format()
            elif args.stage == "review":
                review(materials)
    finally:
        if (EXP / "calls").exists():
            usage()
