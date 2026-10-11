"""Conservative offline scorer: execution equality never proves intent equality."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from math import sqrt
from pathlib import Path

from common import ROOT, utcnow, write_new

UNSET = object()


def binding_key(item: dict):
    return (item.get("column"), item.get("operator", "="), json.dumps(item.get("value"), ensure_ascii=False, sort_keys=True))


def _binding_evidence(response: dict) -> list[dict]:
    # Actual state contract takes precedence over the current linker's transient candidates.
    intent = response.get("intent") or {}
    if "filters" in intent:
        return intent["filters"] or []
    return (response.get("metadata", {}).get("nlu") or {}).get("bindings") or []


def score_bindings(case: dict, response: dict):
    expected = {binding_key(item) for item in case.get("expected_bindings") or []}
    actual = {binding_key(item) for item in _binding_evidence(response)}
    if case.get("category") == "multi_candidate":
        unresolved = (response.get("intent") or {}).get("unresolved") or []
        candidates = []
        for item in unresolved:
            candidates.extend(item.get("candidates") or [])
            for option in item.get("options") or []:
                patch = option.get("patch") or {}
                if patch.get("op") == "resolve_value":
                    candidates.append({"column": patch.get("column"), "standard_value": patch.get("value")})
        nlu = response.get("metadata", {}).get("nlu") or {}
        mentions = nlu.get("ambiguous") or [item for item in nlu.get("mentions", []) if item.get("status") == "ambiguous"]
        for item in mentions:
            candidates.extend(item.get("candidates") or [])
        retained = {(item.get("column"), "=", json.dumps(item.get("standard_value", item.get("canonical_value", item.get("value"))), ensure_ascii=False, sort_keys=True)) for item in candidates}
        good = response.get("status") == "NEEDS_CLARIFICATION" and not actual and expected <= retained
        return {"correct": good, "mode": "candidate_preservation", "expected": sorted(expected), "retained": sorted(retained), "bound": sorted(actual)}
    if case.get("category") == "explicit_absent" and not actual:
        # Unknown literals may legitimately remain outside the resolved value index.
        proof = semantic_check(case.get("gold_sql"), response, case.get("gold_result"))
        return {"correct": True if proof["correct"] is True else None, "mode": "unknown_literal_sql_contract", "expected": sorted(expected), "actual": []}
    return {"correct": expected == actual, "mode": "exact_column_operator_value", "expected": sorted(expected), "actual": sorted(actual),
            "missing": sorted(expected - actual), "extra": sorted(actual - expected)}


def sql_contract(sql: str, *, benign_limit: int | None = None) -> dict:
    import sqlglot
    from sqlglot import exp
    from sqlglot.optimizer.qualify import qualify
    from sqlglot.optimizer.scope import traverse_scope
    from sqlglot.schema import MappingSchema
    from qa_agent.sql.catalog import load_catalog
    catalog = load_catalog(ROOT / "data/catalog/chinook.yaml")
    tree = sqlglot.parse_one(sql, read="postgres")
    if not isinstance(tree, exp.Query):
        raise ValueError("Only SELECT query ASTs can be scored")
    tree = qualify(tree, dialect="postgres", db="public",
                   schema=MappingSchema(catalog.sqlglot_schema(), dialect="postgres", normalize=False),
                   allow_partial_qualification=False, validate_qualify_columns=True)
    for scope in traverse_scope(tree):
        physical = {alias: source for alias, (_, source) in scope.selected_sources.items() if isinstance(source, exp.Table)}
        if len({source.name for source in physical.values()}) != len(physical):
            raise ValueError("Self-join equivalence requires semantic review")
        projections = {item.alias: item.this.copy() for item in scope.expression.selects if isinstance(item, exp.Alias)}
        order = scope.expression.args.get("order")
        if order:
            for node in list(order.find_all(exp.Column)):
                if not node.table and node.name in projections:
                    node.replace(projections[node.name].copy())
        # Only scope-owned physical references are normalized; derived scopes retain lineage structure.
        for column in scope.columns:
            source = physical.get(column.table)
            if source is not None:
                column.set("table", exp.to_identifier(source.name, quoted=False))
                column.set("db", None)
                column.set("catalog", None)
        for source in physical.values():
            source.set("alias", None)
            source.set("db", None)
            source.set("catalog", None)
        for item in list(scope.expression.selects):
            if isinstance(item, exp.Alias):
                item.replace(item.this.copy())
    for ident in tree.find_all(exp.Identifier):
        ident.set("quoted", False)
    if benign_limit and tree.args.get("limit") and not tree.args.get("offset"):
        literal = tree.args["limit"].expression
        if isinstance(literal, exp.Literal) and not literal.is_string and int(literal.this) == benign_limit:
            tree.set("limit", None)
    atoms = Counter()
    for node in tree.walk():
        if isinstance(node, (exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE, exp.In, exp.Between, exp.Like, exp.ILike)):
            atoms[node.sql(dialect="postgres")] += 1
    return {"ast": tree.sql(dialect="postgres", normalize=True), "predicates": dict(sorted(atoms.items())),
            "aggregates": sorted(node.sql(dialect="postgres") for node in tree.find_all(exp.AggFunc)),
            "tables": sorted({table.name for table in tree.find_all(exp.Table)}),
            "limit": tree.args.get("limit").sql() if tree.args.get("limit") else None}


def semantic_check(gold_sql: str | None, response: dict, gold_result: dict | None):
    if not gold_sql:
        return {"correct": None, "status": "AI_pending", "reason": "No deterministic SQL contract for this case"}
    actual = response.get("sql")
    if not actual:
        return {"correct": False, "status": "failed", "reason": "No actual SQL"}
    try:
        golden = sql_contract(gold_sql)
        limit = response.get("metadata", {}).get("max_rows")
        # The existing validator exposes only default_limit_added; recognize the frozen configured cap.
        if limit is None:
            for step in response.get("steps") or []:
                if step.get("name") == "config_check":
                    limit = (step.get("output_summary") or {}).get("max_rows")
        benign = limit if golden["limit"] is None and isinstance(limit, int) and gold_result and gold_result.get("row_count", limit) < limit and not response.get("metadata", {}).get("truncated") else None
        observed = sql_contract(actual, benign_limit=benign)
        if golden["ast"] == observed["ast"]:
            return {"correct": True, "status": "confirmed", "reason": "Qualified SQL AST matches frozen semantic contract", "gold": golden, "actual": observed}
        # Alternative SQL can be equivalent; automatic comparison is intentionally a proof lower bound.
        return {"correct": None, "status": "AI_pending", "reason": "Qualified AST differs; semantic equivalence needs independent review",
                "predicate_match": golden["predicates"] == observed["predicates"], "gold": golden, "actual": observed}
    except Exception as exc:
        return {"correct": None, "status": "AI_pending", "reason": f"AST equivalence unavailable: {type(exc).__name__}: {str(exc)[:300]}"}


def result_check(gold_result: dict | None, response: dict, expected_intent: dict, gold_sql: str | None = None):
    from eval.metrics import compare_results
    if gold_result is None:
        return {"correct": None, "reason": "Saved gold_result unavailable"}
    if response.get("status") not in {"SUCCEEDED", "EMPTY_RESULT"}:
        return {"correct": False, "reason": "No successful query result"}
    columns = response.get("metadata", {}).get("result_columns")
    table = response.get("table")
    if table is None:
        return {"correct": False, "reason": "Actual table missing (NULL, zero, and empty result remain distinct)"}
    names = gold_result.get("columns") or []
    rows = gold_result.get("rows", gold_result.get("table", []))
    # Decimal JSON values are strings: declare numeric only where all observed gold values prove it,
    # or the parser/catalog identify a numeric aggregate. No universal numeric-string coercion.
    numeric = []
    if gold_sql:
        try:
            import sqlglot
            from sqlglot import exp
            expressions = sqlglot.parse_one(gold_sql, read="postgres").selects
            proven_numeric = (exp.Count, exp.Sum, exp.Avg, exp.Add, exp.Sub, exp.Mul, exp.Div)
            numeric.extend(index for index, item in enumerate(expressions) if index < len(names)
                           and isinstance(item.this if isinstance(item, exp.Alias) else item, proven_numeric))
        except Exception:
            pass
    for index, name in enumerate(names):
        values = [row[index] for row in rows if isinstance(row, list) and row[index] is not None]
        if values and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
            numeric.append(index)
    ordered = expected_intent.get("task_type") == "ranking" or expected_intent.get("top_n") is not None or bool(expected_intent.get("tie_breaker"))
    compared = compare_results(rows, table, ordered=ordered, expected_columns=names, actual_columns=columns,
                               numeric_columns=numeric)
    return {"correct": compared.matched, **compared.as_dict(), "ordered": ordered, "numeric_columns": numeric,
            "rounding": "none; exact numeric values", "gold_truncated": gold_result.get("truncated"),
            "actual_truncated": response.get("metadata", {}).get("truncated")}


def _successful(response):
    return response.get("status") in {"SUCCEEDED", "EMPTY_RESULT"}


def score_query(case, response, *, gold_sql=UNSET, gold_result=UNSET, expected_intent=None):
    expected_intent = expected_intent if expected_intent is not None else case.get("expected_final_intent") or {}
    gold_sql = case.get("gold_sql") if gold_sql is UNSET else gold_sql
    gold_result = case.get("gold_result") if gold_result is UNSET else gold_result
    semantic = semantic_check(gold_sql, response, gold_result)
    result = result_check(gold_result, response, expected_intent, gold_sql)
    complete = False if not _successful(response) or result["correct"] is False or semantic["correct"] is False else True if semantic["correct"] is True and result["correct"] is True else None
    return {"semantic_preservation": semantic, "result": result, "complete": complete}


def case_score(case: dict, checkpoint: dict, post_results: dict | None = None):
    turns = checkpoint.get("turns") or []
    target = [item for item in turns if item.get("phase") in {"initial", "clarification"}]
    first = next((item.get("response") or {} for item in turns if item.get("phase") == "initial"), {})
    final = target[-1].get("response") or {} if target else {}
    scorable = case.get("scorable", case.get("scoreable", False)) is True
    initial_bindings = score_bindings(case, first)
    candidate_only = case.get("task") == "01" and case.get("category") == "multi_candidate" and not case.get("controller")
    if candidate_only:
        complete = initial_bindings["correct"]
        query = {"complete": complete, "semantic_preservation": {"correct": complete, "reason": "Preserved candidate-only clarification contract"}, "result": {"correct": None, "reason": "Initial clarification has no unique gold query"}}
    else:
        query = score_query(case, final)
        complete = query["complete"]
    posts = []
    expected_posts = (case.get("controller") or {}).get("post_completion_turns") or []
    actual_posts = [item for item in turns if item.get("phase") == "post_completion"]
    for index, post in enumerate(expected_posts):
        response = actual_posts[index].get("response") or {} if index < len(actual_posts) else {}
        golden = post.get("gold_result") or (post_results or {}).get(case["id"], {}).get(f"post_completion_{index+1}")
        posts.append({"index": index + 1, "message": post["message"], "executed": index < len(actual_posts),
                      **score_query(case, response, gold_sql=post.get("gold_sql"), gold_result=golden,
                                    expected_intent=post.get("expected_intent") or {})})
    if any(item["complete"] is False for item in posts):
        complete = False
    elif complete is True and any(item["complete"] is None for item in posts):
        complete = None
    if checkpoint.get("outcome") not in {"finished", "candidate_only_clarification"}:
        complete = False
    clarify = first.get("metadata", {}).get("clarify") or first.get("metadata", {}).get("clarification") or {}
    level = clarify.get("level") or first.get("metadata", {}).get("level")
    asked = first.get("status") == "NEEDS_CLARIFICATION"
    expected_level = case.get("category") if case.get("task") == "03" else None
    false_clarification = asked if expected_level in {"L0", "L1"} else None
    necessary_recall = asked if expected_level == "L2" else None
    # Level-only metadata cannot demonstrate success/default application/switch support.
    default_declared = bool(first.get("intent", {}).get("assumptions") or clarify.get("assumptions"))
    switches = clarify.get("switch") or first.get("metadata", {}).get("switch")
    l1_behavior = bool(_successful(first) and default_declared and switches and switches.get("options")) if expected_level == "L1" else None
    if l1_behavior is False:
        complete = False
    semantics = [query["semantic_preservation"]["correct"]] + [item["semantic_preservation"]["correct"] for item in posts]
    preserved = False if False in semantics else True if all(item is True for item in semantics) else None
    overcorrect = False if preserved is True and initial_bindings["correct"] is not False else True if initial_bindings["correct"] is False and case.get("category") in {"multi_candidate", "explicit_absent"} else None
    return {"id": case["id"], "task": case["task"], "category": case["category"], "scorable": scorable,
            "initial_status": first.get("status"), "final_status": final.get("status"), "observed_initial_level": level,
            "initial_level_correct": level == expected_level if expected_level else None,
            "binding_correctness": initial_bindings, "query": query, "post_completion": posts,
            "necessary_clarification_recall": necessary_recall, "false_clarification": false_clarification,
            "clarification_effectiveness": (None if complete is None else bool(complete and checkpoint.get("clarification_count", 0) > 0)) if expected_level == "L2" else None,
            "condition_preservation": preserved, "overcorrection": overcorrect, "l1_default_switch_behavior": l1_behavior,
            "automatic_complete": complete if scorable else None, "pending_annotation": not scorable,
            "outcome": checkpoint.get("outcome", "not_started"), "controller_events": checkpoint.get("controller_events", []),
            "semantic_review_status": "AI_pending" if complete is None and scorable else "not_required"}


def wilson(correct: int, denominator: int):
    if not denominator:
        return None
    z = 1.959963984540054
    rate = correct / denominator
    scale = 1 + z*z/denominator
    center = (rate + z*z/(2*denominator)) / scale
    margin = z * sqrt(rate*(1-rate)/denominator + z*z/(4*denominator*denominator)) / scale
    return [max(0, center-margin), min(1, center+margin)]


def aggregate(scores: list[dict], checkpoints: list[dict]):
    groups = defaultdict(list)
    for item in scores:
        groups["all"].append(item)
        groups[f"task:{item['task']}"] .append(item)
        groups[f"task:{item['task']}/category:{item['category']}"] .append(item)
    summaries = {}
    for key, items in groups.items():
        scoreable = [item for item in items if item["scorable"]]
        confirmed = sum(item["automatic_complete"] is True for item in scoreable)
        pending = sum(item["automatic_complete"] is None for item in scoreable)
        summaries[key] = {"total_tasks": len(items), "scorable_tasks": len(scoreable), "pending_annotation": len(items)-len(scoreable),
                          "confirmed_correct": confirmed, "automatic_failed": len(scoreable)-confirmed-pending,
                          "semantic_AI_pending": pending, "correct_over_total_tasks": f"{confirmed}/{len(items)}",
                          "correct_over_scorable_tasks": f"{confirmed}/{len(scoreable)}",
                          "confirmed_correct_lower_bound_wilson_95": wilson(confirmed, len(scoreable)),
                          "scoring_coverage": len(scoreable)/len(items) if items else 0,
                          "outcomes": dict(Counter(item["outcome"] for item in items))}
        metrics = {}
        for metric in ("binding_correctness", "initial_level_correct", "necessary_clarification_recall", "false_clarification",
                       "clarification_effectiveness", "condition_preservation", "overcorrection", "l1_default_switch_behavior"):
            applicable = [item for item in scoreable if
                          (item["task"] == "01" if metric in {"binding_correctness", "overcorrection"} else
                           item["task"] == "03" and item["category"] == "L2" if metric in {"necessary_clarification_recall", "clarification_effectiveness"} else
                           item["task"] == "03" and item["category"] in {"L0", "L1"} if metric == "false_clarification" else
                           item["task"] == "03" and item["category"] == "L1" if metric == "l1_default_switch_behavior" else
                           item["task"] == "03" if metric == "initial_level_correct" else True)]
            values = [(item[metric]["correct"] if metric == "binding_correctness" else item[metric]) for item in applicable]
            observed = [value for value in values if value is not None]
            positives = sum(value is True for value in observed)
            metrics[metric] = {"positive": positives, "applicable_task_denominator": len(values), "observed_denominator": len(observed), "unresolved": len(values)-len(observed),
                               "positive_over_task_denominator": f"{positives}/{len(values)}", "observed_positive_over_observed_denominator": f"{positives}/{len(observed)}",
                               "confirmed_positive_lower_bound_wilson_95": wilson(positives, len(values))}
        summaries[key]["metrics"] = metrics
    responses = [turn.get("response") or {} for checkpoint in checkpoints for turn in checkpoint.get("turns", [])]
    llm_steps = [step for response in responses for step in response.get("steps", []) if step.get("name") == "llm"]
    usage = Counter()
    usage_missing = 0
    for step in llm_steps:
        observed = (step.get("output_summary") or {}).get("usage") or {}
        usage_missing += not bool(observed)
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            if isinstance(observed.get(key), int):
                usage[key] += observed[key]
    return {"created_at": utcnow(), "claim": "本轮合成开发集上的自动评测／AI预审结果；AST未证明的等价SQL保留AI_pending",
            "denominator_policy": "All 60 retained, including pending labels, timeout, unimplemented, API error, controller_unanswered and unfinished tasks",
            "groups": summaries, "api_post_requests": sum(len(checkpoint.get("turns", [])) for checkpoint in checkpoints),
            "api_ambiguous_delivery_requests": sum(checkpoint.get("outcome") == "ambiguous_delivery" for checkpoint in checkpoints),
            "prepared_requests_without_response": sum(bool(checkpoint.get("interrupted_request")) for checkpoint in checkpoints),
            "provider_attempts_observed_in_api_steps": len(llm_steps), "provider_token_usage_observed": dict(usage),
            "provider_captures_archived": sum(turn.get("provider_captures_archived", 0) for checkpoint in checkpoints for turn in checkpoint.get("turns", [])),
            "provider_attempts_without_usage": usage_missing, "offline_generation_review_calls_included": False,
            "cost": "not estimated", "api_latency_ms_observed": sum(turn.get("latency_ms", 0) for checkpoint in checkpoints for turn in checkpoint.get("turns", [])),
            "CI_interpretation": "Descriptive Wilson interval for confirmed-correct lower bound on fixed synthetic dev tasks; no generalization/significance claim"}


def load_post_results(path: Path | None):
    if not path:
        return {}
    # Only an explicitly named dev checker artifact, never unified/holdout content.
    if path.name != "program-normalized-v4.json":
        raise ValueError("Unsupported post-completion result artifact")
    if path.resolve().parent != ROOT / "eval/experiments/after_d2_01_03/checks":
        raise ValueError("Only this experiment's saved dev checker artifact is allowed")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    records = value.get("checks", value.get("cases", value.get("results", []))) if isinstance(value, dict) else value
    if isinstance(records, dict):
        records = [{"id": key, **item} for key, item in records.items()]
    return {item["id"]: {check["label"]: check["result"] for check in item.get("sql_checks", []) if str(check.get("label", "")).startswith("post_completion_") and check.get("result")}
            for item in records}


def score_run(cases: list[dict], run_dir: Path, output: Path, post_results_path: Path | None = None):
    checkpoints = []
    scores = []
    post_results = load_post_results(post_results_path)
    for case in cases:
        path = run_dir / "cases" / case["id"] / "checkpoint.json"
        checkpoint = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"turns": [], "outcome": "not_started"}
        checkpoints.append(checkpoint)
        scores.append(case_score(case, checkpoint, post_results))
    from common import digest
    manifest = json.loads((run_dir / "run-manifest.json").read_text(encoding="utf-8"))
    write_new(output, {"summary": aggregate(scores, checkpoints), "cases": scores,
                       "labels_sha256": manifest["labels_sha256"], "freeze_sha256": manifest["freeze_sha256"], "version": manifest["version"],
                       "scoring_files_sha256": {str(path.relative_to(ROOT)): digest(path) for path in (Path(__file__), ROOT / "eval/metrics.py", Path(__file__).with_name("common.py"))}})
    return output
