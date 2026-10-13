"""Regroup only the frozen human-review presentation, retaining draft hashes."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from build_oct12_review import ROOT, OUT, TITLE, build_html, digest, grouped_review_rows


def main():
    source = OUT / (TITLE + '.json')
    raw = source.read_bytes()
    report = json.loads(raw)
    groups = grouped_review_rows(report)
    folder = ROOT / 'eval/artifacts/oct13/manual-review-grouping'
    if folder.exists():
        raise ValueError('Preserve existing grouping evidence; choose a new version.')
    folder.mkdir(parents=True)
    for suffix in ('.html', '.md'):
        current = OUT / (TITLE + suffix)
        (folder / ('before' + suffix)).write_bytes(current.read_bytes())
    categories = []
    markdown = ['# 全部待人工审核统一入口', '',
        '打开同目录HTML，按问题类型逐类审核。735项同类连续排列；原编号、审核内容、证据与浏览器草稿键保留。', '',
        '保存和导出只生成草稿，不自动应用审核决定。导出始终包含全部735项。', '',
        '|问题类型|数量|', '|---|---:|']
    for key, label, description, subgroups in groups:
        count = sum(len(rows) for rows in subgroups.values())
        markdown.append(f'|{label}|{count}|')
        categories.append({'key': key, 'label': label, 'count': count,
            'subgroups': [{'label': name, 'count': len(rows),
                'review_keys': [row['review_key'] for _, row in rows]}
                for name, rows in subgroups.items()]})
    for key, label, description, subgroups in groups:
        markdown += ['', '## ' + label, '', description]
        for name, rows in subgroups.items():
            markdown += ['', '### ' + name, '', '|原序号|审核键|原编号|题面/对象|', '|---:|---|---|---|']
            for number, row in rows:
                markdown.append('|'+str(number)+'|'+row['review_key']+'|'+', '.join(row['original_ids'])+'|'+row['title'].replace('|','\\|').replace('\n',' ')+'|')
    build_html(report)
    (OUT / (TITLE + '.md')).write_text('\n'.join(markdown)+'\n', encoding='utf-8')
    if source.read_bytes() != raw:
        raise ValueError('Frozen review data changed')
    record = {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'scope': 'Presentation-only grouping; no model/database calls or human decisions',
        'source_json': source.relative_to(ROOT).as_posix(), 'source_json_sha256': sha256(raw).hexdigest(),
        'dataset_sha256': digest(report['rows']), 'pending_rows': len(report['rows']),
        'categories': categories, 'original_json_unchanged': True,
        'row_hashes': {row['review_key']:row['content_sha256'] for row in report['rows']},
        'old_draft_storage_key_preserved': 'oct12-review-draft-v1',
        'human_records_changed': 0, 'model_calls': 0, 'database_calls': 0}
    (folder / 'grouping.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'categories':{c['label']:c['count'] for c in categories},'rows':len(report['rows']),'source_json_unchanged':True},ensure_ascii=False))


if __name__ == '__main__':
    main()
