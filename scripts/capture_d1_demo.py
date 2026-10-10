"""Exercise the real Streamlit UI and capture truthful D1 evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "回答完成": "SUCCEEDED", "查询完成，未找到符合条件的记录": "EMPTY_RESULT",
    "需要补充信息": "NEEDS_CLARIFICATION", "当前来源不支持此问题": "UNSUPPORTED",
    "本次请求未完成": "FAILED", "服务响应超时，请稍后重试。": "CLIENT_TIMEOUT",
    "未能获取有效的问答结果，请稍后重试或联系维护人员。": "CLIENT_ERROR",
}


def safe_text(value: str) -> str:
    value = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[已隐藏凭据]", str(value))
    value = re.sub(r"(?i)Bearer\s+\S+", "Bearer [已隐藏凭据]", value)
    return re.sub(r"(?i)postgres(?:ql)?://[^\s]+", "[已隐藏数据库连接]", value)


def progress(stage: str, **data) -> None:
    print(json.dumps({"stage": stage, **data}, ensure_ascii=False), flush=True)


def wait_result(page, timeout=120000) -> tuple[str, str]:
    # A successful HTTP response may contain an EMPTY_RESULT/FAILED envelope.
    # Do not wait forever for the SUCCEEDED label in such cases.
    result = page.get_by_test_id("stAlert").filter(has_text=re.compile("|".join(map(re.escape, LABELS)))).first
    result.wait_for(timeout=timeout)
    text = result.inner_text()
    for label, status in LABELS.items():
        if label in text:
            return status, text
    raise RuntimeError("The rendered result label is not recognized.")


def read_trace(page) -> dict:
    toggle = page.get_by_text("处理步骤与耗时", exact=True)
    toggle.click()
    caption = page.get_by_text("请求编号：", exact=False)
    caption.wait_for(timeout=30000)
    trace_text = caption.inner_text()
    trace_id = trace_text.split("：", 1)[-1].strip()
    body = page.locator("body").inner_text()
    step_count = len(re.findall(r"(?m)^\d+\. llm\s*[·]", body))
    return {"trace_id": trace_id, "trace_caption": trace_text, "observed_llm_steps": step_count}


def close_trace(page) -> None:
    page.get_by_text("处理步骤与耗时", exact=True).click()
    page.get_by_text("请求编号：", exact=False).wait_for(state="hidden", timeout=10000)


def scroll_main_to_top(page) -> None:
    # Streamlit scrolls its main container; full_page only measures the outer
    # document. Capture a taller viewport at a verified zero main scroll offset.
    page.evaluate("() => { const main = document.querySelector('[data-testid=\"stMain\"]'); if (main) main.scrollTop = 0; }")
    page.wait_for_function("() => { const main = document.querySelector('[data-testid=\"stMain\"]'); return main && main.scrollTop === 0; }", timeout=10000)


def three_panels(page) -> dict:
    page.wait_for_function("() => document.querySelectorAll('[data-testid=\"stExpander\"]').length === 3", timeout=10000)
    panels = page.get_by_test_id("stExpander")
    labels = ["SQL 与结果", "引用来源", "处理步骤与耗时"]
    for label in labels:
        if page.get_by_text(label, exact=True).count() != 1:
            raise RuntimeError(f"Expected one actual expander label: {label}")
    return {"count": panels.count(), "labels": labels, "checked_in_actual_browser": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    parser.add_argument("--browser-path", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "notes/screenshots")
    parser.add_argument("--record-path", type=Path, default=ROOT / "notes/ui-smoke.json")
    args = parser.parse_args()
    browser_path = args.browser_path or Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    runtime = ROOT / ".runtime"
    runtime.mkdir(exist_ok=True)
    errors: list[str] = []
    record = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "ui_url": args.url,
              "browser": "Edge Chromium", "status": "RUNNING", "stage": "launch",
              "sql_status": None, "doc_status": None, "page_errors": errors, "screenshots": [],
              "baseline_inclusion": False, "model_attempt_accounting": "actual rendered llm trace steps",
              "checks": {"sql_answer_and_query_rendered": False, "doc_answer_and_evidence_rendered": False,
                         "citation_button_clicked": False, "original_pdf_page_rendered": False,
                         "sql_three_panels": False, "doc_three_panels": False,
                         "idle_three_panels": False, "scope_switch_three_panels": False}}

    def save() -> None:
        args.record_path.parent.mkdir(parents=True, exist_ok=True)
        args.record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    def stage(name: str) -> None:
        record["stage"] = name
        save()
        progress(name)

    def shot(page, name: str, full_page=True) -> None:
        page.screenshot(path=str(output / name), full_page=full_page)
        relative = str((output / name).relative_to(ROOT))
        if relative not in record["screenshots"]:
            record["screenshots"].append(relative)
        save()

    with sync_playwright() as playwright:
        launch = {"headless": True}
        if browser_path.is_file():
            launch["executable_path"] = str(browser_path)
        browser = playwright.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(safe_text(str(error))))
        try:
            stage("load_ui")
            page.goto(args.url, wait_until="networkidle")
            question = page.get_by_role("textbox", name="你的问题")
            question.wait_for(timeout=60000)
            record["idle_panels"] = three_panels(page)
            record["checks"]["idle_three_panels"] = True
            stage("submit_sql")
            question.fill("来自巴西的客户有多少位？")
            question.press("Tab")
            page.get_by_role("button", name="提交问题", exact=True).click()
            sql_status, _ = wait_result(page)
            record["sql_status"] = sql_status
            progress("sql_result", status=sql_status)
            if sql_status != "SUCCEEDED":
                raise RuntimeError(f"SQL demonstration returned {sql_status}.")
            page.get_by_text("执行的 SQL", exact=True).wait_for()
            page.get_by_test_id("stDataFrame").wait_for(timeout=30000)
            record["sql_panels"] = three_panels(page)
            record["checks"]["sql_three_panels"] = True
            record["checks"]["sql_answer_and_query_rendered"] = True
            shot(page, "D1-sql.png")
            record["sql_trace"] = read_trace(page)
            close_trace(page)
            stage("select_document")
            page.get_by_text("指定文档", exact=True).click()
            selector = page.get_by_role("combobox", name="查询文档")
            selector.wait_for(timeout=30000)
            # Scope changes are processed by Streamlit server reruns. Waiting for
            # the source-derived caption confirms the selected document scope,
            # whereas the immediately changed dropdown text alone does not.
            selector.click()
            page.get_by_role("option", name="MacBook Air User Guide", exact=False).click()
            page.get_by_text("PDF · 76 页 · en", exact=True).wait_for(timeout=30000)
            page.get_by_text("执行的 SQL", exact=True).wait_for(state="hidden", timeout=30000)
            record["scope_switch_panels"] = three_panels(page)
            record["checks"]["scope_switch_three_panels"] = True
            record["selected_document"] = "ohr-manual-macbook-air"
            stage("submit_document")
            question.fill("哪款应用可以让你在几分钟内创建并分享影片？")
            question.press("Tab")
            page.get_by_role("button", name="提交问题", exact=True).click()
            doc_status, _ = wait_result(page)
            record["doc_status"] = doc_status
            progress("document_result", status=doc_status)
            # Collect the real trace even on a failed/empty answer, before
            # recording the failure and preserving its visible explanation.
            record["doc_trace"] = read_trace(page)
            close_trace(page)
            if doc_status != "SUCCEEDED":
                raise RuntimeError(f"Document demonstration returned {doc_status}.")
            page.get_by_text("引用依据", exact=True).wait_for(timeout=30000)
            record["doc_panels"] = three_panels(page)
            record["checks"]["doc_three_panels"] = True
            record["checks"]["doc_answer_and_evidence_rendered"] = True
            stage("click_citation")
            buttons = page.get_by_role("button").filter(has_text=re.compile(r"MacBook Air User Guide.*第 \d+ 页"))
            buttons.first.wait_for(timeout=30000)
            buttons.first.click()
            record["checks"]["citation_button_clicked"] = True
            page.get_by_test_id("stImage").locator("img").wait_for(timeout=30000)
            page.wait_for_function("() => { const img = document.querySelector('[data-testid=\"stImage\"] img'); return img && img.complete && img.naturalWidth > 0; }", timeout=30000)
            record["checks"]["original_pdf_page_rendered"] = True
            stage("capture_document")
            page.set_viewport_size({"width": 1440, "height": 1800})
            scroll_main_to_top(page)
            shot(page, "D1-rag.png")
            stage("capture_trace")
            page.set_viewport_size({"width": 1440, "height": 1080})
            page.get_by_text("处理步骤与耗时", exact=True).click()
            page.get_by_text("请求编号：", exact=False).wait_for(timeout=30000)
            page.get_by_text("处理步骤与耗时", exact=True).evaluate("el => el.scrollIntoView({block: 'start', behavior: 'instant'})")
            shot(page, "D1-rag-trace.png", full_page=False)
            record["observed_model_attempts"] = sum(record[key]["observed_llm_steps"] for key in ("sql_trace", "doc_trace"))
            record["status"] = "PASSED" if not errors else "FAILED"
            record["screenshot_capture"] = {"document_viewport": {"width": 1440, "height": 1800},
                                            "document_main_scroll": 0, "trace_view": "expanded trace with request id and first steps visible"}
            record["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            save()
            progress("complete", status=record["status"], model_attempts=record["observed_model_attempts"],
                     screenshots=record["screenshots"], page_errors=errors)
        except Exception as exc:
            record["status"] = "FAILED"
            record["failure"] = {"stage": record["stage"], "type": type(exc).__name__, "message": safe_text(str(exc))}
            record["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            record["observed_model_attempts"] = sum(record.get(key, {}).get("observed_llm_steps", 0)
                                                    for key in ("sql_trace", "doc_trace"))
            try:
                shot(page, f"D1-failure-{record['stage']}.png")
                diagnostic = runtime / f"ui-capture-{record['stage']}.txt"
                diagnostic.write_text(safe_text(page.locator("body").inner_text()), encoding="utf-8")
                record["failure"]["dom_text_file"] = str(diagnostic.relative_to(ROOT))
            finally:
                save()
            progress("failed", failure=record["failure"], model_attempts=record["observed_model_attempts"])
            raise SystemExit(1)
        finally:
            browser.close()
    if record["status"] != "PASSED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
