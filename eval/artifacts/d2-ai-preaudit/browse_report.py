"""Open only the new local AI report in headless Edge and check its controls."""
from datetime import datetime, timezone
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPORT = ROOT / "eval/reports/d2-ai-preaudit/D2统一待审核表-AI预审报告.html"


def main():
    errors = []
    remote_requests = []
    results = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.on("request", lambda request: remote_requests.append(request.url)
                if request.url.startswith(("http://", "https://")) else None)
        page.goto(REPORT.as_uri(), wait_until="load")
        results["all_rows"] = page.locator("details.item").count()
        results["all_visible"] = page.locator("details.item:not([hidden])").count()
        page.screenshot(path=str(OUT / "report-overview.png"))
        page.locator("#split").select_option("dev")
        results["development_visible"] = page.locator("details.item:not([hidden])").count()
        page.locator("#split").select_option("holdout")
        results["holdout_progress_visible"] = page.locator("details.item:not([hidden])").count()
        results["holdout_generic_only"] = all("保留题内容本轮未审核" in text
            for text in page.locator("details.item:not([hidden])").all_text_contents())
        page.locator("#split").select_option("all")
        page.locator("#group").select_option("alias")
        results["alias_visible"] = page.locator("details.item:not([hidden])").count()
        page.locator("#group").select_option("rag")
        page.locator("#split").select_option("dev")
        results["rag_development_visible"] = page.locator("details.item:not([hidden])").count()
        page.locator("#search").fill("rag-19")
        results["rag19_search_visible"] = page.locator("details.item:not([hidden])").count()
        page.locator("#expand").click()
        item = page.locator("details.item:not([hidden])")
        results["expanded"] = item.get_attribute("open") is not None
        item.scroll_into_view_if_needed()
        page.screenshot(path=str(OUT / "rag-19-expanded.png"))
        browser.close()
    expected = {"all_rows": 195, "all_visible": 195, "development_visible": 77,
                "holdout_progress_visible": 33, "holdout_generic_only": True,
                "alias_visible": 81, "rag_development_visible": 21,
                "rag19_search_visible": 1, "expanded": True}
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "method": "Actual offline Edge; local AI report only; no QA system requests",
              "results": results, "expected": expected, "browser_errors": errors,
              "report_http_requests": remote_requests,
              "status": "PASS" if results == expected and not errors and not remote_requests else "FAIL"}
    (OUT / "report-browser-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
