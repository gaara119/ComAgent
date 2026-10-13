"""Verify local review rendering/edit/export; synthetic decisions never applied."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / 'eval/reports/oct12/manual-review/全部待人工审核统一入口.html'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('href'):
            self.hrefs.append(attrs['href'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='eval/artifacts/oct12/manual-review-ui-v1')
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT) or out.exists():
        raise ValueError('Use a new project-local artifact directory')
    out.mkdir(parents=True)
    content_before = sha256(DOCUMENT.read_bytes()).hexdigest()
    parsed = Links()
    parsed.feed(DOCUMENT.read_text(encoding='utf-8'))
    links = []
    for href in sorted(set(parsed.hrefs)):
        url = urlparse(href)
        if not url.path and not url.scheme and not url.netloc and url.fragment:
            links.append({'href': href, 'relative': True, 'inside_project': True, 'exists': unquote(url.fragment) in parsed.ids, 'kind': 'document_anchor'})
            continue
        target = (DOCUMENT.parent / unquote(url.path)).resolve()
        links.append({'href': href, 'relative': not url.scheme and not url.netloc and not url.path.startswith(('/', '\\')), 'inside_project': target.is_relative_to(ROOT), 'exists': target.is_file()})
    report = {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'command': '.\\.venv\\Scripts\\python.exe -B scripts/check_oct12_review.py --output ' + out.relative_to(ROOT).as_posix(), 'scope': 'Local file UI and synthetic draft export only, no API/model/database requests; not human approval', 'links': links, 'page_errors': [], 'blocked_network': [], 'browser_run': 'not_run'}
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless=True, args=['--disable-background-networking','--disable-extensions','--no-first-run'])
        context = browser.new_context(viewport={'width':1440, 'height':1080}, accept_downloads=True)
        page = context.new_page()
        def intercept(route):
            if urlparse(route.request.url).scheme in {'file','data','about'}:
                route.continue_()
            else:
                report['blocked_network'].append(route.request.url)
                route.abort()
        page.route('**/*', intercept)
        page.on('pageerror', lambda e: report['page_errors'].append(str(e)))
        page.goto(DOCUMENT.as_uri(), wait_until='load', timeout=30000)
        page.screenshot(path=str(out / 'first-view.png'), full_page=False)
        report['article_count'] = page.locator('article.item').count()
        report['original_special_ids_count'] = page.locator('article[data-key^="special:"]').count()
        page.locator('#search').fill('sql:sql-38')
        visible = page.locator('article.item:visible')
        report['filter_visible_keys'] = visible.evaluate_all('els => els.map(e=>e.dataset.key)')
        article = page.locator('article[data-key="sql:sql-38"]')
        article.locator('details').first.evaluate('el=>el.open=true')
        page.screenshot(path=str(out / 'sql-38-proposal-default-pending.png'), full_page=False)
        article.locator('textarea[data-field="notes"]').fill('AUTOMATED_DEMO_ONLY: synthetic export test, not human approval.')
        article.locator('textarea[data-field="notes"]').dispatch_event('change')
        article.locator('select').first.select_option('有条件通过')
        version_article = page.locator('article.item').filter(has=page.locator('select[data-version]')).first
        version_selector = version_article.locator('select[data-version]').first
        version_key = version_article.get_attribute('data-key')
        version_hash = version_selector.get_attribute('data-version')
        version_selector.select_option('历史归档，不启用', force=True)
        rag_article = page.locator('article[data-key^="rag:"]').first
        rag_dimension = rag_article.locator('select[data-version-object]').first
        rag_key = rag_article.get_attribute('data-key')
        rag_hash = rag_dimension.get_attribute('data-version')
        rag_selections = {'答案正确性':'通过','引用语义支持':'证据不足','引用定位':'拒绝/发现错误'}
        for dimension, value in rag_selections.items():
            rag_article.locator('select[data-version="' + rag_hash + '"][data-version-object="' + dimension + '"]').select_option(value, force=True)
        rag_article.locator('textarea[data-field="notes"]').evaluate("el=>{el.value='AUTOMATED_DEMO_ONLY: independent answer/citation dimension export test, not human approval.';el.dispatchEvent(new Event('change',{bubbles:true}));}")
        page.screenshot(path=str(out / 'sql-38-filtered.png'), full_page=False)
        with page.expect_download() as captured:
            page.locator('#export').click()
        download = captured.value
        export_path = out / 'synthetic-export-not-human-approval.json'
        download.save_as(str(export_path))
        exported = json.loads(export_path.read_text(encoding='utf-8'))
        exported_row = next(r for r in exported['records'] if r['review_key']=='sql:sql-38')
        exported_version_row = next(r for r in exported['records'] if r['review_key']==version_key)
        exported_rag_row = next(r for r in exported['records'] if r['review_key']==rag_key)
        report['export_records'] = len(exported['records'])
        report['synthetic_export_test'] = {'notes_preserved': 'AUTOMATED_DEMO_ONLY' in exported_row['notes'], 'decision_preserved': '有条件通过' in exported_row['decisions'].values(), 'individual_version_decision_preserved': exported_version_row['version_decisions'][version_hash] == '历史归档，不启用', 'rag_answer_support_location_separate':exported_rag_row['version_object_decisions'][rag_hash] == rag_selections,'sql38_proposed_gold_prefilled': 'bytes IS NOT NULL' in exported_row['gold_sql'], 'human_signature_null': exported['human_signature'] is None, 'human_confirmation_date_null': exported['human_confirmation_date'] is None, 'automatic_application_false': exported['automatic_application'] is False}
        page.reload(wait_until='load')
        persisted = page.locator('article[data-key="sql:sql-38"] textarea[data-field="notes"]').input_value()
        report['synthetic_browser_localstorage_persistence'] = 'AUTOMATED_DEMO_ONLY' in persisted
        report['synthetic_rag_independent_choices_persisted'] = all(page.locator('article[data-key="' + rag_key + '"] select[data-version="' + rag_hash + '"][data-version-object="' + dimension + '"]').input_value()==value for dimension,value in rag_selections.items())
        page.locator('#search').fill('')
        page.locator('#group').select_option('AW中文目录列说明')
        columns_visible = page.locator('article.item:visible').count()
        page.screenshot(path=str(out / 'aw-all-columns-filter.png'), full_page=False)
        page.locator('#group').select_option('AW中文目录表说明')
        tables_visible = page.locator('article.item:visible').count()
        report['all_pending_aw_catalog_group_counts'] = {'columns':columns_visible,'tables':tables_visible,'expected_complete_68_plus_456':columns_visible==456 and tables_visible==68}
        page.locator('#group').select_option('')
        report['visible_after_clear'] = page.locator('article.item:visible').count()
        report['layout'] = page.evaluate('({innerWidth:innerWidth,scrollWidth:document.documentElement.scrollWidth})')
        report['browser_run'] = 'actual_Edge_headless_complete'
        context.close()
        browser.close()
    report['source_html_unchanged'] = sha256(DOCUMENT.read_bytes()).hexdigest() == content_before
    report['passed'] = all(x['relative'] and x['inside_project'] and x['exists'] for x in links) and not report['page_errors'] and not report['blocked_network'] and report['article_count'] == report['export_records'] == report['visible_after_clear'] and report['original_special_ids_count'] == 60 and report['filter_visible_keys'] == ['sql:sql-38'] and all(report['synthetic_export_test'].values()) and report['source_html_unchanged'] and report['synthetic_browser_localstorage_persistence'] and report['synthetic_rag_independent_choices_persisted'] and report['all_pending_aw_catalog_group_counts']['expected_complete_68_plus_456']
    (out / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['passed','article_count','export_records','filter_visible_keys','source_html_unchanged','page_errors']}, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
