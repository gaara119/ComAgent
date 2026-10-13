"""Verify grouped review navigation and old-draft compatibility in real Edge.

This uses a fresh disposable browser context. Its seeded draft is explicitly
synthetic, is never a human approval, and is not imported into project data.
No API, model, database, or held-label requests are made.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "eval/reports/oct12/manual-review/全部待人工审核统一入口.html"
SOURCE = DOCUMENT.with_suffix(".json")
CATEGORY_COUNTS = {
    "aliases": 2,
    "sql": 77,
    "join": 15,
    "rag": 21,
    "clarify": 21,
    "special": 60,
    "catalog": 524,
    "shared": 15,
}
SEED_KEY = "alias:a-0c47392129d13dd6"
STORAGE_KEY = "oct12-review-draft-v1"
MARKER = "AUTOMATED_GROUPING_COMPATIBILITY_TEST_ONLY_NOT_HUMAN_APPROVAL"


def expected_category(row: dict) -> str:
    key = row["review_key"]
    if key.startswith("alias:"):
        return "aliases"
    if key.startswith(("sql:", "robust:", "d3:aw-")):
        return "sql"
    if key.startswith("oct12-join:"):
        return "join"
    if key.startswith("rag:"):
        return "rag"
    if key.startswith("d3:clarify-"):
        return "clarify"
    if key.startswith("special:"):
        return "special"
    if row["group"] in {"AW中文目录表说明", "AW中文目录列说明"}:
        return "catalog"
    if key.startswith(("d3:d3-b-", "oct12-diagnostic:", "oct12-ui:")):
        return "shared"
    raise ValueError(f"Unclassified existing review row: {key}")


def digest(value) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def contiguous(values: list[str]) -> bool:
    blocks = [value for n, value in enumerate(values) if n == 0 or value != values[n - 1]]
    return len(blocks) == len(set(blocks))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="eval/artifacts/oct13/review-grouping-browser-v1")
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT) or out.exists():
        raise ValueError("Use a new project-local artifact directory")
    out.mkdir(parents=True)
    source_before = sha256(SOURCE.read_bytes()).hexdigest()
    html_before = sha256(DOCUMENT.read_bytes()).hexdigest()
    original = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = original["rows"]
    by_key = {row["review_key"]: row for row in rows}
    assert len(rows) == len(by_key) == 735
    expected = {key: expected_category(row) for key, row in by_key.items()}
    assert dict(Counter(expected.values())) == CATEGORY_COUNTS
    seeded_row = by_key[SEED_KEY]
    decision = seeded_row["decision_objects"][0]["object"]
    seed = {
        "review_key": SEED_KEY,
        "content_sha256": seeded_row["content_sha256"],
        "decisions": {decision: "证据不足"},
        "version_decisions": {},
        "version_object_decisions": {},
        "question": seeded_row["proposed_question"],
        "label": MARKER + ": label restoration fixture",
        "gold_sql": "",
        "notes": MARKER + ": old storage key and row hash restoration fixture",
    }
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": ".\\.venv\\Scripts\\python.exe -B scripts/check_oct13_review_groups.py --output "
        + out.relative_to(ROOT).as_posix(),
        "scope": "Actual Edge on local grouped review; synthetic disposable draft only; no human approvals or API/model/database/held-label calls",
        "synthetic_marker": MARKER,
        "expected_category_counts": CATEGORY_COUNTS,
        "checks": {},
        "page_errors": [],
        "blocked_network": [],
        "browser_run": "not_run",
    }
    checks = report["checks"]
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
            headless=True,
            args=["--disable-background-networking", "--disable-extensions", "--no-first-run"],
        )
        context = browser.new_context(viewport={"width": 1440, "height": 1080}, accept_downloads=True)
        page = context.new_page()

        def intercept(route):
            if urlparse(route.request.url).scheme in {"file", "data", "about", "blob"}:
                route.continue_()
            else:
                report["blocked_network"].append(route.request.url)
                route.abort()

        page.route("**/*", intercept)
        page.on("pageerror", lambda error: report["page_errors"].append(str(error)))
        page.goto(DOCUMENT.as_uri(), wait_until="load", timeout=30000)
        # Seed only this isolated browser's old storage key, then test restoration.
        # The user's open browser context and its localStorage are never attached.
        page.evaluate("arg => localStorage.setItem(arg.key,JSON.stringify(arg.value))", {"key": STORAGE_KEY, "value": {SEED_KEY: seed}})
        page.reload(wait_until="load")
        dom_rows = page.locator("article.item").evaluate_all(
            "els=>els.map(e=>({key:e.dataset.key,hash:e.dataset.hash,category:e.dataset.category,subgroup:e.dataset.subgroup,originalNumber:e.dataset.originalNumber,group:e.dataset.group,heading:e.querySelector('h2').textContent}))"
        )
        report["actual_category_counts"] = dict(Counter(row["category"] for row in dom_rows))
        report["article_count"] = len(dom_rows)
        checks["all_735_original_keys_once"] = len(dom_rows) == 735 and Counter(row["key"] for row in dom_rows) == Counter(list(by_key))
        checks["all_row_hashes_unchanged"] = all(row["hash"] == by_key[row["key"]]["content_sha256"] for row in dom_rows)
        checks["all_original_groups_unchanged"] = all(row["group"] == by_key[row["key"]]["group"] for row in dom_rows)
        checks["classification_matches_independent_original_key_rules"] = all(row["category"] == expected[row["key"]] for row in dom_rows)
        checks["all_categories_are_contiguous"] = contiguous([row["category"] for row in dom_rows])
        checks["category_display_order"] = list(dict.fromkeys(row["category"] for row in dom_rows)) == list(CATEGORY_COUNTS)
        checks["subtypes_present_and_contiguous"] = all(row.get("subgroup") for row in dom_rows) and contiguous([row["category"] + ":" + row["subgroup"] for row in dom_rows])
        original_ordinals = {row["review_key"]: i + 1 for i, row in enumerate(rows)}
        checks["original_display_numbers_unchanged"] = all(
            re.match(r"\s*(?:原序号)?(\d+)\.", row["heading"])
            and int(re.match(r"\s*(?:原序号)?(\d+)\.", row["heading"]).group(1)) == original_ordinals[row["key"]]
            and int(row["originalNumber"]) == original_ordinals[row["key"]]
            for row in dom_rows
        )
        report["dom_order"] = dom_rows
        sections = page.locator("section.review-category").evaluate_all(
            "els=>els.map(e=>({id:e.id,category:e.dataset.category,count:e.querySelectorAll('article.item').length}))"
        )
        report["category_sections"] = sections
        checks["eight_sections_cover_every_row"] = len(sections) == 8 and all(
            section["id"] == "review-type-" + section["category"]
            and section["count"] == CATEGORY_COUNTS[section["category"]]
            for section in sections
        )
        checks["no_articles_outside_categories"] = page.locator("article.item").evaluate_all("els=>els.every(e=>e.closest('section.review-category')!==null)")
        seeded_article = page.locator('article[data-key="' + SEED_KEY + '"]')
        checks["old_draft_notes_restored"] = seeded_article.locator('textarea[data-field="notes"]').input_value() == seed["notes"]
        checks["old_draft_label_restored"] = seeded_article.locator('textarea[data-field="label"]').input_value() == seed["label"]
        checks["old_draft_decision_restored"] = seeded_article.locator('select[data-object="' + decision + '"]').input_value() == "证据不足"
        checks["old_storage_key_retained"] = page.evaluate("key=>localStorage.getItem(key)!==null", STORAGE_KEY)
        page.screenshot(path=str(out / "overview-grouped.png"), full_page=False)
        report["category_filter_counts"] = {}
        report["category_navigation"] = {}

        for category, count in CATEGORY_COUNTS.items():
            page.locator("#type").select_option(category)
            visible = page.locator("article.item:visible").evaluate_all("els=>els.map(e=>({key:e.dataset.key,category:e.dataset.category}))")
            report["category_filter_counts"][category] = len(visible)
            checks["filter_" + category] = len(visible) == count and all(row["category"] == category for row in visible)
            # Dirty all filters before navigation; clicking a category must clear
            # the stale text and original group filter, otherwise users see 0 rows.
            page.locator("#search").fill("AUTOMATED_NO_MATCH_QUERY")
            page.locator("#group").select_option("D2别名待定")
            page.locator('a[data-jump-category="' + category + '"]').first.click()
            nav = {
                "type": page.locator("#type").input_value(),
                "search": page.locator("#search").input_value(),
                "group": page.locator("#group").input_value(),
                "visible": page.locator("article.item:visible").count(),
                "target_exists": page.locator("#review-type-" + category).count() == 1,
            }
            report["category_navigation"][category] = nav
            checks["navigation_" + category] = nav == {"type": category, "search": "", "group": "", "visible": count, "target_exists": True}
            position = page.evaluate("key=>({headingTop:document.querySelector('#review-type-'+key+' .category-heading').getBoundingClientRect().top,toolbarBottom:document.querySelector('.bar').getBoundingClientRect().bottom})", category)
            report["category_navigation"][category]["heading_position"] = position
            checks["navigation_heading_uncovered_" + category] = position["headingTop"] >= position["toolbarBottom"] - 1
            if category == "catalog":
                page.screenshot(path=str(out / "catalog-navigation-title.png"), full_page=False)

        page.set_viewport_size({"width": 900, "height": 1080})
        page.locator('a[data-jump-category="sql"]').first.click()
        narrow = page.evaluate("({headingTop:document.querySelector('#review-type-sql .category-heading').getBoundingClientRect().top,toolbarBottom:document.querySelector('.bar').getBoundingClientRect().bottom,width:innerWidth,scrollWidth:document.documentElement.scrollWidth})")
        report["narrow_navigation_layout"] = narrow
        checks["narrow_navigation_title_uncovered"] = narrow["headingTop"] >= narrow["toolbarBottom"] - 1
        checks["narrow_no_horizontal_overflow"] = narrow["scrollWidth"] <= narrow["width"]
        page.screenshot(path=str(out / "sql-navigation-900px.png"), full_page=False)
        page.set_viewport_size({"width": 1440, "height": 1080})

        page.locator("#show-all").click()
        checks["show_all_restores_735_and_clears_filters"] = (
            page.locator("article.item:visible").count() == 735
            and all(page.locator(selector).input_value() == "" for selector in ("#type", "#group", "#search"))
        )
        page.locator("#type").select_option("catalog")
        page.locator("#group").select_option("AW中文目录列说明")
        report["aw_columns_filtered"] = page.locator("article.item:visible").count()
        checks["old_group_filter_columns_456"] = report["aw_columns_filtered"] == 456
        page.screenshot(path=str(out / "aw-columns-grouped.png"), full_page=False)
        page.locator("#group").select_option("AW中文目录表说明")
        report["aw_tables_filtered"] = page.locator("article.item:visible").count()
        checks["old_group_filter_tables_68"] = report["aw_tables_filtered"] == 68
        page.locator("#show-all").click()
        page.locator("#type").select_option("sql")
        page.locator("#search").fill("sql:sql-38")
        report["sql38_search_keys"] = page.locator("article.item:visible").evaluate_all("els=>els.map(e=>e.dataset.key)")
        checks["sql38_search_within_SQL_group"] = report["sql38_search_keys"] == ["sql:sql-38"]
        page.screenshot(path=str(out / "sql38-grouped-search.png"), full_page=False)
        # Keep the filter active: exporting must still include every review row.
        with page.expect_download() as captured:
            page.locator("#export").click()
        exported_path = out / "synthetic-compatibility-export-not-human-approval.json"
        captured.value.save_as(str(exported_path))
        exported = json.loads(exported_path.read_text(encoding="utf-8"))
        records = {row["review_key"]: row for row in exported["records"]}
        checks["filtered_export_still_contains_all_735_original_keys"] = len(exported["records"]) == len(records) == 735 and set(records) == set(by_key)
        checks["export_hashes_unchanged"] = all(row["content_sha256"] == by_key[key]["content_sha256"] for key, row in records.items())
        checks["dataset_hash_preserves_original_ordered_material"] = exported["dataset_sha256"] == digest(rows)
        checks["seeded_old_draft_preserved_in_export"] = all(records[SEED_KEY][field] == seed[field] for field in ("notes", "label", "decisions", "question", "gold_sql"))
        checks["no_fabricated_signatures_or_automatic_application"] = exported["human_signature"] is None and exported["human_confirmation_date"] is None and exported["automatic_application"] is False
        report["export_records"] = len(records)
        report["export_dataset_sha256"] = exported["dataset_sha256"]
        page.reload(wait_until="load")
        checks["old_draft_survives_second_refresh"] = seeded_article.locator('textarea[data-field="notes"]').input_value() == seed["notes"]
        report["layout"] = page.evaluate("({width:innerWidth,scrollWidth:document.documentElement.scrollWidth})")
        checks["no_horizontal_overflow"] = report["layout"]["scrollWidth"] <= report["layout"]["width"]
        report["browser_run"] = "actual_Edge_headless_complete"
        context.close()
        browser.close()

    checks["source_JSON_unmodified"] = sha256(SOURCE.read_bytes()).hexdigest() == source_before
    checks["source_HTML_unmodified_by_checker"] = sha256(DOCUMENT.read_bytes()).hexdigest() == html_before
    checks["no_browser_errors"] = not report["page_errors"]
    checks["no_external_requests"] = not report["blocked_network"]
    report["passed"] = all(checks.values())
    report["failed_checks"] = [name for name, passed in checks.items() if not passed]
    (out / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("passed", "article_count", "export_records", "actual_category_counts", "failed_checks", "page_errors")}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
