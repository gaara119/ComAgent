"""Observe one existing AW DEV question in the actual UI, without reading gold."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.capture_d2_demo import safe_text, wait_api_record
from scripts.capture_oct12_demo import runtime_source_proof
from scripts.capture_d4_fusion_ui import wait_layout_stable, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api-records", type=Path, required=True)
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT / "eval/artifacts/d4") or out.exists():
        raise ValueError("Use a fresh D4 observation directory")
    source = ROOT / "eval/datasets/d3/aw_schema_link.dev.v2.jsonl"
    # Parse only the existing DEV file to find the question. No gold field is
    # accessed, reported, provided to the UI, or used for result scoring.
    question = None
    for line in source.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["id"] == "aw-01":
            if row["split"] != "dev":
                raise ValueError("Only existing DEV may be submitted")
            question = row["question"]
            break
    if question is None:
        raise ValueError("AW DEV question is absent")
    proof = runtime_source_proof()
    out.mkdir(parents=True)
    report = {"at_utc": datetime.now(timezone.utc).isoformat(), "command": [sys.executable, *sys.argv],
              "source": source.relative_to(ROOT).as_posix(), "source_sha256": sha256(source.read_bytes()).hexdigest(),
              "question_id": "aw-01", "question": question, "runtime_source_proof": proof,
              "gold_fields_accessed": False, "held_predictions": 0, "browser_errors": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 2000}, device_scale_factor=1)
        page.on("pageerror", lambda error: report["browser_errors"].append(safe_text(error)))
        try:
            page.goto("http://127.0.0.1:8501", wait_until="networkidle")
            page.get_by_role("combobox", name="数据库", exact=True).click()
            page.get_by_role("option", name="AdventureWorks", exact=True).click()
            textbox = page.get_by_role("textbox", name="你的问题")
            textbox.wait_for(timeout=60000)
            textbox.fill(question)
            textbox.press("Tab")
            page.get_by_role("button", name="提交问题", exact=True).click()
            caption = page.get_by_text("请求编号：", exact=False)
            caption.wait_for(state="attached", timeout=300000)
            if not caption.is_visible():
                page.get_by_text("处理步骤与耗时", exact=True).click()
            caption.wait_for(timeout=30000)
            trace_id = caption.inner_text().split("请求编号：", 1)[-1].strip()
            record_path, raw = wait_api_record((ROOT / args.api_records).resolve(), trace_id, timeout=20)
            response = raw["response"]
            write(out / "raw-api.json", raw)
            bundle = response.get("metadata", {}).get("schema_linker", {})
            page.get_by_text("所选表及理由", exact=True).wait_for(timeout=30000)
            if bundle.get("excluded_tables"):
                page.get_by_text("未选表及理由", exact=True).wait_for(timeout=30000)
            steps = response.get("steps", [])
            last_step = page.get_by_text(f"{len(steps)}. {steps[-1]['name']}", exact=False).last
            last_step.wait_for(timeout=30000)
            page.wait_for_function("() => !document.querySelector('[data-testid=\"stSpinner\"]')", timeout=30000)
            page.evaluate("() => {const m=document.querySelector('[data-testid=\"stMain\"]');if(m)m.scrollTop=0;}")
            wait_layout_stable(page)
            panel = page.get_by_test_id("stExpander").last.bounding_box()
            tail = last_step.bounding_box()
            height = min(6000, max(2000, int(max(panel["y"] + panel["height"], tail["y"] + tail["height"]) + 100)))
            page.set_viewport_size({"width": 1440, "height": height})
            page.evaluate("() => {const m=document.querySelector('[data-testid=\"stMain\"]');if(m)m.scrollTop=0;}")
            wait_layout_stable(page)
            body = safe_text(page.locator("body").inner_text())
            panel = page.get_by_test_id("stExpander").last.bounding_box()
            tail = last_step.bounding_box()
            names = [step["name"] for step in steps]
            checks = {"actual_aw_scope": raw["request"]["scope"]["db_id"] == "adventureworks",
                      "actual_question": raw["request"]["message"] == question,
                      "successful_api": response["status"] == "SUCCEEDED",
                      "sql_result_visible": bool(response.get("sql")) and bool(response.get("table")) and "执行的 SQL" in body,
                      "selected_reasons_visible": "所选表及理由" in body and bool(bundle.get("reasons")),
                      "excluded_reasons_visible": "未选表及理由" in body and bool(bundle.get("excluded_tables")),
                      "actual_schema_prune": any(step["name"] == "schema_prune" and step["status"] == "ok" for step in steps),
                      "actual_sql_validation_execution": "sql_validate" in names and "sql_exec" in names,
                      "connectivity_reported": "disconnected_components" in bundle and "pruning" in bundle,
                      "three_panels": page.get_by_test_id("stExpander").count() == 3,
                      "full_flow_in_viewport": panel["y"] + panel["height"] <= height,
                      "last_step_in_viewport": tail["y"] + tail["height"] <= height,
                      "no_browser_errors": not report["browser_errors"]}
            page.screenshot(path=str(out / "aw-01.png"), full_page=True)
            (out / "dom.txt").write_text(body, encoding="utf-8")
            report.update(trace_id=trace_id, original_record=record_path.relative_to(ROOT).as_posix(),
                          checks=checks, matched=all(checks.values()), actual_viewport=page.viewport_size,
                          schema_bundle=bundle, result=response.get("table"),
                          measurement="Actual UI/module flow observation; no gold comparison or EX computed")
        except Exception as exc:
            report.update(matched=False, error=safe_text(exc))
            page.screenshot(path=str(out / "error.png"), full_page=True)
            (out / "error-dom.txt").write_text(safe_text(page.locator("body").inner_text()), encoding="utf-8")
        finally:
            write(out / "report.json", report)
            browser.close()
    print(json.dumps({"matched": report.get("matched"), "checks": report.get("checks"), "error": report.get("error")}, ensure_ascii=False))
    return 0 if report.get("matched") else 1


if __name__ == "__main__":
    raise SystemExit(main())
