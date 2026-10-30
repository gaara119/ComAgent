"""Metric-only proof for a retrieved manual's per-customer invoice amount.

The same registered document may be read deterministically to obtain its actual
invoice formula. This is recorded separately from the retrieved passage. It
never chooses a period, ranking, tie policy, default, entity or SQL answer.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from xml.etree import ElementTree
from zipfile import ZipFile

from sqlglot import exp
from sqlglot.optimizer.scope import Scope, traverse_scope

from qa_agent.sql.document_metric_lineage import _compact, _physical_rowset
from qa_agent.sql.validator import SQLValidationError


_EXPRESSION = 'SUM(invoice.total)'


def customer_amount_request(question):
    if not isinstance(question, str):
        return False
    money = r'花钱|消费金额|消费额|发票金额|发票总额|开票额|金额'
    if (re.search(r'例如|比如|示例|举例|假设|如果', question)
            or re.search(r'(?:不要|不用|不按|不看|不再|不算|无需|取消|并非|不是)[^，,。；;！？!?]{0,16}(?:'+money+r')', question)
            or re.search(r'(?:'+money+r')[^，,。；;！？!?]{0,8}(?:不算|不采用|先不|不要)', question)
            or re.search(r'(?:改按|改看|改用|换成|只按|只看|只统计|而是按)[^，,。；;！？!?]{0,16}(?:数量|张数|票数|平均|AVG|COUNT)', question, re.I)):
        return False
    return bool(re.search(r'客户|\bcustomer\b', question, re.I)
        and re.search(r'花钱|消费金额|消费额|发票金额|发票总额|开票额|金额|\bspend(?:ing)?\b|\bamount\b', question, re.I)
        and not re.search(r'利润|成本|毛利|净利|profit|cost', question, re.I))


def _answer_agrees(answer):
    positive = False
    for clause in re.split(r'[，,。；;\n]+|而(?:是|按|采用)', answer):
        clause = _compact(re.sub(r'\[E\d+\]', '', clause)).casefold()
        if not clause:
            continue
        wanted = _compact(_EXPRESSION).casefold()
        # Mentioning another explicitly named grain or its alternatives does
        # not change the customer's metric. It also cannot prove this one.
        if re.search(r'曲目|艺术家|热门', clause) and not re.search(r'客户|customer', clause):
            continue
        negative = re.search(r'不是|不按|不用|不采用|不使用|不得|不能|不要|未给|没有|并非', clause)
        if negative:
            if wanted in clause or re.search(r'(?:客户|customer).{0,24}(?:金额|money|amount)', clause):
                return False
            continue
        formulas = re.findall(r'(?<![a-z0-9_])(?:sum|avg|count|min|max)\([^()]*\)', clause)
        if any(formula != wanted for formula in formulas):
            return False
        if re.search(r'平均|均值|人均|计数|购买数量|发票张数|明细行数', clause):
            return False
        positive |= wanted in clause or bool(re.search(
            r'(?:客户|customer).{0,40}(?:金额口径|按金额|金额排序|发票金额|消费金额)', clause))
    return positive


def resolve_customer_amount_definition(dependencies, question, catalog=None):
    """Return actual source + approved metric, or None; never fill a default.

    The quoted dependency must itself identify a customer's amount metric (or
    invoice SUM), agree with it, and be an exact passage of its registered file.
    A formula read elsewhere in that SAME file is explicitly a program read,
    not a claim that the model retrieved or cited that formula paragraph.
    """
    if not customer_amount_request(question) or not isinstance(dependencies, dict):
        return None
    if catalog is not None and str(catalog.database).casefold() != 'chinook':
        return None
    from qa_agent.config import get_settings
    from qa_agent.documents import load_documents, verify_document_hash
    rules_path = get_settings().catalog_path.parents[1]/'rules/metric_definitions.json'
    rules = json.loads(rules_path.read_text(encoding='utf8'))
    metrics = [m for m in rules.get('metrics', ()) if m.get('id') == 'sales_revenue']
    if (rules.get('review_status') != 'approved' or len(metrics) != 1
            or metrics[0].get('grain') != 'invoice'
            or _compact(metrics[0].get('expression', '')).casefold() != _compact(_EXPRESSION).casefold()):
        return None
    registered = {d['doc_id']: d for d in load_documents()
                  if d.get('entity_ref') == 'chinook:business-metrics'}
    found = []
    for step, dep in dependencies.items():
        if (dep.get('source') != 'documents' or dep.get('status') != 'SUCCEEDED'
                or dep.get('dependency_role') not in {None, 'metric_definition'}
                or 'chinook:business-metrics' not in dep.get('entity_refs', ())
                or not _answer_agrees(str(dep.get('answer') or ''))):
            continue
        for evidence in dep.get('evidences', ()):
            doc = registered.get(evidence.get('doc_id'))
            quote = str(evidence.get('text') or '')
            if doc is None or doc.get('format') != 'docx' or not quote:
                continue
            verify_document_hash(doc)
            with ZipFile(doc['resolved_path']) as archive:
                xml = ElementTree.fromstring(archive.read('word/document.xml'))
            paragraphs = [''.join(p.itertext()) for p in xml.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')]
            actual = '\n'.join(paragraphs)
            if quote not in actual:
                continue
            # The actual retrieved quote must connect this rule to customer
            # amount or the invoice formula. A random paragraph in a real file
            # is not a grant to load arbitrary metrics from the entire manual.
            compact_quote = _compact(quote)
            if not (re.search(r'客户.{0,30}金额口径', compact_quote)
                    or _compact(_EXPRESSION).casefold() in compact_quote.casefold()):
                continue
            candidates = [(i, p) for i, p in enumerate(paragraphs)
                if re.match(r'发票层面按\s*SUM\s*\(\s*invoice\.total\s*\)\s*汇总', p, re.I)]
            if len(candidates) != 1:
                continue
            index, definition = candidates[0]
            section = paragraphs[index-1] if index else ''
            found.append({'dependency': step, 'metric': 'sales_revenue',
                'name': metrics[0].get('name'), 'grain': 'invoice', 'expression': _EXPRESSION,
                'customer_measure': 'per-customer sum of that customer invoices',
                'retrieved_evidence': {'evidence_id': evidence.get('evidence_id'), 'doc_id': doc['doc_id'],
                    'quote': quote, 'quote_sha256': sha256(quote.encode()).hexdigest(),
                    'document_sha256': doc['content_hash']},
                'program_read_definition': {'doc_id': doc['doc_id'], 'document_sha256': doc['content_hash'],
                    'section': section, 'paragraph_index_zero_based': index, 'quote': definition,
                    'quote_sha256': sha256(definition.encode()).hexdigest(),
                    'already_present_in_retrieved_evidence': definition in quote,
                    'source': 'program_read_same_actually_retrieved_registered_document'},
                'approved_metric': {'id': metrics[0]['id'], 'name': metrics[0].get('name'),
                    'grain': metrics[0]['grain'], 'expression': metrics[0]['expression'],
                    'rules_path': str(rules_path), 'rules_sha256': sha256(rules_path.read_bytes()).hexdigest()},
                'metric_only': True, 'period_verified': False, 'ranking_verified': False,
                'top_n_verified': False, 'default_authorized': False,
                'authority': 'actual_registered_document_and_approved_metric_only_not_semantic_state'})
    if not found:
        return None
    identities = {(p['program_read_definition']['document_sha256'],
                   p['program_read_definition']['quote_sha256'], p['approved_metric']['rules_sha256']) for p in found}
    return found[0] if len(identities) == 1 else None


def validate_customer_amount_consumption(sql, catalog, definition):
    """Prove only a visible per-customer SUM of real invoice totals, no fanout."""
    from qa_agent.sql.repair_guard import _qualified
    from qa_agent.sql.document_repeat_lineage import prove_direct_customer_group_grain

    def deny(message):
        raise SQLValidationError('客户发票金额文档消费：'+message)

    tree = _qualified(sql, catalog)
    scopes = list(traverse_scope(tree))
    root = next((s for s in scopes if s.parent is None), None)
    if root is None or not isinstance(tree, exp.Select):
        deny('最终输出不是已支持的SELECT。')
    visited = set()
    measures, identities = [], []

    def un(node):
        while isinstance(node, (exp.Alias, exp.Paren)):
            node = node.this
        return node

    def transparent(scope):
        q = scope.expression
        return (isinstance(q, exp.Select) and len(scope.selected_sources) == 1
                and not q.args.get('joins') and not any(q.args.get(k) for k in ('group', 'having', 'distinct', 'qualify')))

    def trace(node, scope, depth=0):
        if depth > 16:
            deny('投影谱系超过有限深度。')
        node = un(node)
        if isinstance(node, exp.Round):
            digits = node.args.get('decimals')
            if not isinstance(digits, exp.Literal) or digits.is_string or not str(digits.this).isdigit() or not 0 <= int(digits.this) <= 9:
                deny('未知ROUND变换不能冒充原始发票金额。')
            # Display precision remains the caller's separate authority check.
            return trace(node.this, scope, depth+1)
        if isinstance(node, exp.Column):
            source = scope.sources.get(node.table)
            if isinstance(source, Scope):
                if not transparent(scope):
                    deny('消费派生金额的外层含未证明连接、重分组或去重。')
                candidates = [p for p in source.expression.selects if p.alias_or_name == node.name]
                if len(candidates) != 1:
                    deny('派生投影没有唯一真实来源。')
                marker = (id(source), node.name)
                if marker in visited:
                    deny('循环投影没有真实物理来源。')
                visited.add(marker)
                return trace(candidates[0], source, depth+1)
            if isinstance(source, exp.Table) and (source.db or 'public') == 'public':
                return node, scope
        return node, scope

    for projection in tree.selects:
        visited.clear()
        value, owner = trace(projection, root)
        if isinstance(value, exp.Sum):
            field = un(value.this)
            physical = owner.sources.get(field.table) if isinstance(field, exp.Column) else None
            if not (isinstance(physical, exp.Table) and (physical.db or 'public') == 'public'
                    and physical.name == 'invoice' and field.name == 'total'):
                deny('需要实际SUM(invoice.total)，不能用明细金额、DISTINCT、CAST、AVG或COUNT替代。')
            sources = _physical_rowset(owner, catalog, 'invoice')
            prove_direct_customer_group_grain(owner, catalog)
            customer = catalog.get_table('customer', 'public')
            invoice = catalog.get_table('invoice', 'public')
            if (customer.primary_key != ('customer_id',) or invoice.primary_key != ('invoice_id',)
                    or any(c.nullable for c in invoice.columns if c.name in {'customer_id', 'invoice_id'})
                    or not any(fk.get('columns') == ['customer_id'] and
                        fk.get('references') == {'schema': 'public', 'table': 'customer', 'columns': ['customer_id']}
                        for fk in invoice.foreign_keys)):
                deny('实际目录未证明invoice到customer唯一主键的真实关系。')
            measures.append((owner, value, sources))
        elif isinstance(value, exp.Column):
            physical = owner.sources.get(value.table)
            if (isinstance(physical, exp.Table) and (physical.db or 'public') == 'public'
                    and physical.name in {'customer', 'invoice'} and value.name == 'customer_id'):
                identities.append(owner)
        elif value.find(exp.AggFunc) or isinstance(value, (exp.AggFunc, exp.Mul, exp.Div, exp.Cast, exp.Coalesce, exp.Subquery)):
            deny('最终金额须实际消费真实SUM，不能变成平均、比例、任意变换或补零。')
    if len(measures) != 1 or measures[0][0] not in identities:
        deny('最终需同时消费同一客户粒度的真实客户键与一项发票金额，未用CTE/仅排序中的SUM不构成证明。')
    owner, aggregate, _ = measures[0]
    return {**definition, 'physical_consumption': {'verified': True,
        'mode': 'consumed_customer_PK_grouped_invoice_SUM_no_fanout',
        'aggregate': aggregate.sql(dialect='postgres'),
        'group_scope': owner.expression.sql(dialect='postgres'),
        'period_verified': False, 'filters_verified': False, 'ranking_verified': False,
        'top_n_verified': False, 'precision_authorized': False}}
