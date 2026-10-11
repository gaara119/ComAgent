"""Exercise the real D2 UI/API, keep original results and capture five screenshots."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx
from playwright.sync_api import sync_playwright

from qa_agent.schemas import AnswerEnvelope, ChatRequest

LABELS = {"回答完成": "SUCCEEDED", "查询完成，未找到符合条件的记录": "EMPTY_RESULT",
          "需要补充信息": "NEEDS_CLARIFICATION", "当前来源不支持此问题": "UNSUPPORTED",
          "本次请求未完成": "FAILED", "服务响应超时，请稍后重试。": "CLIENT_TIMEOUT",
          "未能获取有效的问答结果，请稍后重试或联系维护人员。": "CLIENT_ERROR"}
CASES = [
    {"id": "sql", "question": "客户表一共有多少位客户？", "scope": "sql", "expected": ["SUCCEEDED"]},
    {"id": "rewrite", "question": "来自 brazill 的客户有多少位？", "scope": "sql", "expected": ["SUCCEEDED"]},
    {"id": "rag-ocr", "question": "Led Zeppelin（齐柏林飞船）是哪一年、在哪座城市成立的？",
     "scope": "doc", "doc_title": "Led Zeppelin 齐柏林飞船乐队公开简介", "doc_id": "artist-led-zeppelin",
     "expected": ["SUCCEEDED"]},
    {"id": "insufficient", "question": "这份文档能提供 Led Zeppelin 在2099年的全年巡演总收入和纳税申报金额吗？",
     "scope": "doc", "doc_title": "Led Zeppelin 齐柏林飞船乐队公开简介", "doc_id": "artist-led-zeppelin",
     "expected": ["EMPTY_RESULT", "UNSUPPORTED"]},
    {"id": "failure", "question": "请仅查询数据库中明确不存在的 d2_nonexistent_table_20261010 表，列出前5行。不得换成customer或其他现有表，不得猜测结果；无法执行就如实失败。",
     "scope": "sql", "expected": ["FAILED", "UNSUPPORTED"]},
]


def safe_text(value):
    value = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[redacted]", str(value))
    value = re.sub(r"(?i)Bearer\s+\S+", "Bearer [redacted]", value)
    return re.sub(r"(?i)postgres(?:ql)?://[^\s]+", "postgresql://[redacted]", value)


def progress(stage, **payload):
    print(json.dumps({"stage": stage, **payload}, ensure_ascii=False), flush=True)


def _relative(path):
    return path.resolve().relative_to(ROOT).as_posix()


def capture_records(directory):
    result = []
    if directory.is_dir():
        for path in directory.glob("*.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(record.get("request"), dict) and isinstance(record.get("response"), dict):
                    result.append((path, record))
            except (OSError, ValueError):
                continue  # A concurrently written file is re-read on the next poll.
    return result


def wait_api_record(directory, trace_id, timeout=15):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        matching = [(p, r) for p, r in capture_records(directory) if r["response"].get("trace_id") == trace_id]
        if len(matching) == 1:
            return matching[0]
        if len(matching) > 1:
            raise RuntimeError("Duplicate actual API capture for one trace ID")
        time.sleep(.2)
    raise RuntimeError("UI result has no corresponding actual API capture; enable D2_CAPTURE_DIR middleware")


def session_post_count(directory, session_id):
    return sum(r["request"].get("session_id") == session_id for _, r in capture_records(directory))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ui-url", default="http://127.0.0.1:8501")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-records", type=Path, default=ROOT/"eval/artifacts/d2/e2e/api")
    parser.add_argument("--output-dir", type=Path, default=ROOT/"eval/artifacts/d2/e2e/browser")
    parser.add_argument("--screenshots", type=Path, default=ROOT/"notes/screenshots")
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--browser-path", type=Path, default=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"))
    parser.add_argument("--only-case", choices=[c["id"] for c in CASES], help="Fresh run for one failed case; preserve previous records")
    args = parser.parse_args()
    directory = (args.output_dir/args.run_id).resolve()
    if (directory/"report.json").exists():
        parser.error("Run already exists; choose a fresh --run-id")
    directory.mkdir(parents=True, exist_ok=True)
    args.screenshots.mkdir(parents=True, exist_ok=True)
    report = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "command": " ".join(sys.argv),
              "ui_url": args.ui_url, "api_url": args.api_url, "method": "real Edge/Playwright + same-project real API",
              "status": "RUNNING", "human_review_count": 0, "cases": [], "browser_errors": [],
              "holdout_prediction_count": 0, "screenshots": []}

    def save():
        (directory/"report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def shot(page, case_id):
        path = args.screenshots/f"D2-{args.run_id}-{case_id}.png"
        page.evaluate("() => { const main=document.querySelector('[data-testid=\"stMain\"]'); if(main)main.scrollTop=0; }")
        # Set the real browser viewport to fit the rendered evidence panels;
        # avoid blank padding without cropping or editing the screenshot.
        last = page.get_by_test_id("stExpander").last.bounding_box()
        if last:
            height = min(4200, max(1300, math.ceil(last["y"]+last["height"]+45)))
            page.set_viewport_size({"width": 1440, "height": height})
        page.screenshot(path=str(path), full_page=True)
        report["screenshots"].append(_relative(path))
        return _relative(path)

    save()
    with sync_playwright() as playwright:
        options = {"headless": True}
        if args.browser_path.is_file():
            options["executable_path"] = str(args.browser_path)
        browser = playwright.chromium.launch(**options)
        try:
            for case in CASES:
                if args.only_case and args.only_case != case["id"]:
                    continue
                entry = {"id": case["id"], "question": case["question"], "expected_statuses": case["expected"],
                         "checks": {}, "status": "RUNNING"}
                report["cases"].append(entry)
                page = browser.new_page(viewport={"width": 1440, "height": 3200}, device_scale_factor=1)
                page.on("pageerror", lambda error: report["browser_errors"].append(safe_text(error)))
                try:
                    progress("ui_case_start", id=case["id"])
                    page.goto(args.ui_url, wait_until="networkidle")
                    textbox = page.get_by_role("textbox", name="你的问题")
                    textbox.wait_for(timeout=60000)
                    if case["scope"] == "doc":
                        page.get_by_text("指定文档", exact=True).click()
                        selector = page.get_by_role("combobox", name="查询文档")
                        selector.wait_for(timeout=30000)
                        selector.click()
                        page.get_by_role("option", name=case["doc_title"], exact=True).click()
                        page.get_by_text("PNG · zh", exact=True).wait_for(timeout=30000)
                    textbox.fill(case["question"])
                    textbox.press("Tab")
                    page.get_by_role("button", name="提交问题", exact=True).click()
                    alert = page.get_by_test_id("stAlert").filter(has_text=re.compile("|".join(map(re.escape, LABELS)))).first
                    alert.wait_for(timeout=240000)
                    alert_text = alert.inner_text()
                    entry["rendered_status"] = next((status for label, status in LABELS.items() if label in alert_text), "UNKNOWN")
                    page.get_by_text("处理步骤与耗时", exact=True).click()
                    caption = page.get_by_text("请求编号：", exact=False)
                    caption.wait_for(timeout=30000)
                    trace_id = caption.inner_text().split("：", 1)[-1].strip()
                    raw_path, actual = wait_api_record(args.api_records, trace_id)
                    response = AnswerEnvelope.model_validate(actual["response"])
                    session_id = actual["request"]["session_id"]
                    (directory/f"{case['id']}-raw.json").write_text(json.dumps(actual, ensure_ascii=False, indent=2), encoding="utf-8")
                    entry.update(trace_id=trace_id, actual_status=response.status,
                                 actual_api_record=_relative(raw_path), raw_response=_relative(directory/f"{case['id']}-raw.json"))
                    entry["checks"].update(ui_api_trace_id_matches=trace_id == response.trace_id,
                                           ui_api_status_matches=entry["rendered_status"] == response.status,
                                           request_question_matches=actual["request"]["message"] == case["question"],
                                           actual_status_expected=response.status in case["expected"],
                                           three_panels=page.get_by_test_id("stExpander").count() == 3,
                                           actual_step_statuses_valid=all(s.status in {"ok", "warn", "error", "skipped"} for s in response.steps))
                    if case["scope"] == "sql" and response.status == "SUCCEEDED":
                        # Streamlit's canvas table mounts after the result/trace
                        # text; wait for its actual DOM instead of a racing count.
                        page.get_by_test_id("stDataFrame").wait_for(timeout=30000)
                        entry["checks"]["sql_and_table_rendered"] = bool(response.sql) and page.get_by_test_id("stDataFrame").count() > 0
                    if case["id"] == "rewrite":
                        entry["checks"]["actual_rewrite_patches"] = bool(response.rewritten_question and response.metadata.get("nlu", {}).get("patches"))
                        entry["checks"]["rewrite_diff_rendered"] = page.get_by_text("原问题", exact=True).count() == 1 and page.get_by_text("改写后", exact=True).count() == 1
                    if case["id"] == "rag-ocr":
                        entry["checks"].update(citations_within_selected_document=bool(response.evidences) and all(e.doc_id == case["doc_id"] for e in response.evidences),
                                              honest_image_location=all(e.page is None for e in response.evidences))
                        images = page.get_by_test_id("stImage").locator("img")
                        images.first.wait_for(timeout=30000)
                        page.wait_for_function("() => {const x=document.querySelector('[data-testid=\"stImage\"] img');return x&&x.complete&&x.naturalWidth>0;}", timeout=30000)
                        entry["checks"]["original_png_rendered"] = True
                    if case["id"] in {"insufficient", "failure"}:
                        entry["checks"]["no_false_succeeded"] = response.status != "SUCCEEDED"
                    preferred = ("value_link" if case["id"] == "rewrite" else "rag_validate" if case["scope"] == "doc" else "sql_exec")
                    index = next((i for i, step in enumerate(response.steps, start=1) if step.name == preferred), 1)
                    before_count = session_post_count(args.api_records, session_id)
                    page.get_by_text(f"展开第 {index} 步详情", exact=True).click()
                    detail = page.get_by_test_id("stCode").filter(has_text='"输入"').first
                    detail.wait_for(timeout=30000)
                    caption.wait_for(timeout=30000)
                    page.wait_for_function("() => !document.querySelector('[data-testid=\"stSpinner\"]')", timeout=30000)
                    time.sleep(1)
                    after_count = session_post_count(args.api_records, session_id)
                    entry["rerun_verification"] = {"session_id": session_id, "api_posts_before_toggle": before_count,
                                                   "api_posts_after_toggle": after_count,
                                                   "source": "actual API middleware records filtered to this browser session",
                                                   "trace_id_after_toggle": caption.inner_text().split("：", 1)[-1].strip()}
                    entry["checks"].update(step_details_rendered='"输出"' in detail.inner_text(),
                                           rerun_no_new_api_post=before_count == after_count,
                                           rerun_keeps_trace_id=entry["rerun_verification"]["trace_id_after_toggle"] == trace_id)
                    entry["screenshot"] = shot(page, case["id"])
                    dom = safe_text(page.locator("body").inner_text())
                    (directory/f"{case['id']}-dom.txt").write_text(dom, encoding="utf-8")
                    entry["status"] = "PASSED" if all(entry["checks"].values()) else "FAILED"
                    progress("ui_case_complete", id=case["id"], status=entry["status"], actual_status=response.status, trace_id=trace_id)
                except Exception as exc:
                    entry.update(status="FAILED", error={"type": type(exc).__name__, "message": safe_text(exc)})
                    (directory/f"{case['id']}-failure-dom.txt").write_text(safe_text(page.locator("body").inner_text()), encoding="utf-8")
                    page.screenshot(path=str(directory/f"{case['id']}-failure.png"), full_page=True)
                    progress("ui_case_failed", id=case["id"], error=entry["error"])
                finally:
                    page.close()
                    save()
        finally:
            browser.close()
    # Additional real API-only scenarios do not create extra screenshots, and
    # pass only user question + selected scope. Gold stays on the offline side.
    if not args.only_case:
        with httpx.Client(timeout=240, trust_env=False) as client:
            probes = [{"id": "legal-unknown-value", "question": "customer表country字段严格等于'Atlantis'的客户数量是多少？保留该值，不做纠错。",
                       "scope": {"route": "sql", "db_id": "chinook", "doc_ids": []}}]
            ocr_case = ROOT/"eval/artifacts/d2/source/ocr-e2e-case.json"
            if ocr_case.is_file():
                offline = json.loads(ocr_case.read_text(encoding="utf-8"))
                probes.append({"id": "scan-ocr", "question": offline["question"],
                               "scope": {"route": "doc", "db_id": None, "doc_ids": [offline["doc_id"]]}})
            report["api_only_cases"] = []
            for probe in probes:
                entry = {"id": probe["id"], "human_review": "pending"}
                request = ChatRequest(session_id=f"d2-e2e-{probe['id']}-{uuid4()}", message=probe["question"], scope=probe["scope"])
                try:
                    raw = client.post(args.api_url.rstrip("/")+"/api/chat", json=request.model_dump())
                    raw.raise_for_status()
                    envelope = AnswerEnvelope.model_validate(raw.json())
                    record = {"request": request.model_dump(), "response": envelope.model_dump(mode="json")}
                    (directory/f"{probe['id']}-raw.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                    entry.update(actual_status=envelope.status, raw_response=_relative(directory/f"{probe['id']}-raw.json"),
                                 trace_id=envelope.trace_id)
                    if probe["id"] == "legal-unknown-value":
                        values = [value for row in envelope.table or [] for value in row.values()]
                        entry["passed"] = envelope.status == "SUCCEEDED" and values == [0]
                    else:
                        entry["passed"] = envelope.status == "SUCCEEDED" and bool(envelope.evidences) and all(e.page == 2 for e in envelope.evidences)
                except Exception as exc:
                    entry.update(passed=False, error=safe_text(exc))
                report["api_only_cases"].append(entry)
                progress("api_probe_complete", **entry)
                save()
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["status"] = ("PASSED" if all(c["status"] == "PASSED" for c in report["cases"])
                        and not report["browser_errors"] and all(c.get("passed") for c in report.get("api_only_cases", [])) else "PARTIAL_OR_FAILED")
    save()
    progress("complete", status=report["status"], report=_relative(directory/"report.json"), screenshots=report["screenshots"])
    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
