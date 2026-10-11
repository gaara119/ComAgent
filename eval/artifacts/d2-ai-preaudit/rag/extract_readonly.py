"""Read-only RAG dev evidence extraction; writes only d2-ai-preaudit artifacts."""
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from html.parser import HTMLParser
import pdfplumber
from docx import Document

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'eval/artifacts/d2-ai-preaudit/rag'
OUT.mkdir(parents=True, exist_ok=True)

def read_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def write_json(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def norm(s):
    return re.sub(r'\s+', ' ', s or '').strip()

unified = read_json('eval/reports/d2-acceptance/unified-review.json')
rows = [r for r in unified['rows'] if r.get('group') == 'rag' and r.get('split') == 'dev']
ids = {r['id'] for r in rows}
dataset = {}
for n, line in enumerate((ROOT/'eval/datasets/rag_single.jsonl').open(encoding='utf-8'), 1):
    value = json.loads(line)
    if value.get('split') == 'dev' and value.get('id') in ids:
        dataset[value['id']] = {'line': n, 'record': value}
responses = {}
for n, line in enumerate((ROOT/'eval/artifacts/d2/rag/final/responses.jsonl').open(encoding='utf-8'), 1):
    value = json.loads(line)
    if value.get('split') == 'dev' and value.get('id') in ids:
        responses[value['id']] = {'line': n, 'record': value}
qa_ids = {r['expected'].get('source_qa_id') for r in rows} - {None}
qa = {v['ID']: v for v in read_json('data/raw/ohr/qas_v2.json') if v['ID'] in qa_ids}
manifest = {v['doc_id']: v for v in csv.DictReader((ROOT/'data/docs/manifest.csv').open(encoding='utf-8-sig'))}
doc_ids = {r['expected']['doc_id'] for r in rows}
pages = {doc_id:set() for doc_id in doc_ids}
for r in rows:
    pages[r['expected']['doc_id']].update(r['expected'].get('physical_pages', []))
    for e in r['actual']['evidences']:
        if e.get('page'):
            pages[e['doc_id']].add(e['page'])
pages['ohr-academic-label-words'].update([5,6,7,12])

source_records = []
page_dir = OUT / 'raw-pages'
page_dir.mkdir(exist_ok=True)
poppler = Path('C:/Users/郭乾冥/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
for doc_id in sorted(doc_ids):
    m = manifest[doc_id]
    source = ROOT / m['path']
    h = hashlib.sha256(source.read_bytes()).hexdigest()
    entry = {'doc_id':doc_id, 'source_path':m['path'], 'sha256':h, 'manifest_sha256':m['content_hash'], 'hash_matches':h==m['content_hash'], 'format':m['format'], 'pages':[]}
    if m['format'] == 'pdf':
        with pdfplumber.open(source) as pdf:
            entry['physical_page_count'] = len(pdf.pages)
            for p in sorted(pages[doc_id]):
                page = pdf.pages[p-1]
                stem = f'{doc_id}-physical-p{p}'
                plain = page.extract_text() or ''
                layout = page.extract_text(layout=True) or ''
                plain_path = page_dir / (stem + '.txt')
                layout_path = page_dir / (stem + '-layout.txt')
                plain_path.write_text(plain+'\n', encoding='utf-8')
                layout_path.write_text(layout+'\n', encoding='utf-8')
                render_path = page_dir / (stem + '.png')
                subprocess.run([str(poppler),'-f',str(p),'-l',str(p),'-singlefile','-r','120','-png',str(source),str(page_dir/stem)], check=True, capture_output=True)
                entry['pages'].append({'physical_page':p,'text_path':plain_path.relative_to(ROOT).as_posix(),'layout_text_path':layout_path.relative_to(ROOT).as_posix(),'render_path':render_path.relative_to(ROOT).as_posix(),'full_page_extracted':True,'rendered':render_path.is_file(),'visual_inspection':'pending'})
    elif m['format'] == 'docx':
        doc = Document(source)
        lines = []
        for node in doc.element.body:
            if node.tag.endswith('}p'):
                from docx.text.paragraph import Paragraph
                p = Paragraph(node, doc)
                lines.append(f'[paragraph; style={p.style.name}] {p.text}')
            elif node.tag.endswith('}tbl'):
                from docx.table import Table
                table = Table(node, doc)
                lines.append('[table]')
                for row in table.rows:
                    lines.append(' | '.join(cell.text for cell in row.cells))
        output = OUT / (doc_id+'-full-docx.txt')
        output.write_text('\n'.join(lines)+'\n', encoding='utf-8')
        entry['full_document_extraction'] = output.relative_to(ROOT).as_posix()
        entry['parser'] = 'python-docx; document order incl tables'
    elif m['format'] in ('html','md'):
        output = OUT / (doc_id+'-full-source.'+m['format'])
        output.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')
        entry['full_document_copy'] = output.relative_to(ROOT).as_posix()
    elif m['format'] == 'png':
        from PIL import Image
        with Image.open(source) as im:
            entry['image_dimensions'] = list(im.size)
        entry['visual_inspection'] = 'pending'
    source_records.append(entry)
write_json('source-verification.json',source_records)

chunks = []
for n, line in enumerate((ROOT/'data/indexes/docs-final/chunks.jsonl').open(encoding='utf-8'),1):
    c = json.loads(line)
    if c['doc_id'] in doc_ids and (not c.get('page') or c['page'] in pages[c['doc_id']]):
        chunks.append({'line':n,'record':c})
qa_audit=[]
cit_audit=[]
compact=[]
for r in rows:
    d = dataset[r['id']]['record']
    a = responses[r['id']]['record']['response']
    q = qa.get(d.get('source_qa_id'))
    orig = {'review_id':r['review_id'],'id':r['id'],'group':'rag','split':'dev','dataset_line':dataset[r['id']]['line'],'source_qa_id':d.get('source_qa_id'),'source_question_type':'OHR原题' if q else '自编','qa_source_path':'data/raw/ohr/qas_v2.json' if q else None,'original_qa':q,'question_exact': q['questions']==d['question'] if q else None,'answer_exact':q['answers']==d['answer'] if q else None,'doc_entry_exact':q['doc_name']+'.pdf'==manifest[d['doc_id']]['source_entry'] if q else None,'page_zero_to_physical_one_based_exact':[q['evidence_page_no']+1]==d['physical_pages'] if q else None,'reference_note':'引用排版/OCR归一化后另按原页语义核验；不假定引用原字符串必须完全一致。'}
    qa_audit.append(orig)
    citations=[]
    for e in a.get('evidences',[]):
        matching=[v for v in chunks if v['record']['doc_id']==e['doc_id'] and v['record']['page']==e.get('page') and v['record']['text']==e['text'] and v['record']['section_path']==e.get('section_path',[])]
        citations.append({'evidence_id':e['evidence_id'],'doc_id':e['doc_id'],'physical_page':e.get('page'),'section_path':e.get('section_path',[]),'actual_text':e['text'],'exact_index_matches':[{'line':v['line'],'chunk_id':v['record']['chunk_id'],'content_hash':v['record']['content_hash'],'parser':v['record']['parser']} for v in matching],'index_exact_match':bool(matching),'source_hash_matches': next(v['hash_matches'] for v in source_records if v['doc_id']==e['doc_id']),'semantic_support_requires_raw_review':True})
    cit_audit.append({'review_id':r['review_id'],'id':r['id'],'group':'rag','split':'dev','response_line':responses[r['id']]['line'],'unified_answer_equals_response':r['actual']['answer']==a['answer'],'unified_status_equals_response':r['actual']['status']==a['status'],'unified_evidence_equals_response': [{k:v for k,v in e.items() if k in ['evidence_id','doc_id','doc_title','page','section_path','text','bbox']} for e in r['actual']['evidences']]==a.get('evidences',[]),'cited_ids_in_answer':re.findall(r'\[(E\d+)\]', a['answer']),'citations':citations})
    compact.append({'review_id':r['review_id'],'id':r['id'],'group':'rag','split':'dev','question':d['question'],'answer':d['answer'],'reference_text':d['reference_text'],'doc_id':d['doc_id'],'physical_pages':d['physical_pages'],'source_qa_id':d.get('source_qa_id'),'actual':{k:a.get(k) for k in ['status','answer','evidences']}})
write_json('original-qa-dev-audit.json',qa_audit)
write_json('citation-index-dev-audit.json',cit_audit)
write_json('dev-compact-inputs.json',compact)
write_json('scope.json',{'reviewed_group':'rag','reviewed_split':'dev','dev_count':len(rows),'reserved_count_skipped':sum(r.get('group')=='rag' and r.get('split')!='dev' for r in unified['rows']),'reserved_policy':'Only counts; no reserved question/answer expanded or copied.','qa_matches':len(qa),'source_documents':len(source_records),'source_pages':sum(len(v['pages']) for v in source_records),'api_calls':0,'model_calls':0})
print(json.dumps({'dev_rows':len(rows),'source_documents':len(source_records),'rendered_pdf_pages':sum(len(v['pages']) for v in source_records),'original_qa_matches':len(qa),'exact_citation_index_matches':sum(c['index_exact_match'] for v in cit_audit for c in v['citations']),'citation_count':sum(len(v['citations']) for v in cit_audit)},ensure_ascii=False))
