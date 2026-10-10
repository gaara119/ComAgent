"""Exercise the real Streamlit UI and capture D1 evidence on this machine."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    parser.add_argument("--browser-path", type=Path)
    args = parser.parse_args()
    browser_path = args.browser_path or Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    output = ROOT / "notes/screenshots"
    output.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    with sync_playwright() as playwright:
        launch = {"headless": True}
        if browser_path.is_file():
            launch["executable_path"] = str(browser_path)
        browser = playwright.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(args.url, wait_until="networkidle")
        question = page.get_by_role("textbox", name="你的问题")
        question.wait_for(timeout=60000)
        question.fill("来自巴西的客户有多少位？")
        page.get_by_role("button", name="提交问题", exact=True).click()
        page.get_by_text("回答完成", exact=True).wait_for(timeout=240000)
        page.get_by_text("执行的 SQL", exact=True).wait_for()
        page.get_by_test_id("stDataFrame").wait_for(timeout=60000)
        page.get_by_text("处理步骤与耗时", exact=True).wait_for()
        page.screenshot(path=str(output / "D1-sql.png"), full_page=True)
        page.get_by_text("处理步骤与耗时", exact=True).click()
        page.get_by_text("请求编号：", exact=False).wait_for()
        sql_trace = page.get_by_text("请求编号：", exact=False).inner_text()
        page.get_by_text("处理步骤与耗时", exact=True).click()
        page.get_by_text("指定文档", exact=True).click()
        selector = page.get_by_role("combobox", name="查询文档")
        selector.click()
        page.get_by_role("option", name="MacBook Air User Guide", exact=False).click()
        # This is a demonstration of a development-set question, never a holdout question.
        question.fill("哪款应用可以让你在几分钟内创建并分享影片？")
        page.get_by_role("button", name="提交问题", exact=True).click()
        page.get_by_text("回答完成", exact=True).wait_for(timeout=240000)
        page.get_by_text("引用依据", exact=True).wait_for()
        buttons = page.get_by_role("button").filter(has_text=re.compile(r"MacBook Air User Guide.*第 \d+ 页"))
        buttons.first.click()
        page.get_by_test_id("stImage").locator("img").wait_for(timeout=60000)
        page.wait_for_function("() => { const img = document.querySelector('[data-testid=\"stImage\"] img'); return img && img.complete && img.naturalWidth > 0; }", timeout=60000)
        page.get_by_text("处理步骤与耗时", exact=True).wait_for()
        page.screenshot(path=str(output / "D1-rag.png"), full_page=True)
        page.get_by_text("处理步骤与耗时", exact=True).click()
        page.get_by_text("请求编号：", exact=False).wait_for()
        doc_trace = page.get_by_text("请求编号：", exact=False).inner_text()
        page.screenshot(path=str(output / "D1-rag-trace.png"), full_page=True)
        record = {"ui_url": args.url, "browser": "chromium", "sql_trace": sql_trace,
                  "doc_trace": doc_trace, "page_errors": errors,
                  "screenshots": ["notes/screenshots/D1-sql.png", "notes/screenshots/D1-rag.png", "notes/screenshots/D1-rag-trace.png"],
                  "checks": {"sql_answer_and_query_rendered": True, "doc_answer_and_evidence_rendered": True,
                             "citation_button_clicked": True, "original_pdf_page_rendered": True}}
        (ROOT / "notes/ui-smoke.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()
    print(json.dumps({"page_errors": errors, "screenshots": record["screenshots"]}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
