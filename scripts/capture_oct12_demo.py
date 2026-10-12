"""Prepare or run real Oct 12 UI observations; never synthesize screenshots."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CASES = [
    {"id": "artist-join", "question": "Metallica有多少张专辑？", "scope": "sql",
     "purpose": "实际艺术家外键JOIN查询、SQL与结果展示"},
    {"id": "pinyin-rewrite", "question": "来自巴稀的客户有多少位？", "scope": "sql",
     "purpose": "真实拼音匹配依据可读、不在主流程展示候选ID"},
    {"id": "invoice-ratio", "question": "2024年账单国家为Brazil的发票金额占同年所有发票金额的比例是多少？", "scope": "sql",
     "purpose": "占比显示百分比，原始结果保持分数值"},
    {"id": "invoice-growth", "question": "2024年账单国家为USA的发票销售额同比增长率是多少？", "scope": "sql",
     "purpose": "同比增长率显示百分比，金额列保持金额"},
    {"id": "rag-03", "question": "For how many years after the effective date of the Merger does PSS agree to file all reports required by Section 13 of the Securities Exchange Act of 1934?",
     "scope": "doc", "doc_id": "ohr-law-affiliate", "source_split": "existing_dev",
     "purpose": "观察既有rag-03真实数字核验状态；未核实时显示提示及真实原文引用；不诱导回退"},
]


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def runtime_source_proof() -> dict:
    """Refuse known stale project workers before sending a model request.

    Process age plus source hashes is startup evidence, not a remote attestation
    that every Python module was imported. Record that practical limit.
    """
    sources = []
    for directory in ("qa_agent", "api", "ui"):
        sources.extend(p for p in (ROOT / directory).rglob("*") if p.is_file() and p.suffix in {".py", ".txt"})
    sources += [ROOT / "scripts/d2_capture_api.py"]
    latest_mtime = max(p.stat().st_mtime for p in sources)
    processes = []
    for name, marker in (("api", "uvicorn"), ("ui", "streamlit")):
        pid = int((ROOT / f".runtime/d2-{name}.pid").read_text().strip())
        command = (f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}';"
                   "if($null -eq $p){exit 2};"
                   "$p | Select-Object ProcessId,ParentProcessId,CommandLine,ExecutablePath,"
                   "@{Name='Created';Expression={$_.CreationDate.ToUniversalTime().ToString('o')}} | ConvertTo-Json")
        raw = subprocess.run(["pwsh", "-NoProfile", "-Command", command], capture_output=True, text=True, encoding="utf-8")
        if raw.returncode:
            raise RuntimeError(f"Saved {name} process is unavailable; no model requests sent")
        process = json.loads(raw.stdout)
        command_line = process.get("CommandLine") or ""
        if str(ROOT / ".venv/Scripts/python.exe").replace("/", "\\").casefold() not in command_line.casefold() or marker not in command_line:
            raise RuntimeError(f"Saved {name} PID is not the verified project worker; no requests sent")
        created = datetime.fromisoformat(process["Created"])
        if created.timestamp() < latest_mtime:
            raise RuntimeError(f"{name} started before current runtime source changes; restart first, no requests sent")
        processes.append({"service": name, "saved_pid": pid, "created_at_utc": created.isoformat(),
                          "owned_project_python": True, "marker": marker})
    return {"processes": processes,
            "source_sha256": {relative(p): sha256(p.read_bytes()).hexdigest() for p in sorted(set(sources))},
            "limit": "Verified saved launchers started after current source modifications; not a remote loaded-module attestation."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true", help="Only save planned steps; no network/model/browser calls")
    mode.add_argument("--run", action="store_true", help="Run real browser observations after project service restart")
    parser.add_argument("--output", type=Path, required=True, help="Fresh project-relative output directory")
    parser.add_argument("--api-records", type=Path)
    parser.add_argument("--ui-url", default="http://127.0.0.1:8501")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--browser-path", type=Path, default=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"))
    parser.add_argument("--only-case", choices=[case["id"] for case in CASES])
    args = parser.parse_args()
    output = (ROOT / args.output).resolve() if not args.output.is_absolute() else args.output.resolve()
    output.relative_to(ROOT)
    if output.exists():
        parser.error("Output already exists; preserve previous plans and actual observations")
    output.mkdir(parents=True)
    cases = [case for case in CASES if not args.only_case or case["id"] == args.only_case]
    if args.prepare:
        write(output / "plan.json", {"state": "PLANNED_NOT_RUN", "cases": cases,
              "procedure": ["核验两个项目服务均启动于当前源码修改之后", "使用真实Edge打开Streamlit并提交题面和来源",
                            "等待对应真实API中间件记录，保存原始响应", "核验主界面文字、引用、百分比与原始值",
                            "保存未经编辑的PNG与DOM，再展开处理步骤核对请求编号"],
              "model_requests": 0, "holdout_predictions": 0, "screenshots": [],
              "rag_fallback_rule": "真实模型未触发第二次数字失败时如实写未观察到该分支，不伪造或诱导回退。"})
        print(json.dumps({"state": "PLANNED_NOT_RUN", "plan": relative(output / "plan.json")}, ensure_ascii=False))
        return 0
    if not args.api_records:
        parser.error("--run requires the fresh service's --api-records directory")
    import httpx
    from playwright.sync_api import sync_playwright
    from qa_agent.schemas import AnswerEnvelope
    from scripts.capture_d2_demo import safe_text, wait_api_record, session_post_count
    from ui.app import result_display_table
    args.api_records = (ROOT / args.api_records).resolve()
    report = {"state": "RUNNING", "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "command": [sys.executable, "-B", *sys.argv], "method": "real Edge/Streamlit + same-project API captures",
              "holdout_predictions": 0, "cases": [], "screenshots": [], "browser_errors": []}
    def save():
        write(output / "report.json", report)
    try:
        report["runtime_source_proof"] = runtime_source_proof()
        with httpx.Client(timeout=15, trust_env=False) as client:
            health = client.get(args.api_url.rstrip("/") + "/health"); health.raise_for_status()
            report["health"] = health.json()
            docs = client.get(args.api_url.rstrip("/") + "/api/documents"); docs.raise_for_status()
            by_id = {doc["doc_id"]: doc for doc in docs.json()["documents"]}
        if report["health"].get("status") != "ok":
            raise RuntimeError("Project health is not ready; no UI model requests sent")
        save()
        with sync_playwright() as playwright:
            options = {"headless": True}
            if args.browser_path.is_file():
                options["executable_path"] = str(args.browser_path)
            browser = playwright.chromium.launch(**options)
            try:
                for case in cases:
                    entry = {**case, "state": "RUNNING", "checks": {}}
                    report["cases"].append(entry); save()
                    print(json.dumps({"stage": "start", "id": case["id"]}, ensure_ascii=False), flush=True)
                    page = browser.new_page(viewport={"width": 1440, "height": 1900}, device_scale_factor=1)
                    page.on("pageerror", lambda error: report["browser_errors"].append(safe_text(error)))
                    try:
                        page.goto(args.ui_url, wait_until="networkidle")
                        textbox = page.get_by_role("textbox", name="你的问题"); textbox.wait_for(timeout=60000)
                        if case["scope"] == "doc":
                            page.get_by_text("指定文档", exact=True).click()
                            selector = page.get_by_role("combobox", name="查询文档")
                            selector.wait_for(timeout=30000); selector.click()
                            page.get_by_role("option", name=by_id[case["doc_id"]]["title"], exact=True).click()
                        textbox.fill(case["question"]); textbox.press("Tab")
                        page.get_by_role("button", name="提交问题", exact=True).click()
                        caption = page.get_by_text("请求编号：", exact=False)
                        caption.wait_for(state="attached", timeout=300000)
                        page.wait_for_function("() => !document.querySelector('[data-testid=\"stSpinner\"]')", timeout=60000)
                        public_dom = safe_text(page.locator("body").inner_text())
                        if not caption.is_visible():
                            page.get_by_text("处理步骤与耗时", exact=True).click()
                        caption.wait_for(timeout=30000)
                        trace_id = caption.inner_text().split("：", 1)[-1].strip()
                        raw_path, raw = wait_api_record(args.api_records, trace_id)
                        response = AnswerEnvelope.model_validate(raw["response"])
                        if response.table:
                            page.get_by_test_id("stDataFrame").wait_for(timeout=30000)
                        if response.evidences and page.get_by_test_id("stImage").count():
                            page.wait_for_function("() => [...document.querySelectorAll('[data-testid=\"stImage\"] img')].every(x=>x.complete&&x.naturalWidth>0)", timeout=30000)
                        write(output / f"{case['id']}-raw.json", raw)
                        entry.update(trace_id=trace_id, actual_status=response.status,
                                     raw=relative(output / f"{case['id']}-raw.json"), api_record=relative(raw_path))
                        entry["checks"].update(trace_matches=response.trace_id == trace_id,
                                                request_question_matches=raw["request"]["message"] == case["question"],
                                                three_panels=page.get_by_test_id("stExpander").count() == 3)
                        if case["scope"] == "sql":
                            entry["checks"]["succeeded_with_sql"] = response.status == "SUCCEEDED" and bool(response.sql)
                        if case["id"] == "artist-join":
                            entry["checks"]["actual_join"] = bool(re.search(r"\bJOIN\b", response.sql or "", re.I))
                        elif case["id"] == "pinyin-rewrite":
                            entry["checks"].update(readable_matching_basis="巴稀 → Brazil（拼音匹配" in public_dom,
                                                    no_candidate_id_in_public_flow=not re.search(r"\bv-[a-z0-9]+", public_dom))
                        elif case["id"] in {"invoice-ratio", "invoice-growth"}:
                            formatted = result_display_table(response)
                            percentages = [value for row in formatted or [] for value in row.values()
                                           if isinstance(value, str) and value.endswith("%")]
                            entry["percentage_observation"] = {"raw_table": response.table, "formatted_display": formatted,
                                                                 "percentage_text_in_answer": [v for v in percentages if v in public_dom]}
                            entry["checks"].update(percentage_display_values=bool(percentages),
                                                    percentage_visible_in_public_text=any(v in public_dom for v in percentages))
                        else:
                            uncertain = response.metadata.get("faithfulness_uncertain") is True
                            entry["fallback_branch_observed"] = uncertain
                            entry["fallback_observation"] = ("实际触发未核实回退" if uncertain else
                                                                "本次真实回答未触发未核实回退；不能据此声称该分支实测通过")
                            entry["checks"].update(no_failed_numeric_return=not (
                                response.status == "FAILED" and response.error and response.error.code == "rag_number_invalid"),
                                document_scope_preserved=all(e.doc_id == case["doc_id"] for e in response.evidences))
                            if uncertain:
                                entry["checks"].update(unverified_visible="未核实" in public_dom,
                                                       unverified_metadata=response.metadata.get("validation_status") == "unverified",
                                                       real_citations_present=bool(response.evidences))
                        session = raw["request"]["session_id"]
                        before = session_post_count(args.api_records, session)
                        # The response caption mounts before Streamlit finishes
                        # painting its code/canvas table and source-page image.
                        # Keep the primary result visible, collapse only the
                        # already-inspected trace panel and await the real paint.
                        if caption.is_visible():
                            page.get_by_text("处理步骤与耗时", exact=True).click()
                        page.wait_for_function("() => !document.querySelector('[data-testid=\"stSpinner\"]')", timeout=60000)
                        if response.table:
                            page.get_by_test_id("stDataFrame").wait_for(timeout=30000)
                        image_load_waited = False
                        if response.evidences:
                            page.get_by_test_id("stImage").first.wait_for(timeout=30000)
                            page.wait_for_function("() => [...document.querySelectorAll('[data-testid=\"stImage\"] img')].every(x=>x.complete&&x.naturalWidth>0)", timeout=30000)
                            image_load_waited = True
                        # Streamlit scrolls within stMain. Measure the page after
                        # the real PDF image establishes its height, otherwise
                        # full_page captures only the old shorter viewport.
                        page.evaluate("async () => {await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));}")
                        page.evaluate("() => { const main=document.querySelector('[data-testid=\"stMain\"]');if(main)main.scrollTop=0; }")
                        last = page.get_by_test_id("stExpander").last.bounding_box()
                        if last:
                            page.set_viewport_size({"width": 1440, "height": min(3400, max(1300, math.ceil(last["y"]+last["height"]+80)))})
                        page.evaluate("async () => {await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));}")
                        time.sleep(1.5)
                        if response.evidences and page.get_by_test_id("stImage").count():
                            page.wait_for_function("() => [...document.querySelectorAll('[data-testid=\"stImage\"] img')].every(x=>x.complete&&x.naturalWidth>0)", timeout=30000)
                        image = output / f"{case['id']}.png"
                        page.screenshot(path=str(image), full_page=True)
                        entry["screenshot_wait"] = {"real_dom_and_fonts_waited": True,
                                                     "table_mount_waited": bool(response.table),
                                                     "image_load_waited_when_present": image_load_waited,
                                                     "viewport_measured_after_image_load": image_load_waited,
                                                     "paint_stability_pause_seconds": 1.5,
                                                     "trace_panel": "inspected_then_collapsed_for_primary_result"}
                        entry["screenshot"] = relative(image); report["screenshots"].append(relative(image))
                        (output / f"{case['id']}-dom.txt").write_text(safe_text(page.locator("body").inner_text()), encoding="utf-8")
                        time.sleep(.5)
                        entry["checks"]["inspection_no_new_api_post"] = session_post_count(args.api_records, session) == before
                        entry["state"] = "PASS" if all(entry["checks"].values()) else "FAIL"
                    except Exception as exc:
                        entry.update(state="ERROR", error={"type": type(exc).__name__, "message": safe_text(exc)})
                        (output / f"{case['id']}-error-dom.txt").write_text(safe_text(page.locator("body").inner_text()), encoding="utf-8")
                        error_image = output / f"{case['id']}-error.png"
                        page.screenshot(path=str(error_image), full_page=True)
                        entry["error_screenshot"] = relative(error_image)
                    finally:
                        page.close(); save()
                    print(json.dumps({"stage": "complete", "id": case["id"], "state": entry["state"]}, ensure_ascii=False), flush=True)
            finally:
                browser.close()
        report["state"] = "PASS" if all(row["state"] == "PASS" for row in report["cases"]) and not report["browser_errors"] else "PARTIAL_OR_FAILED"
    except Exception as exc:
        report.update(state="BLOCKED_OR_ERROR", error=safe_text(exc))
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat(); save()
    print(json.dumps({"state": report["state"], "screenshots": len(report["screenshots"]), "report": relative(output / "report.json")}, ensure_ascii=False), flush=True)
    return 0 if report["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
