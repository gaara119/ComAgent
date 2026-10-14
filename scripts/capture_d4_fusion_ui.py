"""Observe both D4 fusion routes in the actual Streamlit UI; no synthetic images."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.capture_d2_demo import safe_text, wait_api_record
from scripts.capture_oct12_demo import runtime_source_proof

CASES = [
    {"id": "sql-to-doc", "question": "销售额最高的艺术家是谁？介绍一下他的音乐风格。", "kind": "sql_to_doc"},
    {"id": "doc-to-sql", "question": "按口径手册中客单价的定义，计算2024年客户所在地为USA的客单价。", "kind": "doc_to_sql"},
]


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def wait_layout_stable(page, timeout=15):
    """Observe Streamlit's queued DOM/expander layout until geometry settles."""
    deadline = time.monotonic() + timeout
    previous = None
    stable_samples = 0
    while time.monotonic() < deadline:
        current = page.evaluate("""() => {
            const panels=[...document.querySelectorAll('[data-testid="stExpander"]')];
            const main=document.querySelector('[data-testid="stMain"]');
            return JSON.stringify({text:document.body.innerText.length,
                main:main?.scrollHeight,
                boxes:panels.map(p=>{const r=p.getBoundingClientRect();return [Math.round(r.y),Math.round(r.height)]})});
        }""")
        stable_samples = stable_samples + 1 if current == previous else 0
        if stable_samples >= 4:
            return
        previous = current
        time.sleep(0.15)
    raise TimeoutError("Streamlit observation layout did not settle; no complete screenshot claimed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--api-records", type=Path)
    parser.add_argument("--entry-only", action="store_true", help="Observe the source entry without submitting any question")
    parser.add_argument("--only-case", choices=[case["id"] for case in CASES],
                        help="Repeat only the failed observation, retaining earlier successful cases")
    parser.add_argument("--ui-url", default="http://127.0.0.1:8501")
    parser.add_argument("--browser-path", type=Path,
                        default=Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"))
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT / "eval/artifacts/d4") or out.exists():
        raise ValueError("Use a fresh D4 observation directory")
    if args.entry_only:
        out.mkdir(parents=True)
        errors = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=str(args.browser_path), headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 1400}, device_scale_factor=1)
                page.on("pageerror", lambda error: errors.append(safe_text(error)))
                page.goto(args.ui_url, wait_until="networkidle")
                page.get_by_text("数据库与文档", exact=True).click()
                page.get_by_role("textbox", name="你的问题").wait_for(timeout=60000)
                page.get_by_text("允许检索的文档（留空使用全部对应文档）", exact=True).wait_for(timeout=30000)
                page.wait_for_function("() => !document.querySelector('[data-testid=\"stSpinner\"]')", timeout=30000)
                page.evaluate("async () => {await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));}")
                body = safe_text(page.locator("body").inner_text())
                checks = {"project_title": "精准问数问答" in body, "hybrid_source": "数据库与文档" in body,
                          "scope_selection": "允许检索的文档" in body,
                          "three_panels": page.get_by_test_id("stExpander").count() == 3,
                          "no_model_error": not errors}
                page.screenshot(path=str(out / "entry.png"), full_page=True)
                (out / "entry-dom.txt").write_text(body, encoding="utf-8")
                write(out / "report.json", {"command": [sys.executable, *sys.argv], "checks": checks,
                    "matched": all(checks.values()), "browser_errors": errors, "questions_submitted": 0,
                    "measurement": "Actual entry-only browser observation; no question form submitted, not fusion success evidence",
                    "ui_source_sha256": sha256((ROOT / "ui/app.py").read_bytes()).hexdigest()})
                print(json.dumps({"entry_only": True, "questions_submitted": 0, "checks": checks}, ensure_ascii=False))
                return 0 if all(checks.values()) else 1
            finally:
                browser.close()
    if not args.api_records:
        parser.error("Real question observations require --api-records")
    records = (ROOT / args.api_records).resolve()
    proof = runtime_source_proof()
    out.mkdir(parents=True)
    cases = [case for case in CASES if not args.only_case or case["id"] == args.only_case]
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "command": [sys.executable, *sys.argv],
              "runtime_source_proof": proof, "count": len(cases), "matched": 0, "cases": [], "browser_errors": [],
              "human_document_semantics": "pending_human_review", "held_predictions": 0}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=str(args.browser_path), headless=True)
        try:
            for case in cases:
                page = browser.new_page(viewport={"width": 1440, "height": 2000}, device_scale_factor=1)
                page.on("pageerror", lambda error: report["browser_errors"].append(safe_text(error)))
                observation = {"id": case["id"], "question": case["question"]}
                try:
                    page.goto(args.ui_url, wait_until="networkidle")
                    page.get_by_text("数据库与文档", exact=True).click()
                    page.get_by_text("允许检索的文档（留空使用全部对应文档）", exact=True).wait_for(timeout=30000)
                    textbox = page.get_by_role("textbox", name="你的问题")
                    textbox.wait_for(timeout=60000)
                    textbox.fill(case["question"])
                    textbox.press("Tab")
                    page.get_by_role("button", name="提交问题", exact=True).click()
                    caption = page.get_by_text("请求编号：", exact=False)
                    caption.wait_for(state="attached", timeout=300000)
                    page.wait_for_function("() => !document.querySelector('[data-testid=\"stSpinner\"]')", timeout=60000)
                    if not caption.is_visible():
                        page.get_by_text("处理步骤与耗时", exact=True).click()
                    caption.wait_for(timeout=30000)
                    trace_id = caption.inner_text().split("请求编号：", 1)[-1].strip()
                    record_path, raw = wait_api_record(records, trace_id, timeout=20)
                    response = raw["response"]
                    write(out / (case["id"] + "-raw-api.json"), raw)
                    page.wait_for_function("() => !document.querySelector('[data-testid=\"stSpinner\"]')", timeout=60000)
                    if response.get("table"):
                        page.get_by_test_id("stDataFrame").first.wait_for(timeout=30000)
                    if response.get("evidences"):
                        page.get_by_role("button", name="下载原始文件", exact=True).first.wait_for(state="attached", timeout=30000)
                    if response.get("steps"):
                        last_step = f"{len(response['steps'])}. {response['steps'][-1]['name']}"
                        page.get_by_text(last_step, exact=False).wait_for(state="attached", timeout=30000)
                    page.evaluate("async () => {await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));}")
                    page.evaluate("() => {const main=document.querySelector('[data-testid=\"stMain\"]');if(main)main.scrollTop=0;}")
                    wait_layout_stable(page)
                    final_panel = page.get_by_test_id("stExpander").last.bounding_box()
                    last_step_box = page.get_by_text(last_step, exact=False).last.bounding_box() if response.get("steps") else None
                    if final_panel:
                        bottom = max(final_panel["y"] + final_panel["height"],
                                     last_step_box["y"] + last_step_box["height"] if last_step_box else 0)
                        page.set_viewport_size({"width": 1440, "height": min(6000, max(2000, int(bottom + 100)))})
                    page.evaluate("() => {const main=document.querySelector('[data-testid=\"stMain\"]');if(main)main.scrollTop=0;}")
                    page.evaluate("async () => {await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));}")
                    wait_layout_stable(page)
                    body = safe_text(page.locator("body").inner_text())
                    fusion = response.get("metadata", {}).get("fusion", {})
                    final_panel = page.get_by_test_id("stExpander").last.bounding_box()
                    viewport_height = page.viewport_size["height"]
                    download = page.get_by_role("button", name="下载原始文件", exact=True).first
                    last_step_locator = page.get_by_text(last_step, exact=False).last if response.get("steps") else None
                    last_step_box = last_step_locator.bounding_box() if last_step_locator else None
                    checks = {"hybrid_scope": raw["request"]["scope"]["route"] == "hybrid",
                              "successful_api": response["status"] == "SUCCEEDED",
                              "actual_plan": fusion.get("kind") == case["kind"],
                              "two_stages": fusion.get("completed_stages") == 2,
                              "sql_visible": bool(response.get("sql")) and "执行的 SQL" in body,
                              "citations_visible": bool(response.get("evidences")) and "引用依据" in body,
                              "flow_visible": "跨源执行" in body,
                              "three_panels": page.get_by_test_id("stExpander").count() == 3,
                              "download_ready": download.is_visible() and download.is_enabled(),
                              "full_flow_in_viewport": bool(final_panel and final_panel["y"] >= 0
                                  and final_panel["y"] + final_panel["height"] <= viewport_height),
                              "last_step_in_viewport": bool(last_step_locator and last_step_locator.is_visible()
                                  and last_step_box and last_step_box["y"] >= 0
                                  and last_step_box["y"] + last_step_box["height"] <= viewport_height)}
                    if case["kind"] == "sql_to_doc":
                        checks["transferred_artist_visible"] = "数据库结果传给文档检索" in body
                    else:
                        checks["definition_applied_visible"] = "实际检索定义已用于SQL生成" in body
                    # Capture the actual DOM and pixels after the response; leave
                    # SQL and sources expanded and the full execution chain open.
                    image = out / (case["id"] + ".png")
                    page.screenshot(path=str(image), full_page=True)
                    (out / (case["id"] + "-dom.txt")).write_text(body, encoding="utf-8")
                    observation.update(trace_id=trace_id, original_record=record_path.relative_to(ROOT).as_posix(),
                                       checks=checks, matched=all(checks.values()), screenshot=image.name,
                                       raw_response=case["id"] + "-raw-api.json",
                                       actual_viewport=page.viewport_size,
                                       flow_panel_box=final_panel, last_step_box=last_step_box)
                except Exception as exc:
                    observation.update(matched=False, error=safe_text(exc))
                    (out / (case["id"] + "-error-dom.txt")).write_text(safe_text(page.locator("body").inner_text()), encoding="utf-8")
                    page.screenshot(path=str(out / (case["id"] + "-error.png")), full_page=True)
                finally:
                    page.close()
                    report["cases"].append(observation)
                    report["matched"] += int(observation["matched"])
                    write(out / "report.json", report)
                    print(json.dumps(observation, ensure_ascii=False), flush=True)
        finally:
            browser.close()
    return 0 if report["matched"] == len(cases) and not report["browser_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
