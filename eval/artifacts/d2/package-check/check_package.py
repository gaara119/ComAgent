"""Independent, isolated inspection of the D2 evidence ZIP; no project mutations."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
from urllib.parse import unquote, urlparse
import zipfile

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "eval/artifacts/d2/package-check"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_rows(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=ROOT.parent / "D2原清单九项验收与证据.zip")
    args = parser.parse_args()
    archive = args.zip.resolve()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    unpack = (ROOT / ".runtime" / f"d2-unpack-review-{timestamp}").resolve()
    assert unpack.is_relative_to((ROOT / ".runtime").resolve())
    assert not unpack.exists()
    OUT.mkdir(parents=True, exist_ok=True)
    initial_sha = sha(archive)
    findings = []
    forbidden = []
    secret_paths = []
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        assert bundle.testzip() is None, "ZIP CRC error"
        assert len({entry.filename for entry in members}) == len(members)
        for entry in members:
            raw = entry.filename.replace("\\", "/")
            path = PurePosixPath(raw)
            assert not path.is_absolute() and ".." not in path.parts and ":" not in raw
            assert not stat.S_ISLNK(entry.external_attr >> 16)
            target = (unpack / raw).resolve()
            assert target.is_relative_to(unpack)
            parts = {part.lower() for part in path.parts}
            if (parts & {".venv", "venv", ".git", ".runtime", "pgdata", "postgres-data"}
                    or raw.lower().startswith("data/models/") or path.name.lower().endswith(".env")
                    or path.suffix.lower() in {".safetensors", ".ckpt", ".pt", ".pth", ".onnx"}):
                forbidden.append(raw)
            if path.suffix.lower() in {".py", ".md", ".json", ".jsonl", ".txt", ".yaml", ".yml", ".html", ".csv", ".ps1", ".example"}:
                text = bundle.read(entry).decode("utf8", errors="replace")
                if re.search(r"\bsk-[A-Za-z0-9_-]{20,}\b", text):
                    secret_paths.append(raw)
        assert not forbidden, f"Forbidden package paths: {forbidden}"
        assert not secret_paths, f"Possible API key content in: {secret_paths}"
        unpack.mkdir(parents=True, exist_ok=False)
        bundle.extractall(unpack)
        entry_count = len(members)

    root_html = unpack / "D2 原清单九项逐项验收与证据.html"
    nested_html = unpack / "eval/reports/d2-acceptance/requested-d2-evidence.html"
    review_html = unpack / "eval/reports/d2-acceptance/unified-review.html"
    report = read_json(unpack / "eval/reports/d2-acceptance/requested-d2-evidence.json")
    review = read_json(unpack / "eval/reports/d2-acceptance/unified-review.json")
    link_counts = {}
    for document in (root_html, nested_html, review_html):
        soup = BeautifulSoup(document.read_text(encoding="utf8"), "html.parser")
        assert not soup.select("script[src],link[rel=stylesheet]")
        links = [node["href"] for node in soup.select("a[href]")]
        for link in links:
            parsed = urlparse(link)
            if parsed.scheme in {"http", "https"}:
                continue  # Primary/public URLs are not packaged evidence.
            assert parsed.scheme == "" and not link.startswith(("/", "\\")), link
            if not parsed.path:
                assert soup.find(id=unquote(parsed.fragment)), link
                continue
            target = (document.parent / unquote(parsed.path)).resolve()
            assert target.is_relative_to(unpack), link
            assert target.exists(), f"Broken link in {document.relative_to(unpack)}: {link}"
        link_counts[document.relative_to(unpack).as_posix()] = len(links)

    md = (unpack / "eval/reports/d2-acceptance/requested-d2-evidence.md").read_text(encoding="utf8")
    sections = re.split(r"(?m)^## (D2-0[1-9] / [AB][1-5])\s*$", md)
    assert len(sections) == 19
    nine_items = []
    for i in range(1, len(sections), 2):
        title, body = sections[i], sections[i + 1]
        required = ["要求", "实现情况", "改动文件", "测试方法与实际结果", "证据位置", "未完成事项 / 口径限制"]
        checks = {field: f"**{field}：**" in body for field in required}
        assert all(checks.values()), (title, checks)
        nine_items.append({"item": title, "required_fields_present": checks})
    assert report["status"] == "ENGINEERING_PASS_HUMAN_REVIEW_PENDING"
    assert report["review"] == review["counts"]
    assert review["counts"]["pending_rows"] == 191 and review["counts"]["previously_approved_metrics"] == 4
    assert review["counts"]["human_gold_accepted"] == review["counts"]["human_actual_predictions_accepted"] == 0
    holds = [row for row in review["rows"] if row["split"] == "holdout"]
    assert len(holds) == 33 and all(row["actual"] is None for row in holds)
    assert report["holdout_prediction_count"] == 0
    assert "正式成绩尚未发布" in md and "人工正确性、忠实度仍待审核" in md
    assert "工作区有 D2 增量" in md and "没有把此前77题改称在修复后重新运行" in md
    pending = [row for row in review["rows"] if row["review"]["status"] == "pending_human_review"]
    assert len(pending) == 191
    assert all(all(row["review"][field] == "" for field in ("reviewer_A", "reviewer_B", "reviewed_at", "comments")) for row in pending)
    for row in review["rows"]:
        for evidence in row["evidence_files"]:
            assert sha(unpack / evidence["path"]) == evidence["sha256"]

    sql_rows = read_rows(unpack / "eval/artifacts/d2/nl2sql/final/responses.jsonl")
    robust_rows = read_rows(unpack / "eval/artifacts/d2/robust/final/responses.jsonl")
    rag_rows = read_rows(unpack / "eval/artifacts/d2/rag/final/responses.jsonl")
    assert len(sql_rows) == 35 and sum(row["matched"] for row in sql_rows) == 35
    assert len(robust_rows) == 21 and sum(row["matched"] for row in robust_rows) == 21
    assert len(rag_rows) == 21
    answerable = [row for row in rag_rows if row["answerable"]]
    insufficient = [row for row in rag_rows if not row["answerable"]]
    assert len(answerable) == 20 and all(row["metrics"]["hit_at_5"] for row in answerable)
    assert len(insufficient) == 1 and insufficient[0]["metrics"]["insufficient_correct"]
    assert all(row["split"] == "dev" for row in sql_rows + robust_rows + rag_rows)
    module_cmd = read_json(unpack / report["modules"]["command_record"])
    module_output = (unpack / module_cmd["output"]).read_text(encoding="utf8")
    assert module_cmd["exit_code"] == 0 and re.search(r"\b281 passed\b", module_output)
    engineering = read_json(unpack / "eval/reports/d2-acceptance/engineering.json")
    assert engineering["passed"] == engineering["total"] == 58
    assert len(engineering["checks"]) == 58 and all(check["passed"] for check in engineering["checks"])
    ui = read_json(unpack / "eval/artifacts/d2/e2e/browser/d2-live-final/report.json")
    assert len(ui["cases"]) == 5 and ui["status"] == "PASSED" and not ui["browser_errors"]
    for case in ui["cases"]:
        assert (unpack / case["screenshot"]).is_file()
        assert case["status"] == "PASSED"
        assert case["rerun_verification"]["api_posts_before_toggle"] == case["rerun_verification"]["api_posts_after_toggle"] == 1

    errors = []
    clicks = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1080}, accept_downloads=True)
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(root_html.as_uri(), wait_until="load")
        assert page.locator("h1").inner_text() == "D2 原清单九项逐项验收与证据"
        assert sum(re.match(r"D2-0[1-9] /", header) is not None for header in page.locator("h2").all_inner_texts()) == 9
        page.screenshot(path=str(OUT / "package-root-report.png"), full_page=False)
        png_href = "notes/screenshots/D2-d2-live-final-sql.png"
        png = unpack / png_href
        page.locator(f'a[href="{png_href}"]').click()
        page.wait_for_load_state("load")
        assert page.url == png.as_uri()
        assert page.locator("img").evaluate("img => img.naturalWidth > 0")
        page.screenshot(path=str(OUT / "package-png-link-opened.png"), full_page=False)
        clicks.append({"kind": "png", "href": png_href, "actual": "browser rendered unpacked image", "sha256": sha(png)})
        page.goto(root_html.as_uri(), wait_until="load")
        source_href = "scripts/build_value_index.py"
        source_path = unpack / source_href
        downloaded = []
        page.on("download", lambda download: downloaded.append(download))
        page.locator(f'a[href="{source_href}"]').click()
        page.wait_for_timeout(400)
        if downloaded:
            downloaded_path = Path(downloaded[0].path())
            assert sha(downloaded_path) == sha(source_path)
            mode = "browser downloaded source; downloaded bytes match packaged file"
        else:
            assert page.url == source_path.as_uri()
            assert "value" in page.locator("body").inner_text().lower()
            mode = "browser opened unpacked source as text"
        assert source_path.read_text(encoding="utf8").strip()
        clicks.append({"kind": "source", "href": source_href, "actual": mode, "sha256": sha(source_path)})
        page.goto(root_html.as_uri(), wait_until="load")
        review_href = "eval/reports/d2-acceptance/unified-review.html"
        page.locator(f'a[href="{review_href}"]').first.click()
        page.wait_for_load_state("load")
        assert page.url == review_html.as_uri()
        assert page.locator("tr.review-row").count() == 195
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
        page.screenshot(path=str(OUT / "package-unified-review.png"), full_page=False)
        assert not errors, errors
        browser.close()

    assert sha(archive) == initial_sha, "Archive changed during isolated inspection"
    result = {"status": "PASSED", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "method": "independent isolated safe extraction + actual offline Edge + raw evidence comparison",
              "archive": archive.name, "archive_sha256": initial_sha, "archive_entries": entry_count,
              "archive_size_bytes": archive.stat().st_size,
              "scope_note": "This is the archive inspected before these package-check artifacts are added to the final delivery ZIP.",
              "isolated_extraction": unpack.relative_to(ROOT).as_posix(), "zip_crc": "passed",
              "relative_evidence_links": link_counts, "nine_checklist_items": nine_items,
              "review": {"pending": 191, "already_approved_metrics": 4, "gold_human_accepted": 0,
                         "actual_dev_predictions": 77, "actual_human_accepted": 0,
                         "holdout_cases": 33, "holdout_predictions": 0},
              "raw_results": {"sql": "35/35", "robust": "21/21", "rag_hit_at_5": "20/20",
                              "rag_insufficient": "1/1", "modules": 281, "engineering": "58/58", "ui_screenshots": 5},
              "offline_browser": {"errors": errors, "clicked_links": clicks,
                                  "review_rows": 195, "dev_filter": 77, "holdout_filter": 33,
                                  "search_and_expand": "passed"},
              "excluded_sensitive_or_runtime_paths": forbidden, "possible_api_key_content_paths": secret_paths,
              "human_review_not_falsely_claimed": True, "findings": findings}
    (OUT / "report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    summary = ["# D2 交付包独立检查", "", f"实际检查时间：{result['checked_at_utc']}。结果：**PASSED**。", "",
               f"受检 ZIP：`{archive.name}`；SHA-256 `{initial_sha}`；{entry_count} 个条目。",
               "本记录检查的是添加本次检查证据前的 ZIP；最终重新打包会产生新的 ZIP 哈希。", "",
               "安全解压至 system/.runtime 的新隔离目录，解压树不进入交付包。九项均含要求、实现、改动、测试实测、证据与限制。",
               "根报告、嵌套报告、统一审核表的相对证据链接均存在；真实 Edge 离线打开，实际点击截图与源码，内容有效。",
               "191 项待审＋4 项既有明确确认；110 gold 和 77 dev 答案的人审接受均为 0；33 保留题模型预测 0，未冒签。",
               "直接核对原始结果：SQL35/35、鲁棒21/21、RAG可答Hit@5 20/20＋不足1/1、模块281通过、工程58/58、5张实测场景截图。",
               "未发现真实 .env、虚拟环境、模型权重或可疑完整 API key。未改报告、源码或原始记录。", "",
               "细节见同目录 report.json；截图见 package-root-report.png、package-png-link-opened.png、package-unified-review.png。"]
    (OUT / "report.md").write_text("\n".join(summary) + "\n", encoding="utf8")
    print(json.dumps({key: result[key] for key in ("status", "archive_sha256", "archive_entries", "relative_evidence_links", "review", "raw_results", "findings")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
