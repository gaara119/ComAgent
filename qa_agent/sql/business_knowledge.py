"""Shared, source-labelled business knowledge; never a semantic gate.

Both BASE and enhanced generation see the same existing definitions/default
policy text. This module neither evaluates applicability nor commits state,
grants a default, selects a country, or validates a generated query.
"""
from hashlib import sha256
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
METRIC_FIELDS = {'id','name','grain','expression','empty_behavior','alternative',
                 'alternatives','limitation','tie_breaker','short_label_proposal'}
DEFAULT_FIELDS = {'region_scope','missing_period','who_buys_most','invoice_revenue_share'}


def business_knowledge(root: Path | None = None) -> dict | None:
    root = root or ROOT
    references = []
    metric_path = root / 'data/rules/metric_definitions.json'
    if metric_path.is_file():
        raw = metric_path.read_bytes()
        metrics = json.loads(raw.decode('utf-8-sig'))
        if metrics.get('review_status') == 'approved':
            references.append({'source_id':'project:confirmed_metric_definitions',
                'path':'data/rules/metric_definitions.json','sha256':sha256(raw).hexdigest(),
                'version':metrics.get('version'),'review_status':'approved',
                'general':metrics.get('general',{}),
                'metrics':[{k:v for k,v in row.items() if k in METRIC_FIELDS}
                           for row in metrics.get('metrics',[]) if isinstance(row,dict)],
                'definition_document_alone_enables_defaults':False})
    default_path = root / 'qa_agent/clarify/clarify_rules.yaml'
    if default_path.is_file():
        raw = default_path.read_bytes()
        rules = yaml.safe_load(raw.decode('utf-8-sig'))
        if isinstance(rules,dict) and isinstance(rules.get('authorized_defaults'),dict):
            references.append({'source_id':'project:existing_authorized_defaults',
                'path':'qa_agent/clarify/clarify_rules.yaml','sha256':sha256(raw).hexdigest(),
                'version':rules.get('version'),'authorization_source':rules.get('source'),
                'authorized_defaults':{k:v for k,v in rules['authorized_defaults'].items() if k in DEFAULT_FIELDS},
                'interpretation':'只提供既有政策原文及其适用条件，不在此计算本轮适用性。'})
    if not references:
        return None
    return {'database':'chinook','references':references,'authority':'既有项目业务资料，两个实验组相同；不是本轮确认合同或执行授权。',
        'priority':'本轮明确要求及仍有效的用户约定优先。仅在实际满足既有授权默认的适用范围时使用；'
                   '有明确期间时保留，不因缺省条目覆盖已有条件；真正缺失且无适用授权时不编造。',
        'not_included':['evaluation_questions','Gold_SQL','reference_results','SQL_examples','predicted_values'],
        'semantic_gate_invoked':False,'state_committed':False}
