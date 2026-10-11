"""One explicit synthetic DEV API observation plus an independent read-only check.

This is supplemental evidence, never a replacement for the frozen 60-case score.
The question is supplied once; there are no retries or gold sent to the API.
"""
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import httpx
    from qa_agent.config import get_settings
    from qa_agent.sql.catalog import load_catalog
    from qa_agent.sql.executor import execute_sql
    from qa_agent.sql.validator import validate_sql
    output = ROOT / 'eval/experiments/after_d2_01_03/regression/final/ratio-live-001'
    if output.exists():
        raise RuntimeError('Use a fresh observation; never overwrite evidence')
    output.mkdir(parents=True)
    request = {'session_id': 'special-v2-independent-' + uuid4().hex,
               'message': '2024年法国居住客户的销售额占2024年所有发票销售额是多少？',
               'scope': {'route': 'sql', 'db_id': 'chinook', 'doc_ids': []}}
    def save(name, value):
        with (output / name).open('x', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
    save('request.json', request)
    started = datetime.now(timezone.utc).isoformat()
    with httpx.Client(timeout=240, trust_env=False, transport=httpx.HTTPTransport(retries=0)) as client:
        raw = client.post('http://127.0.0.1:8000/api/chat', json=request)
        (output / 'response.raw.json').write_bytes(raw.content)
        response = raw.json()
    settings = get_settings()
    sql = """SELECT SUM(CASE WHEN c.country='France' THEN i.total ELSE 0 END) AS france_revenue,
                     SUM(i.total) AS all_invoice_revenue,
                     SUM(CASE WHEN c.country='France' THEN i.total ELSE 0 END)/NULLIF(SUM(i.total),0) AS share_fraction
              FROM public.invoice i JOIN public.customer c ON i.customer_id=c.customer_id
              WHERE i.invoice_date>=DATE '2024-01-01' AND i.invoice_date<DATE '2025-01-01'"""
    checked = validate_sql(sql, load_catalog(settings.catalog_path), max_rows=settings.max_rows)
    reference = execute_sql(checked.sql, settings.db_url, settings.statement_timeout_ms, settings.max_rows)
    row = reference.table[0]
    fraction = Decimal(row['share_fraction'])
    # Unit correctness requires reading the actual column/answer. These numbers
    # are reference units, not an automatic acceptance rule for any projection.
    verdict = {
        'started_at': started, 'ended_at': datetime.now(timezone.utc).isoformat(),
        'command': [sys.executable, '-B', *sys.argv], 'http_status': raw.status_code,
        'api_status': response.get('status'), 'actual_sql': response.get('sql'),
        'actual_table': response.get('table'), 'actual_answer': response.get('answer'),
        'reference_sql': checked.sql, 'reference_table': reference.table,
        'reference_units': {'fraction': str(fraction), 'percent_unrounded': str(fraction * 100)},
        'independent_database_query_count': 1, 'database_read_only': True,
        'statement_timeout_ms': settings.statement_timeout_ms,
        'api_post_count': 1, 'http_retries': 0,
        'claim': 'Supplemental explicit DEV observation. Frozen 60-case score unchanged; inspect scopes and output units separately.',
        'human_review_status': 'pending_human_review',
        'raw_response_sha256': sha256(raw.content).hexdigest(),
    }
    save('report.json', verdict)
    print(json.dumps({'api_status': verdict['api_status'], 'actual_table': verdict['actual_table'],
                      'reference_table': reference.table, 'api_post_count': 1}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
