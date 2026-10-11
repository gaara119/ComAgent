"""Static links and actual local Edge layout check, with no API/model requests."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
EXP = "eval/experiments/after_d2_01_03"
EXPECTED = {f"sp{task}-{n:02}" for task in ("01", "03") for n in range(1, 31)}


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.articles = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.hrefs.append(attrs["href"])
        if tag == "article":
            self.articles.append(attrs.get("id"))


def local(name: str) -> Path:
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or path.name.startswith(".env"):
        raise ValueError("Layout evidence stays within the project, excluding private environment files")
    return path


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document", required=True)
    parser.add_argument("--output", required=True, help="Fresh relative directory below reports/layout-check")
    parser.add_argument("--kind", choices=["review", "acceptance"], default="review")
    parser.add_argument("--filter-id", default="sp03-27")
    parser.add_argument("--edge", default="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    document, output = local(args.document), local(args.output)
    if not document.is_file():
        raise FileNotFoundError("Actual HTML report not found")
    if not output.is_relative_to(local(EXP + "/reports/layout-check")):
        raise ValueError("Use a directory under the independent layout evidence root")
    if output.exists():
        raise ValueError("Preserve earlier screenshots/logs; choose a fresh output directory")
    output.mkdir(parents=True)
    before = digest(document)
    parsed = PageLinks()
    parsed.feed(document.read_text(encoding="utf-8-sig"))
    links = []
    for href in sorted(set(parsed.hrefs)):
        url = urlparse(href)
        relative = not url.scheme and not url.netloc and not url.path.startswith(("/", "\\"))
        target = (document.parent / unquote(url.path)).resolve()
        exists = target.is_file() if url.path else document.is_file()
        inside = target.is_relative_to(ROOT)
        links.append({"href": href, "relative": relative, "target_inside_project": inside,
                      "target": target.relative_to(ROOT).as_posix() if inside else "outside_project",
                      "actual_file_exists": exists if inside else False})
    checks = {
        "all_href_relative": all(link["relative"] for link in links),
        "all_href_files_exist_inside_project": all(link["actual_file_exists"] and link["target_inside_project"] for link in links),
    }
    if args.kind == "review":
        checks["exact60_original_article_ids"] = len(parsed.articles) == 60 and set(parsed.articles) == EXPECTED
    result = {"purpose": "Local HTML link and browser layout evidence only; not a question-answering functional/API test",
              "created_at_utc": datetime.now(timezone.utc).isoformat(), "document": args.document,
              "kind": args.kind, "document_sha256_before": before,
              "command": [sys.executable, "-B", *sys.argv], "cwd": "system",
              "href_occurrences": len(parsed.hrefs), "distinct_href_files": len(links),
              "actual_article_count": len(parsed.articles), "article_ids": parsed.articles,
              "static_checks": checks, "links": links, "browser_state": "NOT_RUN",
              "page_errors": [], "console_errors": [], "blocked_network_requests": [],
              "browser_requests": [], "screenshots": [], "new_API_requests": 0, "new_model_calls": 0,
              "new_SQL_queries": 0, "human_review_status": "pending_human_review"}
    def save():
        result["document_sha256_after"] = digest(document)
        result["document_unchanged"] = result["document_sha256_after"] == before
        (output / "report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save()
    if not args.static_only:
        from playwright.sync_api import sync_playwright
        try:
            result["browser_state"] = "STARTING_EDGE_HEADLESS"
            save()
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=args.edge, headless=True,
                    timeout=15000,
                    args=["--disable-background-networking", "--disable-extensions", "--disable-default-apps", "--no-first-run", "--no-default-browser-check"])
                result["actual_browser_version"] = browser.version
                context = browser.new_context(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
                page = context.new_page()
                def intercept(route):
                    url = route.request.url
                    result["browser_requests"].append(url)
                    if urlparse(url).scheme in {"file", "data", "about"}:
                        route.continue_()
                    else:
                        result["blocked_network_requests"].append(url)
                        route.abort()
                page.route("**/*", intercept)
                page.on("pageerror", lambda error: result["page_errors"].append(str(error)))
                page.on("console", lambda message: result["console_errors"].append(message.text) if message.type == "error" else None)
                page.goto(document.as_uri(), wait_until="load", timeout=30000)
                page.evaluate("document.fonts.ready")
                page.screenshot(path=str(output / "first-view.png"), full_page=False)
                result["screenshots"].append({"file": (output / "first-view.png").relative_to(ROOT).as_posix(),
                                               "sha256": digest(output / "first-view.png"), "state": "Actual local first viewport"})
                result["actual_title"] = page.title()
                if args.kind == "review":
                    page.locator("#filter").fill(args.filter_id)
                    page.wait_for_function("id => [...document.querySelectorAll('article')].filter(e=>!e.hidden).length===1 && !document.getElementById(id).hidden", arg=args.filter_id, timeout=5000)
                    visible = page.locator("article:visible").evaluate_all("els=>els.map(e=>e.id)")
                    result["actual_filter"] = {"input": args.filter_id, "visible_article_ids": visible,
                                               "expected_unique_article_visible": visible == [args.filter_id]}
                    page.locator("#" + args.filter_id).evaluate("el=>el.scrollIntoView({block:'start'})")
                    page.screenshot(path=str(output / "filtered-sp03-27.png"), full_page=False)
                    result["screenshots"].append({"file": (output / "filtered-sp03-27.png").relative_to(ROOT).as_posix(),
                                                   "sha256": digest(output / "filtered-sp03-27.png"), "state": "Actual filter sp03-27; expected single original case visible"})
                    result["filter_layout_metrics"] = page.evaluate("({innerWidth:innerWidth,scrollWidth:document.documentElement.scrollWidth})")
                    page.locator("#filter").fill("")
                    result["all_cases_restored_after_clear"] = page.locator("article:visible").count() == 60
                result["browser_state"] = "ACTUAL_EDGE_HEADLESS_COMPLETED"
                result["first_view_layout_metrics"] = page.evaluate("({innerWidth:innerWidth,scrollWidth:document.documentElement.scrollWidth})")
                browser.close()
        except Exception as error:
            result["browser_state"] = "FAILED"
            result["browser_error"] = str(error)
            save()
            print(json.dumps({"browser_state": result["browser_state"], "error": str(error), "static_checks": checks}, ensure_ascii=False))
            return 2
    result["document_sha256_after"] = digest(document)
    result["document_unchanged"] = result["document_sha256_after"] == before
    passed = all(checks.values()) and result["document_unchanged"]
    if not args.static_only:
        passed = (passed and result["browser_state"] == "ACTUAL_EDGE_HEADLESS_COMPLETED" and not result["page_errors"]
                  and not result["blocked_network_requests"]
                  and (args.kind != "review" or result.get("actual_filter", {}).get("expected_unique_article_visible") is True))
    result["status"] = "PASS" if passed else "FAILED"
    save()
    print(json.dumps({key: result.get(key) for key in ["status", "href_occurrences", "distinct_href_files", "actual_article_count", "static_checks", "browser_state", "actual_filter", "blocked_network_requests", "document_unchanged", "screenshots"]}, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print("Local report layout check failed: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
