"""Actual offline review-table integrity and browser checks, without model calls."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from urllib.parse import unquote

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[4]
REPORT = ROOT / "eval/reports/d2-acceptance"
OUT = ROOT / "eval/artifacts/d2/review-table"
spec = importlib.util.spec_from_file_location("builder", ROOT / "scripts/build_d2_review_table.py")
builder = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(builder)
payload = json.loads((REPORT / "unified-review.json").read_text(encoding="utf8"))
rows = payload["rows"]
assert len(rows) == 195
pending = [r for r in rows if r["review"]["status"] == "pending_human_review"]
assert len(pending) == 191
assert all(all(r["review"][k] == "" for k in ("reviewer_A", "reviewer_B", "reviewed_at", "comments")) for r in pending)
holds = [r for r in rows if r["split"] == "holdout"]
assert len(holds) == 33 and all(r["actual"] is None and r["review"]["actual_answer_correctness"] == "deferred_until_D5" for r in holds)
assert len([r for r in rows if r["actual"] is not None]) == 77
assert payload["counts"]["human_gold_accepted"] == payload["counts"]["human_actual_predictions_accepted"] == 0
assert len({r["review_id"] for r in rows}) == 195
assert sum(r["machine_checks"].get("recommendation_only") == "建议通过" for r in rows) == 78
assert sum(r["machine_checks"].get("recommendation_only") == "建议拒绝" for r in rows) == 3
assert all(r["machine_checks"].get("selection_csv_hash_matches", True) for r in rows)
for row in rows:
    for evidence in row["evidence_files"]:
        assert not Path(evidence["path"]).is_absolute()
        assert builder.digest(ROOT / evidence["path"]) == evidence["sha256"]
    if row["actual"]:
        actual_record_ref = row["evidence_files"][1]
        record = json.loads((ROOT / actual_record_ref["path"]).read_text(encoding="utf8").splitlines()[actual_record_ref["line"] - 1])
        assert record["id"] == row["id"]
        assert builder.content_hash(record) == row["hashes"]["actual_response_sha256"]
        response = record.get("response") or {}
        for key in ("answer", "sql", "table", "status", "trace_id"):
            assert row["actual"][key] == response.get(key)
        for copied, raw in zip(row["actual"]["evidences"], response.get("evidences") or [], strict=True):
            assert all(copied[k] == v for k, v in raw.items())
            assert copied["source_file"]["sha256"] == builder.digest(ROOT / copied["source_file"]["path"])
    if row["group"] in builder.DATASETS:
        item = json.loads((ROOT / row["evidence_files"][0]["path"]).read_text(encoding="utf8").splitlines()[row["evidence_files"][0]["line"] - 1])
        assert item["question"] == row["title"]
        if row["group"] != "rag":
            assert item["gold_sql"] == row["expected"]["gold_sql"]
            assert item["gold_result"] == row["expected"]["gold_result"]
        else:
            assert item["answer"] == row["expected"]["answer"]

html_path = REPORT / "unified-review.html"
soup = BeautifulSoup(html_path.read_text(encoding="utf8"), "html.parser")
assert len(soup.select("tr.review-row")) == 195
assert not soup.select("script[src],link[rel=stylesheet],img[src]")
links = [a["href"] for a in soup.select("a[href]")]
for link in links:
    if link.startswith("#"):
        assert soup.find(id=link[1:])
    else:
        assert not link.startswith(("http", "file:", "javascript:"))
        assert (REPORT / unquote(link)).is_file(), link
md = (REPORT / "unified-review.md").read_text(encoding="utf8")
for row in rows:
    assert f'<a id="{builder.anchor(row)}"></a>' in md
    rendered = soup.find(id=builder.anchor(row)).get_text()
    for _, value in builder.readable_details(row):
        assert builder.text_value(value) in rendered

# Isolated preference/fallback and holdout-leak guards; no real records changed.
original_root = builder.ROOT
with tempfile.TemporaryDirectory(prefix="review-table-test-") as temporary:
    builder.ROOT = Path(temporary)
    initial = builder.ROOT / "eval/artifacts/d2/rag/initial/responses.jsonl"
    initial.parent.mkdir(parents=True)
    initial.write_text('{"id":"dev-1","split":"dev"}\n', encoding="utf8")
    sample = [{"id": "dev-1", "split": "dev"}, {"id": "hold-1", "split": "holdout"}]
    assert builder.actual_runs("rag", sample)[1]["phase"] == "initial"
    final = builder.ROOT / "eval/artifacts/d2/rag/final/responses.jsonl"
    final.parent.mkdir(parents=True)
    final.write_text('{"id":"dev-1","split":"dev"}\n', encoding="utf8")
    assert builder.actual_runs("rag", sample)[1]["phase"] == "final"
    final.write_text('{"id":"hold-1","split":"holdout"}\n', encoding="utf8")
    try:
        builder.actual_runs("rag", sample)
    except ValueError as error:
        assert "Non-dev" in str(error)
    else:
        raise AssertionError("Holdout prediction was accepted by the review loader")
builder.ROOT = original_root

browser_errors = []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
    page.on("pageerror", lambda error: browser_errors.append(str(error)))
    page.goto(html_path.as_uri(), wait_until="load")
    assert page.locator("tr.review-row").count() == 195
    page.screenshot(path=str(OUT / "unified-review-overview.png"), full_page=False)
    page.locator("#split").select_option("holdout")
    assert page.locator("tr.review-row:visible").count() == 33
    page.locator("#split").select_option("dev")
    assert page.locator("tr.review-row:visible").count() == 77
    page.locator("#split").select_option("")
    page.locator("#query").fill("rag-25")
    assert page.locator("tr.review-row:visible").count() == 1
    page.locator("#expand").click()
    assert page.locator("tr.review-row:visible details[open]").count() == 1
    page.locator("#rag-rag-25").scroll_into_view_if_needed()
    page.screenshot(path=str(OUT / "unified-review-rag25-expanded.png"), full_page=False)
    page.locator("#collapse").click()
    assert page.locator("details[open]").count() == 0
    assert not browser_errors, browser_errors
    browser.close()

result = {"status": "passed", "pending_rows": 191, "previously_approved_metrics": 4,
          "gold_human_accepted": 0, "actual_dev_predictions": 77, "actual_human_accepted": 0,
          "holdout_cases": 33, "holdout_predictions": 0, "html_rows": 195,
          "relative_links_checked": len(links), "markdown_html_json_same_content": True,
          "raw_actual_fields_and_hashes_equal": True, "reviewer_fields_empty_for_pending": True,
          "isolated_final_preference_initial_fallback_holdout_rejection": True,
          "offline_edge_ui": {"errors": browser_errors, "dev_filter_count": 77,
                              "holdout_filter_count": 33, "search_rag25_count": 1,
                              "expand_and_collapse": "passed"}}
(OUT / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
print(json.dumps(result, ensure_ascii=False, indent=2))
