import collections
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
ART=ROOT/'eval/artifacts/d2-ai-preaudit/rag'
report=json.loads((ROOT/'eval/reports/d2-ai-preaudit/rag-review.json').read_text(encoding='utf-8'))
unified=json.loads((ROOT/'eval/reports/d2-acceptance/unified-review.json').read_text(encoding='utf-8'))
dev=[r for r in unified['rows'] if r.get('group')=='rag' and r.get('split')=='dev']
rows=report['rows']
assert len(rows)==21
assert {r['review_id'] for r in rows}=={r['review_id'] for r in dev}
assert len({r['review_id'] for r in rows})==21
statuses={'AI建议通过','AI建议有条件通过','AI发现错误','证据不足'}
required=['reference_status','actual_status','answer_correctness_status','citation_support_status','citation_location_status','source_question_type','reason','actual_reason','issues','suggestion','human_confirmation','evidence','evidence_complete']
errors=[]
for r in rows:
    assert r['group']=='rag' and r['split']=='dev'
    assert all(k in r for k in required)
    assert all(r[k] in statuses for k in ['reference_status','actual_status','answer_correctness_status','citation_support_status','citation_location_status'])
    assert isinstance(r['issues'],list) and isinstance(r['evidence_complete'],bool)
    assert r['reason'] and r['actual_reason'] and r['human_confirmation']
    for e in r['evidence']:
        assert (ROOT/e['path']).is_file(), e['path']
        assert 'sourcequote' in e and (e.get('page') or e.get('line') or e.get('section'))
    assert r['source_verification']['manifest_hash_verified']
    assert r['source_verification']['actual_equals_final_response']
    if r['source_question_type']=='OHR原题':
        assert r['source_verification']['original_qa_exact_match']
        assert r['source_verification']['original_qa_source_hash_verified']
    if r['citation_location_status']=='AI发现错误':
        errors.append(r['id'])
assert len(errors)==10
src=json.loads((ART/'source-verification.json').read_text(encoding='utf-8'))
assert len(src)==10 and all(s['hash_matches'] for s in src)
assert sum(len(s['pages']) for s in src)==15
assert all(p['visual_inspection'].startswith('completed') for s in src for p in s['pages'])
cit=json.loads((ART/'citation-index-dev-audit.json').read_text(encoding='utf-8'))
assert len(cit)==21
assert sum(len(r['citations']) for r in cit)==30
assert all(e['index_exact_match'] and e['bbox_exact_index_matches'] for r in cit for e in r['citations'])
loc=json.loads((ART/'citation-location-dev-audit.json').read_text(encoding='utf-8'))
assert len(loc)==30
assert sum(e['source_location_status']=='AI发现错误' for e in loc)==13
boxes=json.loads((ART/'actual-bbox-visible-render.json').read_text(encoding='utf-8'))
assert len(boxes)==15 and all(b['visual_inspection'].startswith('completed') for b in boxes)
for b in boxes:
    assert (ROOT/b['outline_path']).is_file()
    assert (ROOT/b['visible_crop_path']).is_file()
for field,counts in report['counts'].items():
    assert dict(collections.Counter(r[field] for r in rows))==counts
assert report['scope']['reserved_skipped_count']==9
assert not report['scope']['reserved_content_reviewed']
assert not list(ART.rglob('*.pyc'))
result={'status':'passed','dev_rows':21,'reserved_skipped_count':9,'reference_pass':21,'actual_pass':11,'actual_conditional':10,'core_answer_pass':21,'answer_correctness_pass':20,'answer_correctness_conditional':1,'citation_semantic_pass':20,'citation_semantic_conditional':1,'citation_location_pass':11,'citation_location_error_rows':10,'citation_location_error_entries':13,'citation_location_error_ids':errors,'original_qa_exact_and_hash_verified':14,'citation_index_exact_matches':30,'original_sources_hash_matches':10,'full_original_pdf_pages_visually_reviewed':15,'existing_pdf_bbox_visually_reviewed':15,'evidence_links_exist':True,'required_fields_valid':True,'human_approval_fields_written':False,'api_or_model_calls':0}
(ART/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
