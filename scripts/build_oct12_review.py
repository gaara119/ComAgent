"""Build a new DEV-only review hub; never apply or forge human decisions."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import yaml
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "eval/reports/oct12/manual-review"
TITLE = "全部待人工审核统一入口"
SPECIAL = "eval/experiments/after_d2_01_03"
SOURCES: dict[str, dict] = {}
ROWS: dict[str, dict] = {}
AUTHORIZED: list[dict] = []


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def read(path):
    p = ROOT / path
    content = p.read_bytes()
    SOURCES[path] = {"path": path, "sha256": sha256(content).hexdigest(), "role": "source", "read_policy": "explicit DEV source or split-filtered before use"}
    return json.loads(content.decode('utf-8-sig'))


def track_text_source(path, role):
    content = (ROOT / path).read_bytes()
    SOURCES[path] = {'path':path,'sha256':sha256(content).hexdigest(),'role':role,'read_policy':'schema, document manifest or alias relationships; no held questions'}
    return content.decode('utf-8-sig')


def read_dev(path):
    p = ROOT / path
    if not p.exists():
        return []
    content = p.read_bytes()
    SOURCES[path] = {"path": path, "sha256": sha256(content).hexdigest(), "role": "source", "read_policy": "split=dev only; held content not extracted"}
    result = []
    for number, line in enumerate(content.decode('utf-8-sig').splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("split") != "dev":
            continue
        item = dict(item)
        item["_source_line"] = number
        result.append(item)
    return result


def add(key, identifier, group, title, source, material, **kwargs):
    if key not in ROWS:
        ROWS[key] = {"review_key": key, "original_ids": [identifier], "group": group, "title": title, "human_status": "pending_human_review", "decision_objects": [], "source_materials": [], "system_versions": [], "suggestions": [], "proposed_question": title, "proposed_label": "", "human_decisions": {}, "human_signatures": None, "human_confirmed_at": None}
    row = ROWS[key]
    row["source_materials"].append({"source": source, "original_id": identifier, "material": material})
    row.update(kwargs)
    return row


def object_pending(row, name, reason, ai="未进行新的AI逐项审核"):
    if not any(obj["object"] == name for obj in row["decision_objects"]):
        row["decision_objects"].append({"object": name, "status": "pending_human_review", "AI_judgment": ai, "reason": reason})


def compact_response(record):
    response = record.get("response", record.get("result", record))
    if not isinstance(response, dict):
        return response
    return {key: response.get(key) for key in ["status", "trace_id", "answer", "sql", "table", "evidences", "error", "intent", "rewritten_question", "clarification", "metadata"] if key in response}


def append_actual(key, source, record, version):
    row = ROWS.get(key)
    if row is None:
        return
    response = compact_response(record)
    content = digest(response)
    existing = next((item for item in row["system_versions"] if item["content_sha256"] == content), None)
    ref = {"path": source, "line": record.get("_source_line"), "position": record.get('_source_position'), "id": record.get("id")}
    if existing:
        existing["evidence"].append(ref)
        return
    has_document_citations = key.startswith('rag:') or (isinstance(response, dict) and any(isinstance(e,dict) and e.get('doc_id') for e in response.get('evidences') or []))
    review_dimensions = ['整体回答'] + (['答案正确性','引用语义支持','引用定位'] if has_document_citations else [])
    row["system_versions"].append({"version": version, "actual": response, "content_sha256": content, "evidence": [ref], "review_dimensions":review_dimensions,"human_status": "pending_human_review", "AI_judgment": "以该版本对应审核材料为准；未继承其他版本的人工通过"})
    object_pending(row, "系统实际回答（各版本分别确认或归档）", "参考答案的批准不等于批准新的模型输出，历史输出不因新版本成功而抹去。")


def clean_proposal(row):
    if row['group'] in {'D2别名待定', 'AW中文目录表说明', 'AW中文目录列说明', '公共接口与会话', '声明的对象限定假设', '增长率显示单位', '测试结论范围'}:
        return
    original = row["title"]
    clean = original
    reason = []
    replacements = [
        (r"；如果数据库里根本没有这个流派，请直接报告没有记录。?$", "？", "删去指定系统输出行为的提示；不存在值的期望行为移至标签规范。"),
        (r"；如果数据库没有这个国家，就按这个字面值查，直接报告没有记录。?$", "？", "删去指定执行和回答方式的提示，保留不存在的字面值。"),
        (r"；如果那段时间没有发票，就按这个时间范围查询并报告没有记录。?$", "。", "删去回答行为指令，保留原半开区间。"),
        (r"如果那一年没有发票记录，请直接说没有可用记录，不要用0代替。?$", "", "NULL与空结果规范放在标签，不在题面透露系统应答。"),
        (r"如果没有，请如实输出0。?$", "", "空计数为0留在标签，不在题面要求模型输出。"),
    ]
    for pattern, replacement, explanation in replacements:
        updated = re.sub(pattern, replacement, clean)
        if updated != clean:
            reason.append(explanation)
            clean = updated
    cleaned_identifiers = clean.replace("customer.country='Atlantis'", "国家为 Atlantis").replace("genre 为 Vaporwave", "Vaporwave 流派").replace("仅 first_name，不包含姓氏 last_name", "不包含姓氏")
    if cleaned_identifiers != clean:
        reason.append("去掉代码字段或SQL过滤表达式，保留业务范围；需人工确认措辞未改变含义。")
        clean = cleaned_identifiers
    if row["original_ids"] == ["sp01-30"]:
        clean = "统计从2030年1月1日（含）到2030年12月31日（不含）的发票张数。"
        reason.append("精确保留原[2030-01-01,2030-12-31)区间，不能擅改为全年或<2031-01-01。旧gold的区间冲突须重新定标签。")
    row["proposed_question"] = clean
    if reason:
        row["suggestions"].extend(reason)
        object_pending(row, "题面清洗提案", "只是草案；不自动改题库。")
    if re.search(r"(?:\w+\.\w+|\b(?:currentflag|enddate|first_name|last_name|NULL|SUM|AVG|COUNT|LIMIT)\b)", clean, re.I):
        row["suggestions"].append("题面仍含字段/SQL术语：核对它属于必要业务定义还是实现提示；单位、排序、区间、返回对象等业务要求应保留，不按关键词一刀切删除。")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    old = read("eval/reports/d2-acceptance/unified-review.json")
    confirmed_metric_material = read('data/rules/metric_definitions.json')
    dev_rows = [r for r in old["rows"] if r.get("split") != "holdout"]
    for r in dev_rows:
        if r["group"] == "metric":
            AUTHORIZED.append({"id": r["id"], "group": "已确认四项业务定义", "source": "data/rules/metric_definitions.json", "scope": r["title"], "status": "already_user_confirmed"})
    with (ROOT / "data/aliases/aliases-d2-reviewed.csv").open(encoding="utf-8-sig", newline="") as stream:
        aliases = list(csv.DictReader(stream))
    track_text_source('data/aliases/aliases-d2-reviewed.csv', 'original alias relationship and review-status evidence')
    alias_views = {source:list(csv.DictReader(track_text_source(source, 'alias state version; relationship-only').splitlines())) for source in ['data/aliases/aliases.csv','data/aliases/aliases-italy-draft.csv','data/aliases/aliases-oct12-approved.csv']}
    def alias_key(item):
        return (item['alias'],item['column'],item['standard_value'])
    alias_latest = {alias_key(item):item for item in alias_views['data/aliases/aliases-oct12-approved.csv']}
    alias_reviewed_keys = {alias_key(item) for item in aliases}
    unknown_legacy_relations = [{'source':source,'alias':item} for source,view in alias_views.items() for item in view if alias_key(item) not in alias_reviewed_keys]
    alias_deduplication = {'canonical_source':'data/aliases/aliases-d2-reviewed.csv','canonical_relationships':len(aliases),'source_view_counts':{source:len(view) for source,view in alias_views.items()},'historical_pending_rows_are_not_new_decisions':'Original draft pending statuses remain untouched; same relationship uses the later user-attested decision and retains old provenance. Candidate relation approval remains distinct from direct binding authorization.','new_oct12_current_status_counts':dict(Counter(item['review_status'] for item in alias_views['data/aliases/aliases-oct12-approved.csv'])),'legacy_relationships_not_in_reviewed_source':unknown_legacy_relations}
    if unknown_legacy_relations:
        raise ValueError('Additional alias relationships found outside the reviewed81; add them to manual review explicitly before delivery.')
    read("eval/artifacts/d2-final/review/user-attestation-and-revisions.json")
    ai_alias = {r['id']: r for r in read("eval/reports/d2-ai-preaudit/aliases-review.json")['rows']}
    for alias in aliases:
        identifier = alias["alias_id"]
        status = alias["review_status"]
        if status != "pending":
            AUTHORIZED.append({"id": identifier, "group": "别名关系", "scope": alias, "status": status, "current_alias_state":alias_latest.get(alias_key(alias)),"current_alias_source":"data/aliases/aliases-oct12-approved.csv","historical_duplicate_sources":[source for source,view in alias_views.items() if any(alias_key(item)==alias_key(alias) for item in view)],"effective_authorization": "10月12日明确批准直接USA，不再因该别名触发L1" if alias['alias'] == '老美' and alias['standard_value'] == 'USA' else status, "source": "data/aliases/aliases-d2-reviewed.csv", "note": "该source为历史D2版本；approved_candidate仅批准候选关系，不能强制唯一绑定。新授权改变的范围独立列出。"})
            continue
        row = add("alias:" + identifier, identifier, "D2别名待定", alias["alias"] + " → " + alias["standard_value"] + "（" + alias["column"] + "）", "data/aliases/aliases-d2-reviewed.csv", {"alias": alias, "AI_precheck": ai_alias[identifier]})
        object_pending(row, "别名关系", "仍无足够证据，运行中继续停用；核对是否保留候选/拒绝。", "证据不足")
        row['source_materials'].append({'source':'data/aliases/aliases-oct12-approved.csv','original_id':identifier,'material':alias_latest.get(alias_key(alias))})
    approved = {}
    for source in ["eval/artifacts/d2-final/review/sql-dev-v1.jsonl", "eval/artifacts/d2-final/review/robust-dev-v1.jsonl"]:
        for item in read_dev(source):
            key = ("robust:" if item["id"].startswith("robust-") else "sql:") + item["id"]
            if item["gold_review"]["status"] == "accepted":
                approved[item["id"]] = item
                AUTHORIZED.append({"id": item["id"], "group": "D2参考答案", "status": "user_attested_original_AI_pass", "source": source, "content_sha256": item["gold_review"].get("content_sha256")})
                continue
            row = add(key, item["id"], "D2新gold待定", item["question"], source, item)
            object_pending(row, "新参考答案", "当前修订版未获最终人工确认；具体NULL/范围提案另见gold-38-23-proposal.md。", "AI建议有条件通过")
            row["evidence_files"] = ["notes/oct12/gold-38-23-proposal.md", "eval/artifacts/oct12/review-gold/readonly-rerun/readonly-verification.json"]
    # A later accepted version does not silently sign off older ambiguous wording.
    sql_reference_compare_keys = ['question','gold_sql','gold_columns','gold_result','ordered','monetary_columns','db_id']
    sql_reference_deduplication = {'comparison_keys':sql_reference_compare_keys,'identical_authorized_sources':[],'distinct_pending_sources':[],'old_pending_states_unchanged':True}
    for source in ["eval/datasets/nl2sql_chinook.jsonl", "eval/datasets/nl2sql_chinook_d1_acceptance.jsonl"]:
        for item in read_dev(source):
            same_as_approved = item['id'] in approved and all(item.get(k)==approved[item['id']].get(k) for k in sql_reference_compare_keys)
            group = '历史/本轮系统回答（参考已确认）' if same_as_approved else 'D1历史待核与归档'
            row = add("sql:" + item["id"], item["id"], group, item["question"], source, item)
            canonical = {name:item.get(name) for name in ['question','gold_sql','gold_columns','gold_result','ordered','monetary_columns','category','db_id']}
            variant_hash = digest(canonical)
            variants = row.setdefault('historical_reference_versions', [])
            variant = next((v for v in variants if v['content_sha256'] == variant_hash), None)
            if variant:
                variant['evidence_files'].append(source)
            else:
                variants.append({'content_sha256':variant_hash,'reference':canonical,'evidence_files':[source],'human_status':'already_user_confirmed_same_content' if same_as_approved else 'pending_human_review','original_status_unchanged':True})
            if same_as_approved:
                sql_reference_deduplication['identical_authorized_sources'].append({'id':item['id'],'source':source})
                authorization = next(a for a in AUTHORIZED if a['id']==item['id'] and a['group']=='D2参考答案')
                authorization.setdefault('same_content_historical_sources', []).append(source)
            else:
                sql_reference_deduplication['distinct_pending_sources'].append({'id':item['id'],'source':source})
                object_pending(row, "历史D1题面/gold版本 " + variant_hash[:10] + " 确认或归档", "此版本与已确认D2题面/SQL/结果不同；同内容合并出处，不同版本保留独立选择，不能继承批准。")
            if item["id"] in approved:
                row["accepted_current_reference"] = {"status": "already_user_confirmed_for_D2_version", "reference": approved[item["id"]], "approval_not_applied_to_old_version": True}
    for item in read_dev("eval/reports/d1-acceptance/sql-dev/responses.jsonl"):
        append_actual("sql:" + item['id'], "eval/reports/d1-acceptance/sql-dev/responses.jsonl", item, "D1验收开发回答")
    rag_ai = {r['id']: r for r in read("eval/artifacts/d2-final/rag/second-review-v4.3.json")['rows']}
    with (ROOT / 'data/docs/manifest.csv').open(encoding='utf-8-sig', newline='') as stream:
        documents = {r['doc_id']: r for r in csv.DictReader(stream)}
    track_text_source('data/docs/manifest.csv', 'raw RAG source/document-ID manifest')
    track_text_source('data/catalog/chinook.yaml', 'existing Chinook schema and date-range metadata')
    rag_references = {}
    for item in read_dev("eval/artifacts/d2-final/review/rag-dev-view.jsonl"):
        rag_references[item['id']] = item
        row = add("rag:" + item['id'], item['id'], "RAG新回答与引用", item['question'], "eval/artifacts/d2-final/review/rag-dev-view.jsonl", {"current_reference": item, "D2_final_AI_review": rag_ai.get(item['id'])})
        row["reference_authorization"] = "原开发题来源/gold已有用户接受原AI审计依据；旧gold_review字段未追改。新系统答案/新引用未人审。"
        AUTHORIZED.append({'id':item['id'],'group':'D2 RAG参考与来源','status':'user_attested_original_AI_pass','source':'eval/reports/d2-final/D2原清单九项逐项验收与证据.md','scope':'原gold与来源；不覆盖定位修复后或本轮新模型回答/引用','original_gold_fields_preserved':True})
        document = documents.get(item['doc_id']) or {}
        row['evidence_files'] = [document['path']] if document.get('path') else []
        row['evidence_files'] += [c['evidence_file'] for c in (rag_ai.get(item['id']) or {}).get('citations', []) if c.get('evidence_file')]
        for name in ["完整答案正确性", "引用语义支持", "引用页/章节/区域定位"]:
            object_pending(row, name, "逐版本核对原文与实际引用；章节未知不能当作已证实。", (rag_ai.get(item['id']) or {}).get('answer_verdict' if name == '完整答案正确性' else 'citation_semantic_verdict', '证据不足'))
    historical_rag_dev = read_dev('eval/datasets/rag_ohr.jsonl')
    rag_reference_keys = ['question','doc_id','answer','reference_text','physical_pages','evidence_source','source_qa_id','source_qa_sha256']
    historical_rag_identical = []
    for item in historical_rag_dev:
        current = rag_references.get(item['id'])
        if current is None:
            raise ValueError('Additional historical RAG DEV reference found outside the current21; add independent review before delivery.')
        row = ROWS['rag:' + item['id']]
        row['source_materials'].append({'source':'eval/datasets/rag_ohr.jsonl','original_id':item['id'],'material':{'historical_D1_reference':item,'comparison_to_user_attested_D2_reference':{key:item.get(key)==current.get(key) for key in rag_reference_keys},'original_pending_status_unchanged':True}})
        if all(item.get(key)==current.get(key) for key in rag_reference_keys):
            historical_rag_identical.append(item['id'])
            row['suggestions'].append('历史D1 RAG参考与已确认D2版本的题意、gold、原文、页码及来源完全相同，合并出处而不重复要求批准；旧文件needs_human_review字段不追改。旧/新模型回答及引用仍逐版本待核。')
        else:
            object_pending(row, '历史D1 RAG参考版本确认或归档', '源/gold/定位与当前已确认版本不同，不能继承批准。')
    rag_reference_deduplication = {'historical_D1_DEV':len(historical_rag_dev),'identical_to_user_attested_D2_reference':len(historical_rag_identical),'identical_DEV_ids':historical_rag_identical,'reference_comparison_keys':rag_reference_keys,'old_pending_states_unchanged':True,'source':'eval/datasets/rag_ohr.jsonl'}
    # Every generated human_review.md is tracked. Identical response content is stored once with all source locations.
    review_tables = [p for p in (ROOT / "eval").rglob("human_review.md") if "protected_holdout" not in p.parts and "version-changes" not in p.parts]
    for review_path in review_tables:
        relative = review_path.relative_to(ROOT).as_posix()
        SOURCES[relative] = {"path": relative, "sha256": sha256(review_path.read_bytes()).hexdigest(), "role": "historical RAG manual-review variant", "read_policy": "metadata only; DEV responses linked below"}
        response_path = review_path.with_name("responses.jsonl")
        if response_path.is_file():
            response_relative = response_path.relative_to(ROOT).as_posix()
            for record in read_dev(response_relative):
                append_actual("rag:" + record['id'], response_relative, record, review_path.parent.relative_to(ROOT).as_posix())
    final_rag = SPECIAL + "/regression/final/V1-001/rag/responses.jsonl"
    for record in read_dev(final_rag):
        append_actual("rag:" + record['id'], final_rag, record, "专项结束最终V1回归")
    aw = read("eval/reports/d3-acceptance/A待人工核对表.json")
    for item in aw['rows']:
        row = add("d3:" + item['id'], item['id'], item['group'], item.get('question', item.get('target', item['id'])), "eval/reports/d3-acceptance/A待人工核对表.json", item)
        object_pending(row, "目录说明" if item['id'].startswith('AW-CAT-') else "参考答案", item['human_action'], item['ai_judgment'])
        if item.get('system_evidence'):
            object_pending(row, "系统实际回答", "aw-07的产品编号含义优先；EX相同不是业务语义证明。")
            row['evidence_files'] = [item['gold_evidence'], item['system_evidence'].split('#')[0]]
    # The earlier D3 table intentionally listed only 25 priority descriptions.
    # The user now asks for EVERY pending table, including AI-pass descriptions.
    catalog_path = ROOT / 'data/catalog/adventureworks.yaml'
    catalog = yaml.safe_load(catalog_path.read_text(encoding='utf-8'))
    SOURCES['data/catalog/adventureworks.yaml'] = {'path':'data/catalog/adventureworks.yaml','sha256':sha256(catalog_path.read_bytes()).hexdigest(),'role':'AW descriptions awaiting human review','read_policy':'schema only; no held questions'}
    catalog_ai = read('eval/reports/d3-ai-review/catalog-pass2.json')
    catalog_ai_by_table = {r['table']:r for r in catalog_ai['reviews']}
    for table in catalog['tables']:
        table_name = table['schema'] + '.' + table['name']
        ai = catalog_ai_by_table[table_name]
        identifier = 'AW-CAT-T-' + table_name
        row = add('d3:' + identifier, identifier, 'AW中文目录表说明', table_name, 'data/catalog/adventureworks.yaml', {'schema_table':table,'AI_pass2':ai,'catalog_human_status':catalog.get('description_review_status'),'note':'AI通过说明也仍待人工确认；旧D3优先索引只列条件项，不代表其余已人审。'})
        object_pending(row, '目录说明', '核对用途、粒度、单位和真实结构；不把AI建议通过当人工签名。', ai['verdict'])
        row['evidence_files'] = ['data/catalog/adventureworks.yaml','eval/reports/d3-ai-review/catalog-pass2.json']
        ai_columns = {c['column']:c for c in ai['columns']}
        for column in table['columns']:
            identifier = 'AW-CAT-C-' + table_name + '.' + column['name']
            row = add('d3:' + identifier, identifier, 'AW中文目录列说明', table_name + '.' + column['name'], 'data/catalog/adventureworks.yaml', {'table':table_name,'column':column,'primary_key':table.get('primary_key'),'foreign_keys':table.get('foreign_keys'),'description_limits':table.get('description_limits'),'AI_pass2':ai_columns[column['name']],'catalog_human_status':catalog.get('description_review_status')})
            object_pending(row, '目录说明', '核对类型/可空性/单位/枚举证据；未有字典的枚举不要补造。', ai_columns[column['name']]['verdict'])
            row['evidence_files'] = ['data/catalog/adventureworks.yaml','eval/reports/d3-ai-review/catalog-pass2.json']
    for source in ['eval/reports/d3-aw-live-dev-run1/responses.jsonl', 'eval/reports/d3-aw-live-dev-run2/responses.jsonl']:
        for record in read_dev(source):
            append_actual('d3:' + record['id'], source, record, Path(source).parent.name)
    clarify = read("notes/d3/clarify-human-review.json")
    for item in clarify['rows'] + clarify['manual_items']:
        row = add("d3:" + item['id'], item['id'], item['group'], item.get('question', item.get('requirement', item['id'])), "notes/d3/clarify-human-review.json", item)
        object_pending(row, "参考语义/协议", item.get('still_needs_human', item.get('reason')), item.get('ai_reference_judgment', item.get('ai_judgment')))
        if item['id'].startswith('clarify-'):
            object_pending(row, "系统完整回答与多轮行为", item['actual_answer_business_judgment'])
        row['evidence_files'] = [e['path'] if isinstance(e, dict) else e for e in item.get('evidence', [])]
        if item['id'].startswith('clarify-'):
            source = 'eval/artifacts/d3/b/clarify-dev-v4/' + item['id'] + '.json'
            if (ROOT / source).is_file():
                append_actual('d3:' + item['id'], source, read(source), 'D3澄清初次实际回答v4')
    special = read(SPECIAL + "/reports/manual-review/①③专项统一待人工审核表.json")
    special_dev_ids = {case['id'] for case in read_dev(SPECIAL + '/data/cases-v6-reviewed.jsonl')}
    if special_dev_ids != {case['id'] for case in special['cases']}:
        raise ValueError('Special review IDs must match the independently DEV-filtered case source.')
    for item in special['cases']:
        row = add("special:" + item['id'], item['id'], item['group'], item['input'], SPECIAL + "/reports/manual-review/①③专项统一待人工审核表.json", item)
        row['proposed_label'] = item['category']
        object_pending(row, "参考答案与标签", "包含原11个标签待定和后续参考争议；不以自动成绩代替人工批准。", (item.get('selected_final_review') or {}).get('reference_verdict', '证据不足'))
        object_pending(row, "系统实际回答与控制器", "V0/V1/V2的回答、引用及控制器分别保留在源材料；本轮不改旧49题分母。", (item.get('selected_final_review') or {}).get('system_verdict', '证据不足'))
        row['evidence_files'] = [SPECIAL + "/data/cases-v6-reviewed.jsonl"]
        # Retain independent choices for every historical HTTP turn as well as
        # the later model calls. The DEV case whitelist above is established
        # before any raw response is opened; no held trace is traversed.
        for observation in item.get('trial_observations', []):
            for turn in observation.get('turns', []):
                raw_source = (turn.get('raw_response_evidence') or {}).get('path')
                if not raw_source or not raw_source.startswith(SPECIAL + '/runtime_eval/runs/'):
                    continue
                if '/cases/' + item['id'] + '/turns/' not in raw_source or not (ROOT / raw_source).is_file():
                    continue
                raw = read(raw_source)
                response = raw.get('body')
                if isinstance(response, str):
                    try:
                        response = json.loads(response)
                    except ValueError:
                        response = None
                if not isinstance(response, dict):
                    # A transport/non-JSON failure is retained as such; no
                    # synthetic successful output is reconstructed.
                    response = {'status': turn.get('actual_status', 'FAILED'), 'error': turn.get('actual_error'), 'metadata': {'actual_http_status': raw.get('http_status'), 'actual_run_state': observation.get('actual_run_state'), 'body_was_valid_json': False}}
                append_actual('special:' + item['id'], raw_source, {'id':item['id'], '_source_position':'body (JSON string parsed)', 'response':response}, '专项历史 ' + str(observation.get('version')) + ' / turn' + str(turn.get('index')))
                row['evidence_files'].append(raw_source)
    new_join = "eval/datasets/oct12/chinook_join_dev_v1.jsonl"
    for item in read_dev(new_join):
        row = add("oct12-join:" + item['id'], item['id'], "10月12日JOIN新增回归", item['question'], new_join, item)
        object_pending(row, "新增参考答案", "标准SQL已只读执行仍需人工核对题意/对象/排序/NULL；这是新DEV集。")
        row['evidence_files'] = ["eval/artifacts/oct12/join-gold/" + item['id'] + '.json']
    # Refreshable final-stage hook: only explicit DEV predictions from this stage,
    # and only IDs already present in known developer label views are imported.
    known_references = {}
    for source in ['eval/artifacts/d2-final/review/sql-dev-v1.jsonl', 'eval/artifacts/d2-final/review/robust-dev-v1.jsonl', new_join]:
        for item in read_dev(source):
            known_references[item['id']] = (source, item)
    for actual_path in sorted((ROOT / 'eval/artifacts/oct12').rglob('responses.jsonl')):
        source = actual_path.relative_to(ROOT).as_posix()
        for record in read_dev(source):
            identifier = record.get('id', '')
            if identifier.startswith('sql-'):
                key = 'sql:' + identifier
            elif identifier.startswith('robust-'):
                key = 'robust:' + identifier
            elif identifier.startswith('rag-'):
                key = 'rag:' + identifier
            elif identifier.startswith('oct12-join-'):
                key = 'oct12-join:' + identifier
            elif identifier.startswith(('sp01-', 'sp03-')):
                key = 'special:' + identifier
            elif identifier.startswith(('aw-', 'clarify-')):
                key = 'd3:' + identifier
            else:
                continue
            if key not in ROWS and identifier in known_references:
                ref_source, reference = known_references[identifier]
                row = add(key, identifier, '10月12日新系统回答', reference['question'], ref_source, reference)
                row['reference_authorization'] = '已有参考答案授权范围按本条gold_review原记录；本轮新实际回答仍待人工核对。'
            append_actual(key, source, record, '10月12日：' + actual_path.parent.relative_to(ROOT / 'eval/artifacts/oct12').as_posix())
    for target_path in sorted((ROOT / 'eval/artifacts/oct12').glob('targets-live-*/*.json')):
        if target_path.name == 'report.json':
            continue
        source = target_path.relative_to(ROOT).as_posix()
        record = read(source)
        if record.get('split') != 'dev' or not record.get('id') or not isinstance(record.get('turns'), list):
            continue
        identifier = record['id']
        key = ('special:' + identifier) if identifier.startswith(('sp01-', 'sp03-')) else ('oct12-diagnostic:' + identifier)
        if key not in ROWS:
            row = add(key, identifier, '10月12日默认口径诊断', record['question'], source, {key:value for key,value in record.items() if key != 'turns'})
            object_pending(row, '诊断参考与实际结果', '诊断请求不是新增正式评分题；只核对新授权口径实现与输出，不加入旧题集分母。')
        for turn, response in enumerate(record['turns']):
            wrapped = {'id': identifier, '_source_position': f'turns[{turn}]', 'response': response.get('response', {})}
            append_actual(key, source, wrapped, target_path.parent.name + f' / turn{turn+1}')
        ROWS[key]['source_materials'].append({'source':source,'original_id':identifier,'material':{'gold_sql':record.get('gold_sql'),'readonly_gold':record.get('readonly_gold'),'automatic_comparison':record.get('comparison'),'context':'本轮诊断原始标准/实跑比较，未借此修改原标签'}})
    repair_files = list((ROOT / 'eval/artifacts/oct12').glob('repairs-live-*/*.json')) + list((ROOT / 'eval/artifacts/oct12').glob('sql22-live-*/*.json'))
    for repair_path in sorted(repair_files):
        if repair_path.name == 'report.json':
            continue
        source = repair_path.relative_to(ROOT).as_posix()
        record = read(source)
        if record.get('split') != 'dev' or not isinstance(record.get('request'), dict) or not isinstance(record.get('response'), dict):
            continue
        identifier = record.get('id', '')
        if identifier.startswith('sql-'):
            key = 'sql:' + identifier
        elif identifier.startswith('robust-'):
            key = 'robust:' + identifier
        elif identifier.startswith(('sp01-', 'sp03-')):
            key = 'special:' + identifier
        else:
            key = 'oct12-diagnostic:' + identifier
        if key not in ROWS:
            row = add(key, identifier, '10月12日默认口径诊断', record.get('question', record['request'].get('message', identifier)), source, {'request':record['request'], 'gold_sql':record.get('gold_sql'),'readonly_gold':record.get('readonly_gold'),'comparison':record.get('comparison'),'scope':'Explicit DEV repair probe, not a new formal scoring question'})
            object_pending(row, '诊断参考与实际结果', '修复后的真实DEV调用独立留存，旧失败不抹去，不增加正式题集分母。')
        else:
            ROWS[key]['source_materials'].append({'source':source,'original_id':identifier,'material':{'request':record['request'],'gold_sql':record.get('gold_sql'),'readonly_gold':record.get('readonly_gold'),'automatic_comparison':record.get('comparison'),'legacy_comparison':record.get('legacy_comparison'),'literal_strict_before_intent':record.get('literal_strict_before_intent'),'context':'修复后实际原始比较；新的成功不改旧日志或旧gold'}})
        append_actual(key, source, {'id':identifier,'_source_position':'response','response':record['response']}, repair_path.parent.name + '/' + repair_path.stem)
    # Browser examples are separate real calls; map identical scoped questions to
    # an existing developer object, otherwise retain as a non-scoring diagnosis.
    scoped_questions = defaultdict(list)
    for key, row in ROWS.items():
        scoped_questions[re.sub(r'\s+', '', row['title']).casefold()].append(key)
    for actual_path in sorted((ROOT / 'eval/artifacts/oct12/ui-live').glob('run-*/*-raw.json')):
        source = actual_path.relative_to(ROOT).as_posix()
        record = read(source)
        if not isinstance(record.get('request'), dict) or not isinstance(record.get('response'), dict):
            continue
        question = record['request'].get('message', '')
        candidates = scoped_questions.get(re.sub(r'\s+', '', question).casefold(), [])
        key = candidates[0] if len(candidates) == 1 else 'oct12-ui:' + actual_path.stem.removesuffix('-raw')
        if key not in ROWS:
            row = add(key, key, '10月12日页面真实问答', question, source, {'request':record['request'],'response':compact_response(record),'source_kind':'actual_browser_example_not_scored_dataset'})
            object_pending(row, '页面实际回答/来源/口径', '实际页面请求不加入旧测试集分母；按当前请求范围和真实引用核对。')
        wrapped = {'id':key,'_source_position':'response','response':record['response']}
        append_actual(key, source, wrapped, actual_path.parent.name + '/' + actual_path.stem)
    for row in ROWS.values():
        clean_proposal(row)
    label_proposals = {
        'sp03-07': ('L0（其他条件明确时）', '年份、账单国分子已经明确；10月12日授权销售额占比分母为同期全部发票金额，不能再以缺分母触发L2。'),
        'sp03-22': ('L0（其他条件明确时）', '法国居住客户为显式分子范围，优先于账单国家默认；分母适用新授权同期全部发票金额。'),
        'sp03-24': ('L0', '明确年份、国家、发票销售额；新授权按账单国家默认，不再问地区口径。'),
        'sp03-08': ('重新定级，去掉缺排名对象理由', '新授权谁买得最多默认客户消费金额；仍需核对TopN与完整排名合同，不能直接批准旧控制器。'),
        'sp03-23': ('重新定级，去掉缺排名对象理由', '与sp03-08题面相同，但本题还有完成后改看2024年测试；保留这个多轮差异或将其作为同题子场景。'),
        'sp03-29': ('L0（其他条件明确时）', '热门曲目默认购买数量、未给期间默认全部数据；不能继续仅为缺期间标L2。'),
        'sp03-30': ('重新定级，去掉缺对象/缺期间理由', '新授权默认客户/金额/全数据，但TopN、并列与历史隐藏2023目标不能无证据继承。'),
        'sp01-06': ('题意/对象不一致，建议替换或移出可评分集', 'Deguo是德国拼音，题面却问专辑；不能把国家擅自当艺术家。若改为德国客户数是新题，必须重新定gold。'),
        'sp01-30': ('保留明确半开区间的不存在数据题', '原题截止2030-12-31不含，而旧gold使用<2031-01-01。当前结果同为0无法掩盖期间差异，需重定gold。'),
    }
    for identifier, (label, reason) in label_proposals.items():
        row = ROWS['special:' + identifier]
        row['proposed_label'] = label
        row['suggestions'].append(reason)
        object_pending(row, '标签修订提案', '根据新授权重新评定，但没有改写冻结标签或分母。')
    for identifier, (label, reason) in {
        'clarify-19': ('L0（其他条件明确时）', '新授权分母为同期全部发票金额，账单Brazil分子已明确，不能再仅因缺分母要求L2。'),
        'clarify-22': ('重新定级，去掉缺排名对象理由', '谁买得最多默认客户消费金额；核对TopN等剩余条件。'),
        'clarify-26': ('L0（其他条件明确时）', '复购已有定义>=2张发票；新授权未说期间默认全部数据。'),
    }.items():
        row = ROWS['d3:' + identifier]
        row['proposed_label'] = label
        row['suggestions'].append(reason)
        object_pending(row, '标签修订提案', '旧标签属于原规则版本；本提案不回填旧评测分数。')
    ROWS['d3:d3-b-growth-display']['proposed_label'] = '前端百分比已于10月12日授权；待核历史raw单位/显示一致性与精度'
    ROWS['d3:d3-b-growth-display']['suggestions'].append('12号任务已明确要求前端比例和增长率显示成百分比，不重复让你决定fraction或percent；本页保留旧审核需求原文，待核对象限为各实际版本的单位标记、乘100显示及舍入是否一致。该显示授权不改变SQL原值或旧gold。')
    ROWS['d3:d3-b-defaults']['suggestions'].append('10月12日已授权热门曲目/复购/客户排名缺期间用全部数据并保留已确认上轮年份；旧“缺期间不得猜”条款需按此授权更新待审标签，不再重复审批这条默认。Top1/默认Top10的适用边界仍待决定。')
    for identifier in ['sql-22', 'sql-24']:
        row = ROWS['sql:' + identifier]
        row['proposed_question'] = approved[identifier]['question'].replace('仅 first_name，不包含姓氏 last_name', '不包含姓氏')
        row['suggestions'].append('旧题“名字”范围不明；已有确认D2版本仅名不含姓。草案保留业务消歧，去掉字段实现提示；若批准为归档只覆盖你选定的历史版本。')
    sql22_diagnosis = 'notes/oct12/sql22-final-readonly-diagnosis.md'
    if (ROOT / sql22_diagnosis).is_file():
        ROWS['sql:sql-22'].setdefault('evidence_files', []).append(sql22_diagnosis)
        ROWS['sql:sql-22']['suggestions'].append('本轮曾将带空格的“严格早于2004年”误解析为月份窗口；原参考SQL/仅名口径仍正确。旧轮次最终SQL碰巧符合原题不能证明Intent期间正确。请把本轮错误和后续修复后的真实版本分别判断，不能改gold适配错误。')
        object_pending(ROWS['sql:sql-22'], '严格早于年份的Intent/SQL/结果一致性', '这是日期解析技术错误及修复回归核验；原gold与已确认名字范围不改。', '以sql22-final-readonly-diagnosis及各版本真实输出为准')
    ROWS['sql:sql-38']['suggestions'].append('推荐已知bytes才参加排行；现有NULLS LAST与IS NOT NULL是两个边界选择，待你确认。')
    ROWS['special:sp03-06']['suggestions'].append('本轮真实系统仅返回所问同比值，原gold额外有当前额/基期额。是否把这两列设为可选诊断列，须先确认标准列合同；不能为EX直接删旧gold列。')
    ROWS['special:sp03-06']['evidence_files'].append('notes/oct12/参考答案与计分争议提案.md')
    ROWS['special:sp03-19']['suggestions'].append('最新phase2存在业务范围冲突：题面“买得最多的客户是谁”、gold LIMIT1，而计划未给TopN默认10导致实际10行。第一名45/32.75相同不能把额外9行当描述列宽容；请先定Top1与默认Top10的适用边界。不改gold、不改默认。')
    ROWS['special:sp03-19']['evidence_files'].extend(['notes/oct12/参考答案与计分争议提案.md','notes/oct12/phase2-target-readonly-diagnosis.md'])
    object_pending(ROWS['special:sp03-19'], '最大客户Top1与未给TopN默认10冲突', '这是返回行数/范围冲突，不能靠EX额外描述列政策放过。', 'AI建议有条件通过（口径边界待你决定）')
    for row in ROWS.values():
        if row['review_key'].startswith(('oct12-diagnostic:', 'special:')) and ('占比' in row['title'] or 'ratio' in row['title'].casefold()):
            row['suggestions'].append('比例的fraction与×100百分数分别标单位；数值相差100倍可能只是单位，先核对SQL表达式/显示，再判事实或计分。新UI百分比授权不自动改旧gold。')
    ROWS['robust:robust-23']['proposed_question'] = '库里所有曲目的平均长度是多少毫秒？'
    ROWS['robust:robust-23']['suggestions'].append('明确全集，保留毫秒与逐曲目等权平均；不用未知“这批”范围。')
    proposal = gold_proposals()
    for case in proposal['cases']:
        key = ('sql:' if case['id'].startswith('sql-') else 'robust:') + case['id']
        row = ROWS[key]
        row['source_materials'].append({'source': 'notes/oct12/gold-38-23-proposal.json', 'original_id': case['id'], 'material': case})
        row['proposed_question'] = case['recommended_candidate']['question']
        row['proposed_gold_sql'] = case['recommended_candidate']['gold_sql']
        row['proposed_label'] = 'top / 已知文件大小 / 字节 / 有序' if case['id'] == 'sql-38' else 'colloquial / 全部曲目 / 等权AVG / 毫秒'
    duplicate_groups = []
    groups = defaultdict(list)
    for row in ROWS.values():
        if row['review_key'].startswith('special:'):
            groups[re.sub(r'\s+', '', row['title']).casefold()].append(row['original_ids'][0])
    for identifiers in groups.values():
        if len(identifiers) > 1:
            same_followup = identifiers == ['sp01-02', 'sp01-13']
            duplicate_groups.append({'ids': identifiers, 'decision': '建议保留sp01-02并归档sp01-13重复题；未实际删除' if same_followup else '题面重复但控制器后续不同；建议同题两个子场景，不盲删多轮测试', 'human_status': 'pending_human_review'})
            for identifier in identifiers:
                ROWS['special:' + identifier]['duplicate_group'] = identifiers
                ROWS['special:' + identifier]['suggestions'].append(duplicate_groups[-1]['decision'])
    boundaries = holdout_metadata()
    (OUT / '保留集隔离边界.json').write_text(json.dumps(boundaries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    current_authorizations = {'source': 'C:/Users/郭乾冥/Desktop/12号任务.md', 'scope': '用户明确要求执行；文件内五项为已授权业务决策，不待重复签字', 'decisions': ['销售额/发票默认账单国家、客户类默认客户所在地，显式用户口径优先', '热门曲目/复购/客户排名没说期间默认全部已有数据，沿用已确认上轮期间', '谁买得最多默认客户按发票金额，热门曲目仍按数量', '仅发票金额/销售额占比分母默认同期全部发票金额，客户数量占比不套用', '老美→USA直接绑定；不因已批准别名单独要求L1切换'], 'additional_explicit_implementation_requirements':['前端比例与增长率显示为百分比；不等同于改写SQL原值或旧gold单位', '增加方案EX（忽略列名、允许额外描述列）作为主指标；不允许额外结果行、放宽业务范围或篡改gold'], 'human_signatures_fabricated': False}
    rows = list(ROWS.values())
    for row in rows:
        row['content_sha256'] = digest({key: val for key, val in row.items() if key not in ['human_decisions', 'human_signatures', 'human_confirmed_at']})
    counts_by_kind = {'AW_catalog_tables':sum(r['original_ids'][0].startswith('AW-CAT-T-') for r in rows),'AW_catalog_columns':sum(r['original_ids'][0].startswith('AW-CAT-C-') for r in rows),'Chinook_SQL_cases':sum(r['review_key'].startswith('sql:') for r in rows),'Chinook_robust_cases':sum(r['review_key'].startswith('robust:') for r in rows),'RAG_cases':sum(r['review_key'].startswith('rag:') for r in rows),'AW_dev_cases':sum(r['review_key'].startswith('d3:aw-') for r in rows),'clarify_dev_cases':sum(r['review_key'].startswith('d3:clarify-') for r in rows),'special_dev_cases':sum(r['review_key'].startswith('special:') for r in rows),'new_JOIN_cases':sum(r['review_key'].startswith('oct12-join:') for r in rows),'alias_relationships':sum(r['review_key'].startswith('alias:') for r in rows),'shared_interface_display_scope_objects':4,'Oct12_non_scoring_diagnostic_requests':sum(r['review_key'].startswith(('oct12-diagnostic:','oct12-ui:')) for r in rows)}
    summary = {'pending_rows': len(rows), 'counts_by_object_kind':counts_by_kind,'pending_by_group': dict(Counter(r['group'] for r in rows)), 'pending_review_objects': sum(len(r['decision_objects']) for r in rows), 'actual_output_versions': sum(len(r['system_versions']) for r in rows), 'per_version_decision_slots': sum(len(v['review_dimensions']) for r in rows for v in r['system_versions']), 'already_authorized_records': len(AUTHORIZED), 'exact_question_duplicate_groups': len(duplicate_groups), 'semantic_duplicate_delete_candidates': 1, 'same_question_different_followup_groups': 1, 'preserved_special_ids': 60, 'new_JOIN_dev_questions': len(read_dev(new_join)), 'held_stage_records': boundaries['total_stage_records_excluding_D1_overlap'], 'held_new_predictions': 0, 'source_files': len(SOURCES)}
    summary['alias_relationship_inventory'] = {'canonical_relationships':len(aliases),'pending':sum(a['review_status']=='pending' for a in aliases),'current_directly_authorized':alias_deduplication['new_oct12_current_status_counts'].get('approved',0),'current_candidate_relationships':alias_deduplication['new_oct12_current_status_counts'].get('approved_candidate',0),'original_pending_csv_and_italy_draft_deduplicated':True}
    report = {'title': TITLE, 'created_at_utc': datetime.now(timezone.utc).isoformat(), 'scope': 'All identified existing manual-review tables: D1 historical pending/archive decisions, D2 new gold/disabled aliases/new RAG answers, D3 A/B including ALL 68 table +456 column descriptions (not just25 priority descriptions in original71-row index), special60, Oct12 newJOIN and actual new model outputs. MD/HTML/JSON representations and identical response contents deduplicated; gold/actual/citation/candidate approval kept as separate review objects.', 'summary': summary, 'newly_explicit_authorizations': current_authorizations, 'already_authorized': AUTHORIZED, 'confirmed_metric_material':confirmed_metric_material,'duplicates': duplicate_groups, 'rows': rows, 'source_inventory': list(SOURCES.values()), 'holdout_boundary_report': 'eval/reports/oct12/manual-review/保留集隔离边界.json', 'no_automatic_application': True, 'business_code_changed_by_builder': False, 'manual_signatures_added': False}
    report['alias_deduplication'] = alias_deduplication
    report['rag_reference_deduplication'] = rag_reference_deduplication
    report['sql_reference_deduplication'] = sql_reference_deduplication
    (OUT / (TITLE + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    build_html(report)
    lines = ['# ' + TITLE, '', '打开同目录HTML逐项展开、填写或导出审核决定JSON；页面保存的是草稿，不会自动改题库、别名或人工记录。', '', f"待核{summary['pending_rows']}条，分开{summary['pending_review_objects']}个审核对象；原始题号全部保留。已批准对象另列，不要求你重复批准。", '', '先定sql-38/robust-23；再看专项去重、题面清洗和新口径标签；最后核对D3目录/题意及RAG各版本原文。不同答案版本可以逐个批准、拒绝或归档，不能用新版本成功代签旧版本。', '', '|审核键|原编号|分组|题面/对象|', '|---|---|---|---|']
    for r in rows:
        lines.append('|' + '|'.join(str(v).replace('|', '\\|').replace('\n', ' ') for v in [r['review_key'], ', '.join(r['original_ids']), r['group'], r['title']]) + '|')
    lines += ['', '保留记录D2 33＋D3 18＝51；D1历史15条不另加。内容本轮不审核、不生成预测，独立边界见同目录JSON。', '', '所有完整材料、AI意见、各版本真实回答、源码与原始证据路径在同名JSON和HTML中，脚本只创建新入口，不覆盖旧表。']
    (OUT / (TITLE + '.md')).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    evidence_package(report)
    print(json.dumps(summary, ensure_ascii=False))


def holdout_metadata():
    def metadata_counts(source, keys):
        content = (ROOT / source).read_bytes()
        metadata = json.loads(content.decode('utf-8-sig'))
        SOURCES[source] = {'path':source,'sha256':sha256(content).hexdigest(),'role':'held count manifest only','read_policy':'Only count/prediction metadata selected; no held label file opened'}
        return {key:metadata.get(key) for key in keys}
    aw_counts = metadata_counts('eval/datasets/d3/aw_schema_link_v2_manifest.json', ['dev_count','holdout_count','total_count','holdout_predictions'])
    clarify_counts = metadata_counts('eval/datasets/d3/clarify/manifest.json', ['dev','holdout','total','holdout_predictions'])
    d3_count = aw_counts['holdout_count'] + clarify_counts['holdout']
    if d3_count != 18 or aw_counts['holdout_predictions'] != 0 or clarify_counts['holdout_predictions'] != 0:
        raise ValueError('D3 manifest held counts/prediction metadata changed; do not assert inferred counts.')
    def families(source, category):
        result = set()
        count = 0
        for line in (ROOT / source).read_text(encoding='utf-8-sig').splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get('split') != 'holdout':
                continue
            count += 1
            result.add((category, item.get('family_id', item['id'])))
        return count, result
    d1_count, d1_families = 0, set()
    for source, category in [('eval/datasets/nl2sql_chinook.jsonl', 'chinook-sql'), ('eval/datasets/rag_ohr.jsonl', 'rag')]:
        count, values = families(source, category)
        d1_count += count
        d1_families.update(values)
    d2_count, d2_families = 0, set()
    for source, category in [('eval/datasets/nl2sql_chinook_d2.jsonl', 'chinook-sql'), ('eval/datasets/robust.jsonl', 'chinook-sql'), ('eval/datasets/rag_single.jsonl', 'rag')]:
        count, values = families(source, category)
        d2_count += count
        d2_families.update(values)
    if d1_count != 15 or d2_count != 33 or not d1_families <= d2_families:
        raise ValueError('Held metadata totals/overlap changed; do not assert inferred counts.')
    return {'scope': '开发审核入口不含保留题题干/答案；人工应在独立审核环境进行保留集内容审核。', 'metadata_method': 'Only split/id/family_id and count manifests used; no question, gold, answers extracted into review report', 'D2': {'records': d2_count, 'unique_question_families': len(d2_families), 'model_predictions': 0}, 'D3': {'records': d3_count, 'model_predictions': 0, 'count_basis': '既有D3 manifest计数字段；未打开D3保留标签明细','AW_manifest':aw_counts,'clarify_manifest':clarify_counts,'source_manifests':['eval/datasets/d3/aw_schema_link_v2_manifest.json','eval/datasets/d3/clarify/manifest.json']}, 'D1': {'records': d1_count, 'all_families_in_D2': True, 'note': '历史D1保留记录已包含于D2对应题族，不能把15再加到33+18。'}, 'total_stage_records_excluding_D1_overlap': d2_count + d3_count, 'independent_review_sources': ['eval/datasets/nl2sql_chinook_d2.jsonl（独立环境先筛split=holdout）', 'eval/datasets/robust.jsonl（独立环境先筛split=holdout）', 'eval/datasets/rag_single.jsonl（独立环境先筛split=holdout）', 'eval/datasets/d3/aw_schema_link.holdout.jsonl', 'eval/datasets/d3/clarify/protected_holdout/cases.jsonl'], 'independent_review_entry': '将仅保留标签与原始来源交给独立审核环境；详细审核报告独立保管，不交给后续调参任务。当前开发交付不打包明细。', 'access_incident': '本代理早期rg命令误输出了历史D1混合CSV的部分保留内容；停止后未进行内容审核、未传递题干/答案给开发代理，未据此修改提示词/业务代码/标签。后续仅使用DEV文件或先过滤split=dev。', 'details_disclosed_in_this_report': False, 'new_holdout_predictions': 0}


def gold_proposals():
    sql_rows = read_dev('eval/artifacts/d2-final/review/sql-dev-v1.jsonl')
    robust_rows = read_dev('eval/artifacts/d2-final/review/robust-dev-v1.jsonl')
    readonly = read('eval/artifacts/oct12/review-gold/readonly-rerun/readonly-verification.json')
    by_id = {item['id']: item for item in readonly['records']}
    proposal = {'title': 'sql-38、robust-23 新gold人工决定提案', 'human_review_status': 'pending_human_review', 'human_signatures': None, 'human_confirmed_at': None, 'source_readonly_results': 'eval/artifacts/oct12/review-gold/readonly-rerun/readonly-verification.json', 'new_model_predictions': 0, 'cases': []}
    for identifier, items in [('sql-38', sql_rows), ('robust-23', robust_rows)]:
        current = next(item for item in items if item['id'] == identifier)
        if identifier == 'sql-38':
            candidate = {'question': '找出文件大小已记录的曲目中，字节数最大的前3首，返回曲目编号、名称和字节数；按字节数降序，并列按曲目编号升序。', 'reference_semantics': {'bytes_null_behavior': 'exclude_unknown', 'fewer_than_three': 'return_all_eligible', 'unit': 'bytes', 'ordered': True}, 'gold_sql': by_id['sql-38_recommended']['sql'], 'gold_result': by_id['sql-38_recommended']['result']['table']}
            alternative = {'choice': 'NULLS LAST', 'gold_sql': current['gold_sql'], 'requires_confirmation': '已知不足3条时是否允许用未知大小补齐；若不允许则不等同推荐方案。'}
        else:
            candidate = {'question': '库里所有曲目的平均长度是多少毫秒？', 'reference_semantics': {'scope': 'all_public_track_rows', 'grain': 'one_track_one_equal_weight', 'unit': 'milliseconds', 'null_behavior': 'AVG_ignores_null_and_returns_null_on_no_nonnull_rows', 'ordered': False}, 'gold_sql': by_id['robust-23_recommended']['sql'], 'gold_result': by_id['robust-23_recommended']['result']['table']}
            alternative = {'choice': '保留这批并改为范围澄清题', 'requires_confirmation': '改变保持原意的colloquial类别；必须重建行为/后续标签而非改平均值。'}
        proposal['cases'].append({'id': identifier, 'split': 'dev', 'current_pending_version': current, 'recommended_candidate': candidate, 'alternative': alternative, 'AI_judgment': 'AI建议通过（仅针对明示语义的候选方案）', 'human_decision': None, 'gold_result_verified': True, 'verification_record': identifier + '_recommended'})
    (ROOT / 'notes/oct12/gold-38-23-proposal.json').write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return proposal


def evidence_package(report):
    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.hrefs = []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'a' and attrs.get('href'):
                self.hrefs.append(attrs['href'])
    parsed = Links()
    parsed.feed((OUT / (TITLE + '.html')).read_text(encoding='utf-8'))
    candidates = {entry['path'] for entry in report['source_inventory']}
    candidates.update(['eval/reports/oct12/manual-review/' + TITLE + extension for extension in ['.json','.md','.html']])
    candidates.update(['eval/reports/oct12/manual-review/保留集隔离边界.json','notes/oct12/gold-38-23-proposal.json','notes/oct12/gold-38-23-proposal.md','notes/oct12/参考答案与计分争议提案.md','scripts/build_oct12_review.py','scripts/verify_oct12_gold.py','scripts/check_oct12_review.py','data/catalog/chinook.yaml','data/docs/manifest.csv','data/aliases/aliases-d2-reviewed.csv','data/rules/metric_definitions.json','eval/artifacts/oct12/review-gold/date-facts/readonly-verification.json','eval/artifacts/oct12/review-gold/date-facts/queries.sql'])
    links = []
    for href in parsed.hrefs:
        url = urlparse(href)
        if url.scheme or url.netloc:
            continue
        target = (OUT / unquote(url.path)).resolve()
        if target.is_relative_to(ROOT):
            relative = target.relative_to(ROOT).as_posix()
            candidates.add(relative)
            links.append({'href':href,'target':relative,'exists':target.is_file()})
    # Documentation link targets needed for two gold proposals; query source and
    # failure/success evidence are independently preserved.
    for relative in ['notes/oct12/gold-38-23-proposal.md','notes/oct12/参考答案与计分争议提案.md']:
        text = (ROOT / relative).read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)', text):
            url = urlparse(target.strip('<>'))
            if url.scheme or url.netloc:
                continue
            path = ((ROOT / relative).parent / unquote(url.path)).resolve()
            if path.is_relative_to(ROOT) and path.is_file():
                candidates.add(path.relative_to(ROOT).as_posix())
    def has_held_question(value):
        if isinstance(value, dict):
            if value.get('split') == 'holdout' and any(k in value for k in ['question','gold_sql','answer','reference','expected','title','input']):
                return True
            return any(has_held_question(v) for v in value.values())
        if isinstance(value, list):
            return any(has_held_question(v) for v in value)
        return False
    safe, excluded = [], []
    for relative in sorted(candidates):
        p = ROOT / relative
        if not p.is_file():
            continue
        unverified_text_variant = p.name == 'human_review.md'
        source_builder = p.suffix == '.py' and p.name.startswith('build_') and not relative.startswith('scripts/build_oct12_')
        copied_offline_evaluator = 'runtime-snapshot-' in relative and '/source/eval/' in relative
        forbidden = any(part in {'protected_holdout','.venv','.runtime','models','indexes','.git'} for part in p.parts) or 'holdout' in p.name.casefold() or p.name.startswith('.env') or source_builder or copied_offline_evaluator or unverified_text_variant
        mixed = False
        if not forbidden and p.suffix in {'.json','.jsonl'}:
            try:
                values = [json.loads(l) for l in p.read_text(encoding='utf-8-sig').splitlines() if l.strip()] if p.suffix == '.jsonl' else [json.loads(p.read_text(encoding='utf-8-sig'))]
                mixed = any(has_held_question(v) for v in values)
            except (ValueError, UnicodeError):
                forbidden = True
        if forbidden or mixed:
            reason = 'Historical review text is only inventory metadata; independently DEV-filtered actual responses are embedded instead' if unverified_text_variant else 'Offline dataset builder/copy may hardcode held questions; classification-only exclusion without inspecting answers' if source_builder or copied_offline_evaluator else 'private/protected/large dependency path' if forbidden else 'original mixed source contains held question material; only embedded DEV extraction is bundled'
            excluded.append({'path':relative,'reason':reason})
        else:
            safe.append(relative)
    with (ROOT / 'data/docs/manifest.csv').open(encoding='utf-8-sig', newline='') as stream:
        documents = list(csv.DictReader(stream))
    raw_documents = [{'doc_id':d['doc_id'],'format':d['format'],'path':d['path'],'exists':(ROOT / d['path']).is_file()} for d in documents]
    unique_links = list({entry['href']:entry for entry in links}.values())
    excluded_link_targets = [entry for entry in unique_links if entry['target'] not in safe]
    payload = {'scope':'Safe developer evidence/link targets only; no mixed held source inclusion, secrets, model/index weights; this allowlist does not authorize bulk inclusion of source directories', 'safe_dev_files':safe,'raw_documents':raw_documents,'pdf_paths':[d['path'] for d in documents if d['format']=='pdf'],'raw_document_count':len(documents),'pdf_count':sum(d['format']=='pdf' for d in documents),'relative_links':unique_links,'excluded_original_sources':excluded,'excluded_source_categories':['Original offline dataset/gold builders (including build_d3_aw_dataset.py, build_d3_clarify_cases.py, build_gold.py, build_d2_sql_datasets.py)','runtime-snapshot-*/source/eval/ offline copies','Original mixed gold_review.md/csv/JSONL or unverified historical human_review.md text','OHR qas_v2 and bulk QA caches; DEV reference material is embedded','protected_holdout or held labels/questions/predictions','Real .env/secret files, model/index weights and virtual environments'],'all_rendered_link_targets_exist':all(entry['exists'] for entry in links),'all_rendered_link_targets_safe_for_packaging':not excluded_link_targets,'excluded_link_targets':excluded_link_targets,'human_approval_changed':False}
    (OUT / 'evidence-package-paths.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def build_html(report):
    esc = html.escape
    def link(path):
        raw = str(path).split('#', 1)[0]
        fragment = '#' + str(path).split('#', 1)[1] if '#' in str(path) else ''
        p = ROOT / raw
        if p.is_file() and 'holdout' not in raw.casefold() and raw not in ['eval/datasets/nl2sql_chinook.jsonl', 'eval/datasets/nl2sql_chinook_d1_acceptance.jsonl', 'eval/datasets/nl2sql_chinook_d2.jsonl','eval/datasets/robust.jsonl','eval/datasets/rag_ohr.jsonl','eval/datasets/rag_single.jsonl','eval/reports/d2-acceptance/unified-review.json']:
            return '<a href="' + esc(Path(os.path.relpath(p, OUT)).as_posix() + fragment, quote=True) + '">' + esc(path) + '</a>'
        return esc(path) + '（原混合表仅列出处，DEV内容已提取在下面）'
    sections = []
    for i, row in enumerate(report['rows']):
        material = json.dumps({'source_materials':row['source_materials'], 'historical_reference_versions':row.get('historical_reference_versions', []), 'accepted_current_reference':row.get('accepted_current_reference'), 'reference_authorization':row.get('reference_authorization'), 'duplicate_group':row.get('duplicate_group')}, ensure_ascii=False, indent=2)
        actual = json.dumps(row['system_versions'], ensure_ascii=False, indent=2)
        sources = set(row.get('evidence_files', []))
        for source in row['source_materials']:
            sources.add(source['source'])
        links = '<br>'.join(link(p) for p in sorted(sources))
        decisions = ''.join('<label>' + esc(o['object']) + '<select data-object="' + esc(o['object'], quote=True) + '"><option>待审核</option><option>通过</option><option>有条件通过</option><option>拒绝/发现错误</option><option>证据不足</option><option>历史归档，不启用</option></select><small>' + esc(o['reason']) + ' | ' + esc(str(o['AI_judgment'])) + '</small></label>' for o in row['decision_objects'])
        suggestions = ''.join('<li>' + esc(text) + '</li>' for text in row['suggestions']) or '<li>未自动提出题面/标签修改；请按原材料逐项核对。</li>'
        version_controls = ''
        options = '<option>待审核</option><option>通过</option><option>有条件通过</option><option>拒绝/发现错误</option><option>证据不足</option><option>历史归档，不启用</option>'
        for version in row['system_versions']:
            fields = '<label>这个输出版本的整体判断<select data-version="' + version['content_sha256'] + '">' + options + '</select></label>'
            for dimension in version['review_dimensions'][1:]:
                fields += '<label>这个版本的' + esc(dimension) + '<select data-version="' + version['content_sha256'] + '" data-version-object="' + esc(dimension, quote=True) + '">' + options + '</select></label>'
            version_controls += '<details><summary>' + esc(version['version']) + ' | ' + esc(str(version['actual'].get('status', '未知状态'))) + '</summary>' + fields + '<pre>' + esc(json.dumps(version, ensure_ascii=False, indent=2)) + '</pre></details>'
        sections.append(f'<article class="item" data-key="{esc(row["review_key"], quote=True)}" data-hash="{row["content_sha256"]}" data-group="{esc(row["group"], quote=True)}"><h2>{i+1}. {esc(row["review_key"])} <span>{esc(row["group"])}</span></h2><p class="question">{esc(row["title"])}</p><ul>{suggestions}</ul>{decisions}<div class="edit"><label>清洗后题面/描述草案（可改；保存不应用）<textarea data-field="question">{esc(row["proposed_question"])}</textarea></label><label>新标签/处理草案（可改）<textarea data-field="label">{esc(row["proposed_label"])}</textarea></label><label>新gold SQL草案（如有）<textarea data-field="gold_sql">{esc(row.get("proposed_gold_sql", ""))}</textarea></label><label>你的理由、仍需补证据、条件或归档范围<textarea data-field="notes"></textarea></label></div><details><summary>展开完整标准材料、原题、SQL/结果、AI意见（已读取提取的DEV材料）</summary><pre>{esc(material)}</pre></details><details><summary>展开各版本真实回答，逐版本单独决定</summary>{version_controls if row["system_versions"] else "实际回答请见上述source_materials内原始版本与具体证据；这里未额外生成预测。"}</details><p class="links">{links}</p></article>')
    overview = json.dumps(report['summary'], ensure_ascii=False, indent=2)
    group_options = '<option value="">全部分组</option>' + ''.join('<option value="' + esc(group, quote=True) + '">' + esc(group) + '（' + str(count) + '）</option>' for group, count in report['summary']['pending_by_group'].items())
    auth = json.dumps(report['newly_explicit_authorizations'], ensure_ascii=False, indent=2)
    already = json.dumps({'authorized_objects':report['already_authorized'], 'confirmed_metric_material':report['confirmed_metric_material'],'alias_deduplication':report['alias_deduplication'],'rag_reference_deduplication':report['rag_reference_deduplication'],'sql_reference_deduplication':report['sql_reference_deduplication']}, ensure_ascii=False, indent=2)
    meta = json.dumps({'source_report': 'eval/reports/oct12/manual-review/' + TITLE + '.json', 'dataset_sha256': digest(report['rows']), 'rows': [{'key': r['review_key'], 'hash': r['content_sha256'], 'ids': r['original_ids']} for r in report['rows']]}, ensure_ascii=False).replace('<', '\\u003c')
    css = 'body{max-width:1180px;margin:28px auto;padding:0 24px;font:15px/1.65 Microsoft YaHei,sans-serif;color:#202c40;background:#f6f8fb}h1{font-size:27px}h2{font-size:20px}h2 span{font-size:13px;font-weight:400;color:#52647a}article{background:white;border:1px solid #dce3ed;border-radius:8px;padding:18px;margin:16px 0}.bar{position:sticky;top:0;background:#e8eff8;padding:12px;z-index:2}input,button,select,textarea{font:inherit;padding:7px;border:1px solid #b8c7da;border-radius:4px}label{display:block;margin:10px 0}select{margin-left:12px}small{display:block;color:#516179}textarea{display:block;width:calc(100% - 18px);min-height:65px}.edit{display:grid;grid-template-columns:1fr 1fr;gap:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3f8;padding:14px;max-height:650px;overflow:auto}details{margin:14px 0}summary{cursor:pointer;font-weight:600}a{color:#135ba0;overflow-wrap:anywhere}.links{font-size:13px}.question{font-size:16px}.notice{background:#fff5d8;padding:15px;border-radius:5px}@media(max-width:760px){.edit{grid-template-columns:1fr}}'
    js = """
