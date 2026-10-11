"""Real HTTP runner, with a formally frozen gate and non-replaying checkpoints."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from time import perf_counter
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from common import ROOT, HERE, digest, history_messages, load_cases, request_payload, safe, utcnow, write_new
from controller import next_answer
from scorer import score_run
from snapshot import service_evidence, snapshot, verify_freeze


def _save_checkpoint(path: Path, value: dict):
    # Only this run's mutable progress is replaced; request/response evidence uses exclusive create.
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(safe(value), ensure_ascii=False, indent=2) + "\n")
        handle.flush()
        import os
        os.fsync(handle.fileno())
    temporary.replace(path)


def _response_from_raw(raw: dict):
    if raw.get("network_error"):
        return {"status": "FAILED", "error": {"code": raw["network_error"], "message": raw.get("message", "")},
                "metadata": {"runner_transport_error": True}, "steps": []}
    try:
        value = json.loads(raw.get("body", ""))
        if not isinstance(value, dict):
            raise ValueError("Response is not a JSON object")
        if raw.get("http_status", 500) >= 400:
            return {"status": "FAILED", "error": {"code": "http_error", "message": str(value.get("detail", value))[:1200]},
                    "metadata": {"http_status": raw["http_status"]}, "steps": [], "actual_error_body": value}
        return value
    except Exception as exc:
        return {"status": "FAILED", "error": {"code": "invalid_api_json", "message": str(exc)}, "metadata": {}, "steps": []}


def archive_provider_captures(response: dict, turn_dir: Path) -> dict:
    """Copy only server-referenced observational records from the two explicit safe capture roots."""
    items = []
    for index, step in enumerate(response.get("steps") or []):
        if step.get("name") != "llm":
            continue
        reference = (step.get("output_summary") or {}).get("provider_capture")
        if not reference:
            items.append({"step": index, "status": "capture_missing"})
            continue
        source = (ROOT / reference).resolve()
        allowed = [ROOT / ".runtime/provider-captures", HERE / "provider-captures"]
        if not any(source.is_relative_to(directory.resolve()) for directory in allowed) or not re.fullmatch(r"[0-9a-fA-F-]{36}\.json", source.name):
            items.append({"step": index, "status": "capture_path_rejected", "reference": reference})
            continue
        try:
            capture = json.loads(source.read_text(encoding="utf-8"))
            if capture.get("trace_id") != response.get("trace_id"):
                raise ValueError("Capture trace_id mismatch")
            target = turn_dir / "provider" / source.name
            if not target.exists():
                write_new(target, safe(capture))
            items.append({"step": index, "status": "archived", "source": reference,
                          "source_sha256": digest(source), "copy": str(target.relative_to(turn_dir)), "copy_sha256": digest(target)})
        except Exception as exc:
            items.append({"step": index, "status": "capture_unavailable", "error": type(exc).__name__})
    manifest = turn_dir / "provider-evidence.json"
    if not manifest.exists():
        write_new(manifest, {"trace_id": response.get("trace_id"), "records": items})
    return {"provider_attempts": len(items), "provider_captures_archived": sum(item["status"] == "archived" for item in items),
            "provider_evidence_file": str(manifest.relative_to(turn_dir))}


def recover_case(case_dir: Path, state: dict):
    """Recover response evidence before choosing the next user turn, without another POST."""
    known = {turn["index"] for turn in state["turns"]}
    for path in sorted((case_dir / "turns").glob("*/request.json")) if (case_dir / "turns").exists() else []:
        record = json.loads(path.read_text(encoding="utf-8"))
        index = record["index"]
        if index in known:
            continue
        response_path = path.parent / "response.raw.json"
        if not response_path.exists():
            # The process can die after bytes reached the server. Automatic retry could apply the patch twice.
            state["outcome"] = "ambiguous_delivery"
            state["interrupted_request"] = str(path.relative_to(case_dir))
            return state
        raw = json.loads(response_path.read_text(encoding="utf-8"))
        turn = {**record, "response": _response_from_raw(raw), "latency_ms": raw["latency_ms"],
                "http_status": raw.get("http_status"), "response_raw_file": str(response_path.relative_to(case_dir))}
        turn.update(archive_provider_captures(turn["response"], path.parent))
        state["turns"].append(turn)
        if raw.get("delivery_uncertain"):
            state["outcome"] = "ambiguous_delivery"
    state["turns"].sort(key=lambda turn: turn["index"])
    state["clarification_count"] = sum(item["phase"] == "clarification" for item in state["turns"])
    state["used_keys"] = [item["asked_key"] for item in state["turns"] if item.get("asked_key")]
    return state


def post_once(client, base_url: str, case_dir: Path, state: dict, phase: str, payload: dict, *, asked_key=None, supplement_key=None):
    index = len(state["turns"])
    turn_dir = case_dir / "turns" / f"{index:03d}"
    record = {"index": index, "phase": phase, "prepared_at": utcnow(), "request": payload,
              "asked_key": asked_key, "supplement_key": supplement_key}
    write_new(turn_dir / "request.json", safe(record))
    started = perf_counter()
    try:
        response = client.post(base_url.rstrip("/") + "/api/chat", json=payload)
        raw = {"received_at": utcnow(), "http_status": response.status_code,
               "headers": {key: value for key, value in response.headers.items() if key.lower() in {"content-type", "x-request-id"}},
               "body": safe(response.text), "latency_ms": round((perf_counter()-started)*1000)}
    except Exception as exc:
        raw = {"received_at": utcnow(), "network_error": type(exc).__name__, "message": safe(str(exc)),
               "latency_ms": round((perf_counter()-started)*1000), "delivery_uncertain": True}
    # Durable actual response is saved before parsing/controller/checkpoint progression.
    write_new(turn_dir / "response.raw.json", raw)
    turn = {**record, "response": _response_from_raw(raw), "latency_ms": raw["latency_ms"],
            "http_status": raw.get("http_status"), "response_raw_file": str((turn_dir / "response.raw.json").relative_to(case_dir))}
    turn.update(archive_provider_captures(turn["response"], turn_dir))
    state["turns"].append(turn)
    if phase == "clarification":
        state["clarification_count"] += 1
        state["used_keys"].append(asked_key)
    if raw.get("delivery_uncertain"):
        state["outcome"] = "ambiguous_delivery"
    _save_checkpoint(case_dir / "checkpoint.json", state)
    return turn["response"]


def run_case(client, base_url, case, run_dir, version):
    case_dir = run_dir / "cases" / case["id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = case_dir / "checkpoint.json"
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text(encoding="utf-8"))
    else:
        # A version-specific UUID ensures no result/session cache is reused across experiments.
        state = {"id": case["id"], "session_id": "special-" + version + "-" + str(uuid4()), "started_at": utcnow(),
                 "turns": [], "used_keys": [], "clarification_count": 0, "controller_events": [], "outcome": "running"}
        write_new(checkpoint, state)
    state = recover_case(case_dir, state)
    if state["outcome"] != "running":
        _save_checkpoint(checkpoint, state)
        return state
    history = history_messages(case)
    done_history = sum(item["phase"] == "history" for item in state["turns"])
    if any(item["response"].get("status") not in {"SUCCEEDED", "EMPTY_RESULT"} for item in state["turns"] if item["phase"] == "history"):
        state["outcome"] = "history_incomplete"
        _save_checkpoint(checkpoint, state)
        return state
    for message in history[done_history:]:
        response = post_once(client, base_url, case_dir, state, "history", request_payload(state["session_id"], message, case["scope"]))
        if response.get("status") not in {"SUCCEEDED", "EMPTY_RESULT"}:
            state["outcome"] = "history_incomplete" if state["outcome"] == "running" else state["outcome"]
            _save_checkpoint(checkpoint, state)
            return state
    if not any(item["phase"] == "initial" for item in state["turns"]):
        post_once(client, base_url, case_dir, state, "initial", request_payload(state["session_id"], case["input"], case["scope"]))
    if state["outcome"] != "running":
        return state
    target_turns = [item for item in state["turns"] if item["phase"] in {"initial", "clarification"}]
    response = target_turns[-1]["response"]
    cap = min(3, int((case.get("controller") or {}).get("max_clarification_followups", 3)))
    while response.get("status") == "NEEDS_CLARIFICATION" and state["clarification_count"] < cap:
        if case.get("category") == "multi_candidate" and case.get("task") == "01" and not case.get("controller"):
            state["outcome"] = "candidate_only_clarification"
            _save_checkpoint(checkpoint, state)
            return state
        prior_versions = [(item["response"].get("intent") or {}).get("intent_version") for item in target_turns[:-1]]
        latest = max((item for item in prior_versions if isinstance(item, int)), default=None)
        seen_ids = [item["request"].get("clarification_id") for item in target_turns if item["phase"] == "clarification"]
        answer = next_answer(case, response, state["session_id"], state["used_keys"], latest, seen_ids)
        state["controller_events"].append({"after_turn": target_turns[-1]["index"], **answer.as_dict()})
        if answer.outcome != "answer":
            state["outcome"] = answer.outcome
            _save_checkpoint(checkpoint, state)
            return state
        response = post_once(client, base_url, case_dir, state, "clarification", answer.request,
                             asked_key=answer.asked_key, supplement_key=answer.supplement_key)
        if state["outcome"] != "running":
            return state
        target_turns = [item for item in state["turns"] if item["phase"] in {"initial", "clarification"}]
    if response.get("status") == "NEEDS_CLARIFICATION":
        state["outcome"] = "clarification_limit"
    elif response.get("status") not in {"SUCCEEDED", "EMPTY_RESULT"}:
        error = (response.get("error") or {}).get("code", "")
        state["outcome"] = "unimplemented" if response.get("status") == "UNSUPPORTED" else "timeout" if "timeout" in error else "api_failed"
    else:
        # Ordinary user edits begin only after actual clarification completion.
        posts = (case.get("controller") or {}).get("post_completion_turns") or []
        done_posts = sum(item["phase"] == "post_completion" for item in state["turns"])
        if any(item["response"].get("status") not in {"SUCCEEDED", "EMPTY_RESULT"} for item in state["turns"] if item["phase"] == "post_completion"):
            state["outcome"] = "post_completion_incomplete"
            _save_checkpoint(checkpoint, state)
            return state
        for post in posts[done_posts:]:
            response = post_once(client, base_url, case_dir, state, "post_completion", request_payload(state["session_id"], post["message"], case["scope"]))
            if state["outcome"] != "running":
                return state
            if response.get("status") not in {"SUCCEEDED", "EMPTY_RESULT"}:
                state["outcome"] = "post_completion_incomplete"
                break
        else:
            state["outcome"] = "finished"
    state["finished_at"] = utcnow()
    _save_checkpoint(checkpoint, state)
    return state


def check(cases):
    counts = {}
    for case in cases:
        request = request_payload("offline-check-" + case["id"], case["input"], case["scope"])
        forbidden = {"task", "category", "gold_sql", "gold_result", "hidden_goal", "expected_intent", "allowed_user_supplements"}
        if set(request) & forbidden:
            raise AssertionError("Evaluation labels leaked to API payload")
        history_messages(case)
        category = case["task"] + "/" + case["category"]
        counts[category] = counts.get(category, 0) + 1
    return {"cases": len(cases), "scorable": sum(case.get("scorable", False) for case in cases),
            "prediction_calls": 0, "request_contract_check": "passed", "categories": counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "snapshot", "run", "score"))
    parser.add_argument("--cases", type=Path)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--version", default="V0")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=360)
    parser.add_argument("--restart-record", type=Path)
    parser.add_argument("--post-results", type=Path)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    for target in (args.output, args.run_dir):
        if target is not None and not target.resolve().is_relative_to(HERE):
            parser.error("Runner outputs must stay inside this runtime_eval directory")
    if args.action == "snapshot":
        if not args.output:
            parser.error("snapshot requires --output (new path)")
        write_new(args.output, snapshot())
        print(json.dumps({"snapshot": str(args.output), "sha256": digest(args.output), "prediction_calls": 0}))
        return
    if not args.cases:
        parser.error("--cases required")
    cases = load_cases(args.cases)
    if args.action == "check":
        print(json.dumps(check(cases), ensure_ascii=False, indent=2))
        return
    if not args.run_dir:
        parser.error("--run-dir required")
    if args.action == "score":
        if not args.output:
            parser.error("score requires a new --output path")
        manifest = json.loads((args.run_dir / "run-manifest.json").read_text(encoding="utf-8"))
        if manifest["labels_sha256"] != digest(args.cases):
            raise ValueError("Rescoring requires the same frozen labels; amendments need explicit new version evidence")
        print(score_run(cases, args.run_dir, args.output, args.post_results))
        return
    if not args.freeze:
        parser.error("run requires formal --freeze")
    if args.timeout <= 0 or args.timeout > 600:
        parser.error("HTTP timeout must be bounded within (0,600]")
    gate = verify_freeze(args.freeze, args.cases)
    import httpx
    # No HTTP retries: provider retries already belong to the real system's bounded trace.
    with httpx.Client(timeout=args.timeout, trust_env=False, transport=httpx.HTTPTransport(retries=0)) as client:
        health_response = client.get(args.base_url.rstrip("/") + "/health")
        health_response.raise_for_status()
        health = safe(health_response.json())
        evidence = service_evidence(health, gate["current_snapshot"], args.restart_record)
        manifest_path = args.run_dir / "run-manifest.json"
        if args.resume:
            if not manifest_path.exists():
                raise ValueError("No existing run to resume")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest["labels_sha256"] != digest(args.cases) or manifest["freeze_sha256"] != gate["freeze_sha256"] or manifest["version"] != args.version:
                raise ValueError("Resume cannot change labels/freeze/version")
            write_new(args.run_dir / ("resume-" + utcnow().replace(":", "-") + ".json"), {"health": health, "service_load_evidence": evidence, "at": utcnow()})
        else:
            if args.run_dir.exists():
                raise ValueError("Independent new run directory required; existing evidence is never overwritten")
            args.run_dir.mkdir(parents=True)
            write_new(manifest_path, {"started_at": utcnow(), "version": args.version, "labels_sha256": digest(args.cases),
                                      "freeze_sha256": gate["freeze_sha256"], "safe_snapshot": gate["current_snapshot"],
                                      "health": health, "service_load_evidence": evidence,
                                      "http_timeout_seconds": args.timeout, "http_retries": 0, "maximum_clarification_followups": 3,
                                      "total_tasks": 60, "offline_review_calls_mixed_into_runtime": False})
        for index, case in enumerate(cases):
            try:
                state = run_case(client, args.base_url, case, args.run_dir, args.version)
            except Exception as exc:
                case_dir = args.run_dir / "cases" / case["id"]
                checkpoint = case_dir / "checkpoint.json"
                state = json.loads(checkpoint.read_text(encoding="utf-8")) if checkpoint.exists() else {"id": case["id"], "turns": []}
                if "outcome" in state and state["outcome"] == "running":
                    state = recover_case(case_dir, state)
                if state.get("outcome") != "ambiguous_delivery":
                    state["outcome"] = "runner_failed"
                state["runner_error"] = {"type": type(exc).__name__, "message": safe(str(exc))[:1600]}
                case_dir.mkdir(parents=True, exist_ok=True)
                _save_checkpoint(checkpoint, state)
            print(json.dumps({"progress": f"{index+1}/60", "id": case["id"], "outcome": state["outcome"], "posts": len(state["turns"])}, ensure_ascii=False), flush=True)
    if args.output:
        print(score_run(cases, args.run_dir, args.output, args.post_results))


if __name__ == "__main__":
    main()