const meta = META;
const storageKey = 'oct12-review-draft-v1';
let saved = {}; try { saved = JSON.parse(localStorage.getItem(storageKey) || '{}'); } catch(_) {}
function gather(article) {
 const item = {review_key:article.dataset.key, content_sha256:article.dataset.hash, decisions:{}, version_decisions:{}, version_object_decisions:{}, question:'', label:'', gold_sql:'', notes:''};
 article.querySelectorAll('select[data-object]').forEach(s => item.decisions[s.dataset.object] = s.value);
 article.querySelectorAll('select[data-version]:not([data-version-object])').forEach(s => item.version_decisions[s.dataset.version] = s.value);
 article.querySelectorAll('select[data-version-object]').forEach(s => { const dims=item.version_object_decisions[s.dataset.version] || {}; dims[s.dataset.versionObject]=s.value; item.version_object_decisions[s.dataset.version]=dims; });
 article.querySelectorAll('textarea[data-field]').forEach(t => item[t.dataset.field] = t.value);
 return item;
}
document.querySelectorAll('article.item').forEach(a => {
 const s = saved[a.dataset.key];
 if(s && s.content_sha256 === a.dataset.hash) { a.querySelectorAll('select[data-object]').forEach(t => t.value=s.decisions[t.dataset.object]||'待审核'); a.querySelectorAll('select[data-version]:not([data-version-object])').forEach(t=>t.value=(s.version_decisions||{})[t.dataset.version]||'待审核'); a.querySelectorAll('select[data-version-object]').forEach(t=>t.value=((s.version_object_decisions||{})[t.dataset.version]||{})[t.dataset.versionObject]||'待审核'); a.querySelectorAll('textarea[data-field]').forEach(t=>{if(s[t.dataset.field]!==undefined)t.value=s[t.dataset.field];}); }
 a.addEventListener('change',()=>{saved[a.dataset.key]=gather(a);try{localStorage.setItem(storageKey,JSON.stringify(saved));document.getElementById('state').textContent='草稿已保存在当前浏览器';}catch(_){document.getElementById('state').textContent='浏览器不允许保存，请导出JSON';}});
});
function filterRows() { const q=document.getElementById('search').value.trim().toLowerCase(), group=document.getElementById('group').value;let visible=0;document.querySelectorAll('article.item').forEach(a=>{a.hidden=(group && a.dataset.group!==group)||!a.textContent.toLowerCase().includes(q);if(!a.hidden)visible++;});document.getElementById('visible').textContent='显示'+visible+'项';}
document.getElementById('search').addEventListener('input', filterRows);
document.getElementById('group').addEventListener('change', filterRows);
filterRows();
document.getElementById('export').addEventListener('click',()=>{
 const records=[...document.querySelectorAll('article.item')].map(gather);
 const payload={schema_version:'oct12-human-decisions-draft-v1',source_report:meta.source_report,dataset_sha256:meta.dataset_sha256,exported_at_utc:new Date().toISOString(),human_signature:null,human_confirmation_date:null,automatic_application:false,records};
 const u=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='10月12日-人工审核决定草稿.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);
});
""".replace('META', meta)
    document = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>' + TITLE + '</title><style>' + css + '</style><body><h1>' + TITLE + '</h1><p class="notice">逐项核对原题、gold、实际回答、引用和候选关系，各自独立。页面填写是你的审核草稿，不自动改代码、题库、别名、旧审核状态或签名。导出后交回统一执行。保留题不在本页展开，需独立环境审核。</p><p>先定 <a href="../../../../notes/oct12/gold-38-23-proposal.md">sql-38 / robust-23 两个gold</a>。题面清洗保留业务条件、单位、排序和半开区间，去掉模型执行/应答指令。清洗及新标签均未应用。</p><p>选择分组可分别过AW目录68表/456列、专项题、RAG和新增JOIN。逐版本选择“历史归档”只表示你对那个旧输出的处理，不代表确认新答案。导出JSON中的时间是导出时间，签名和人工确认日期保持空。</p><details><summary>本轮统计、去重方式与待核范围</summary><pre>' + esc(overview) + '</pre><p>同一对象的MD/HTML/JSON及相同输出内容合并出处；不同gold版本、不同系统输出和多轮控制器差异保留，不能只按题面去重。</p></details><details><summary>已明确授权的五项新口径，不重复要求确认</summary><pre>' + esc(auth) + '</pre></details><details><summary>已有人工授权对象与批准范围</summary><pre>' + esc(already) + '</pre></details><div class="bar"><select id="group">' + group_options + '</select><input id="search" placeholder="筛选编号、关键词"><button id="export">导出决定JSON</button><span id="visible"></span> <span id="state">更改只存在本页草稿</span></div>' + ''.join(sections) + '<script>' + js + '</script></body></html>'
    (OUT / (TITLE + '.html')).write_text(document, encoding='utf-8')


if __name__ == '__main__':
    main()
