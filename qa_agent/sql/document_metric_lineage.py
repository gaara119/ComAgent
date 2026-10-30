"""Bounded consumption of existing registered manual measures, never a gate.

The complete original request supplies period and named filter. The actual
registered document supplies only its already approved measure, not those
user facts. No model/state/Gold, execution, default or new alias approval.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
import unicodedata
from xml.etree import ElementTree
from zipfile import ZipFile

from sqlglot import exp
from sqlglot.optimizer.scope import build_scope

from qa_agent.sql.validator import SQLValidationError


def _deny(message):
    raise SQLValidationError('手册指标消费：' + message)


def _compact(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text)).replace('’', "'")


def _atoms(node):
    # Unknown OR branches remain whole atoms and must be rejected, not silently
    # discarded by an intersection-of-mandatory-atoms optimization.
    if node is None:
        return []
    if isinstance(node, (exp.Where, exp.Paren)):
        return _atoms(node.this)
    if isinstance(node, exp.And):
        return _atoms(node.left) + _atoms(node.right)
    return [node]


def document_metric_target(question):
    """Identify only a requested manual measure, not its filters or formula."""
    if not re.search(r'手册|口径|定义', question):
        return None
    if re.search(r'曲目热度|热门曲目|曲目最受欢迎', question) and re.search(r'卖|售|购买|多少|数量', question):
        return '热门曲目'
    if re.search(r'曲目.*销售额|销售额.*曲目', question) and re.search(r'占|比例|百分|多少|计算', question):
        return '曲目销售额'
    return None


def _request(question, kind):
    text = _compact(question).rstrip('？?。')
    prefix = r'(?:按|根据|依据)(?:业务指标)?口径手册'
    if kind == '曲目销售额':
        match = re.fullmatch(prefix + r'[，,]?(?P<year>\d{4})年(?P<value>.+?)(?:格式)?的?销售额占(?:全年|同期全部|当年全部)曲目销售额的?(?:百分之几|百分比|比例)(?:是多少)?', text)
        column = 'media_type.name'
    else:
        match = re.fullmatch(prefix + r'(?:里|中)?(?:曲目热度|热门曲目|曲目最受欢迎)的?口径[，,]?(?P<year>\d{4})年(?P<value>.+?)歌单里?的?曲目(?:卖了|售出|购买了)(?:多少份|多少件)', text)
        column = 'playlist.name'
    if match is None or not 1 <= int(match['year']) < 9999:
        _deny('原文对象、完整期间或额外条件超出有限支持，不能选默认或丢弃条件。')
    from qa_agent.config import get_settings
    from qa_agent.nlu.value_index import load_value_index
    index = load_value_index(get_settings().value_index_path)
    value = match['value'].removesuffix('格式')
    pairs = {(item.standard_value, item.candidate_id) for item in index.records
             if item.column == column and item.kind in {'standard', 'alias'}
             and _compact(item.surface).casefold() == value.casefold()} if index else set()
    if len(pairs) != 1:
        _deny('原文名称没有唯一的实际 direct 索引身份；条件候选不升级为绑定。')
    year = int(match['year'])
    return {'period': {'start': f'{year:04d}-01-01', 'end': f'{year + 1:04d}-01-01'},
            'column': column, 'value': next(iter(pairs))[0], 'candidate_id': next(iter(pairs))[1],
            'question_sha256': sha256(question.encode()).hexdigest()}


def _answer_acknowledges(answer, kind, expression):
    """A bounded consistency check, not a formula extracted from model prose.

    Source evidence + the approved registry alone determine the formula. A
    Chinese paraphrase need not repeat SQL. Conversely mentioning the right
    formula while negating it never acknowledges that definition.
    """
    wanted = _compact(expression).casefold()
    positive = False
    parts = re.split(r'[，,。；;\n]+|而(?:是|按|采用|使用)', answer)
    for part in parts:
        part = _compact(re.sub(r'\[E\d+\]', '', part)).casefold()
        if not part:
            continue
        # The manual distinguishes invoice sales from track/artist sales;
        # faithfully mentioning that other grain is not a conflicting formula.
        if (kind == '曲目销售额' and re.search(r'发票(?:层面|粒度)', part)
                and not re.search(r'曲目|艺术家', part)):
            continue
        if re.search(r'备选|可选|替代口径', part):
            continue
        if re.search(r'不按|不用|不采用|不使用|不是|不能|不得|不应|不要|而非|禁止', part):
            continue
        formulas = re.findall(r'(?<![a-z0-9_])(?:sum|avg|count|min|max)\([^()]*\)', part)
        if any(formula != wanted for formula in formulas):
            return False
        if kind == '曲目销售额':
            if re.search(r'平均|均值|计数|记录数|发票数', part):
                return False
            paraphrase = re.search(r'(?:单价|unit_price).{0,8}(?:乘以?|×|\*).{0,8}'
                r'(?:购买数量|数量|quantity).{0,10}(?:加总|合计|求和|汇总|累加|总和)', part)
        else:
            if re.search(r'平均|均值|明细行数|发票数|曲目数|歌单收录数|销售额|销售金额', part):
                return False
            paraphrase = re.search(r'(?:购买|售出|销售)的?(?:数量|份数).{0,8}'
                r'(?:合计|加总|求和|汇总|累加|总和)', part)
        positive |= wanted in part or bool(paraphrase)
    return positive


def _definition(dependencies, kind):
    from qa_agent.config import get_settings
    from qa_agent.documents import load_documents, verify_document_hash
    docs = {d['doc_id']: d for d in load_documents() if d.get('entity_ref') == 'chinook:business-metrics'}
    rules_path = get_settings().catalog_path.parents[1] / 'rules/metric_definitions.json'
    rules = json.loads(rules_path.read_text(encoding='utf-8'))
    metric_id = 'sales_revenue' if kind == '曲目销售额' else 'popular_tracks'
    metrics = [item for item in rules.get('metrics', ()) if item.get('id') == metric_id]
    expression = ('SUM(invoice_line.unit_price * invoice_line.quantity)' if kind == '曲目销售额'
                  else 'SUM(invoice_line.quantity)')
    if rules.get('review_status') != 'approved' or len(metrics) != 1 or _compact(expression).lower() not in _compact(json.dumps(metrics[0], ensure_ascii=False)).lower():
        _deny('真实已批准指标规则不支持该明细度量。')
    found = []
    for step_id, dep in dependencies.items():
        if (dep.get('source') != 'documents' or dep.get('status') != 'SUCCEEDED'
                or dep.get('dependency_role') not in {None, 'metric_definition'}
                or 'chinook:business-metrics' not in dep.get('entity_refs', ())):
            continue
        if not _answer_acknowledges(str(dep.get('answer') or ''), kind, expression):
            continue
        for evidence in dep.get('evidences', ()):
            doc = docs.get(evidence.get('doc_id'))
            text = str(evidence.get('text') or '')
            compact = _compact(text)
            if doc is None or _compact(expression).lower() not in compact.lower():
                continue
            verify_document_hash(doc)
            if doc['format'] != 'docx':
                _deny('当前只证明已登记手册的实际 DOCX 段落，不猜未知文档格式。')
            with ZipFile(doc['resolved_path']) as archive:
                root = ElementTree.fromstring(archive.read('word/document.xml'))
            actual = '\n'.join(''.join(p.itertext()) for p in root.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'))
            if not compact or compact not in _compact(actual):
                continue
            if kind == '曲目销售额' and not re.search(r'曲目或艺术家层面', text):
                continue
            if kind == '热门曲目' and not re.search(r'热门曲目|曲目最受欢迎', text):
                continue
            found.append({'dependency': step_id, 'metric': metric_id,
                'expression': expression, 'doc_id': doc['doc_id'], 'content_sha256': doc['content_hash'],
                'definition_quote': text, 'rules_sha256': sha256(rules_path.read_bytes()).hexdigest(),
                'answer_relation': 'bounded_consistent_acknowledgement_not_formula_authority'})
    if not found:
        missing = SQLValidationError('手册指标消费：缺少实际手册定义回答及其可逐字回查的登记证据，不能仅凭模型回答执行。')
        missing.sql_repairable = False  # SQL regeneration cannot manufacture a missing source.
        raise missing
    return found[0]


def _physical_rowset(scope, catalog, base):
    """Only real nonnull FK -> physical PK inner lookup preserves each fact."""
    sources = {alias: value for alias, (_, value) in scope.selected_sources.items()}
    if not sources or any(not isinstance(value, exp.Table) or (value.db or 'public') != 'public' for value in sources.values()):
        _deny('购买数量必须直接消费真实物理明细，未知派生行集不冒充粒度证明。')
    seen = {alias for alias, value in sources.items() if value.name == base}
    if len(seen) != 1:
        _deny('明细粒度没有唯一物理主来源。')
    equalities = []
    for join in scope.expression.args.get('joins') or ():
        atoms = _atoms(join.args.get('on'))
        if (join.args.get('side') or join.args.get('using') or join.args.get('method')
                or str(join.args.get('kind') or '').upper() not in {'', 'INNER'} or not atoms
                or any(not isinstance(a, exp.EQ) or not isinstance(a.left, exp.Column) or not isinstance(a.right, exp.Column) for a in atoms)):
            _deny('明细关联只支持实际非空外键到主键的内连接，不能混入筛选或多行来源。')
        equalities.extend(atoms)
    actual = {frozenset(((a.left.table, a.left.name), (a.right.table, a.right.name))) for a in equalities}
    used = set()
    while len(seen) < len(sources):
        before = set(seen)
        for alias, source in sources.items():
            if alias in seen:
                continue
            target = catalog.get_table(source.name, source.db or 'public')
            for old in tuple(seen):
                physical = catalog.get_table(sources[old].name, sources[old].db or 'public')
                for fk in physical.foreign_keys:
                    ref = fk.get('references') or {}
                    columns, remote = fk.get('columns') or [], ref.get('columns') or []
                    if (ref.get('table') != target.name or (ref.get('schema') or 'public') != target.schema
                            or not columns or len(columns) != len(remote) or set(remote) != set(target.primary_key)
                            or any(next(c for c in physical.columns if c.name == name).nullable for name in columns)):
                        continue
                    required = {frozenset(((old, left), (alias, right))) for left, right in zip(columns, remote)}
                    if required <= actual:
                        seen.add(alias)
                        used.update(required)
        if before == seen:
            _deny('关联无法证明每条实际明细恰好一次；歌单成员限制请使用按曲目键相关的 EXISTS 或 IN 半连接，不能用可能重复明细的歌单 JOIN。')
    if not actual <= used:
        _deny('关联含未证明额外条件，不能默改明细人口。')
    return sources


def _quantity(sql, catalog, request, playlist_identity=None):
    from qa_agent.sql.repair_guard import _qualified
    from qa_agent.sql.semantic_guard import _midnight_date
    tree = _qualified(sql, catalog)
    scope = build_scope(tree)
    if (not isinstance(tree, exp.Select) or scope is None or tree.find(exp.CTE)
            or any(tree.args.get(k) for k in ('group', 'having', 'distinct', 'offset', 'qualify'))
            or len(tree.expressions) != 1):
        _deny('购买数量只支持一个完整明细合计，不把分组、去重或未消费 CTE 当同一度量。')
    limit = tree.args.get('limit')
    if limit is not None and (not isinstance(limit, exp.Limit) or not isinstance(limit.expression, exp.Literal)
            or limit.expression.is_string or not str(limit.expression.this).isdigit() or int(limit.expression.this) < 1):
        _deny('最终合计不能被非法限制或 LIMIT 0 隐藏。')
    sources = _physical_rowset(scope, catalog, 'invoice_line')
    node = tree.expressions[0]
    while isinstance(node, (exp.Alias, exp.Paren)):
        node = node.this
    def field(node, physical, column):
        return (isinstance(node, exp.Column) and node.name == column and node.table in sources
                and sources[node.table].name == physical)
    if not isinstance(node, exp.Sum) or node.args.get('distinct') or not field(node.this, 'invoice_line', 'quantity'):
        _deny('实际输出不是手册 SUM(invoice_line.quantity)，不把记录数、金额或零填充视作购买数量。')
    covered, membership_methods = set(), []
    for atom in _atoms(tree.args.get('where')):
        if isinstance(atom, (exp.GTE, exp.LT)) and field(atom.left, 'invoice', 'invoice_date'):
            key = 'start' if isinstance(atom, exp.GTE) else 'end'
            if _midnight_date(atom.right) != request['period'][key]:
                _deny('实际发票日期与原文明示期间不一致。')
            covered.add(key)
            continue
        is_exists = isinstance(atom, exp.Exists)
        if not is_exists and (not isinstance(atom, exp.In) or not (
                field(atom.this, 'invoice_line', 'track_id') or field(atom.this, 'track', 'track_id'))):
            _deny('实际数量行集含未证明条件，不能忽略原文或另添筛选。')
        nested = atom.this if is_exists else atom.args.get('query')
        nested = nested.this if isinstance(nested, exp.Subquery) else nested
        sub = build_scope(nested) if isinstance(nested, exp.Select) else None
        if sub is None or any(nested.args.get(k) for k in ('group', 'having', 'limit', 'offset', 'qualify', 'order')):
            _deny('歌单成员必须是完整真实半连接集合，不能先截断或任意取一。')
        members = _physical_rowset(sub, catalog, 'playlist_track')
        member_tables = set(s.name for s in members.values())
        if (len(nested.expressions) != 1 or member_tables != {'playlist_track', 'playlist'}
                and not (playlist_identity and member_tables == {'playlist_track'})):
            _deny('歌单成员没有实际消费唯一的关联表及歌单来源。')
        projection = nested.expressions[0]
        projection = projection.this if isinstance(projection, exp.Alias) else projection
        if is_exists:
            if not isinstance(projection, exp.Literal) or projection.is_string or str(projection.this) != '1':
                _deny('EXISTS 只证明实际成员存在，不能用 COUNT 等保证总有一行的投影改变空集真值。')
        elif (not isinstance(projection, exp.Column) or projection.name != 'track_id'
                or projection.table not in members or members[projection.table].name != 'playlist_track'):
            _deny('歌单半连接投影不是实际曲目键。')
        conditions = _atoms(nested.args.get('where'))
        member_checks, correlations = set(), set()
        for condition in conditions:
            if not isinstance(condition, exp.EQ):
                _deny('歌单半连接含 OR 或未证明条件。')
            for left, right in ((condition.left, condition.right), (condition.right, condition.left)):
                if (isinstance(left, exp.Column) and left.table in members
                        and members[left.table].name == 'playlist' and left.name == 'name'
                        and isinstance(right, exp.Literal) and right.is_string and right.this == request['value']):
                    member_checks.add('name')
                    break
                actual_key = False
                if playlist_identity and isinstance(left, exp.Column) and left.table in members:
                    source = catalog.get_table(members[left.table].name, 'public')
                    actual_key = (source.name == 'playlist' and left.name == playlist_identity['pk_column']) or any(
                        fk.get('columns') == [left.name]
                        and fk.get('references', {}).get('table') == 'playlist'
                        and fk.get('references', {}).get('schema', 'public') == 'public'
                        and fk.get('references', {}).get('columns') == [playlist_identity['pk_column']]
                        for fk in source.foreign_keys)
                if (actual_key
                        and isinstance(right, exp.Literal) and not right.is_string
                        and str(right.this) == str(playlist_identity['playlist_id'])
                        and playlist_identity['playlist_name'] == request['value']):
                    member_checks.add('actual_pk')
                    break
                if (is_exists and isinstance(left, exp.Column) and left.table in members
                        and members[left.table].name == 'playlist_track' and left.name == 'track_id'
                        and isinstance(right, exp.Column) and right.table not in members
                        and (field(right, 'invoice_line', 'track_id') or field(right, 'track', 'track_id'))):
                    member_checks.add('correlation')
                    correlations.add((right.table, right.name))
                    break
            else:
                _deny('歌单实际身份、相关曲目键或额外条件无法由原问和真实目录证明。')
        identity_check = 'actual_pk' if 'actual_pk' in member_checks else 'name'
        expected_checks = {identity_check, 'correlation'} if is_exists else {identity_check}
        external = {(c.table, c.name) for c in sub.external_columns}
        if (len(conditions) != len(expected_checks) or member_checks != expected_checks
                or (external != correlations if is_exists else bool(external))):
            _deny('EXISTS 必须与当前真实曲目键相关，IN 成员集不得偷读外层，不能忽略额外或缺失条件。')
        covered.add('membership')
        membership_methods.append('correlated_exists' if is_exists else 'track_id_in')
    if covered != {'start', 'end', 'membership'}:
        _deny('购买数量缺少完整原文期间或歌单成员限制。')
    return {'mode': 'physical_purchase_quantity_with_playlist_semijoin',
            'membership_methods': membership_methods, 'aggregate_null_policy': 'empty_sum_null',
            'actual_playlist_identity': playlist_identity}


def _null_case_proof_tree(tree, *, program_display=None):
    """Canonicalize only proved NULL CASE SUM to FILTER for the existing proof.

    Never change executed SQL or raw results. For SUM, a single searched CASE
    with absent/NULL ELSE includes exactly the same non-NULL inputs as FILTER;
    ELSE0 has different empty-numerator behavior and is never rewritten here.
    """
    transformed, records = tree.copy(), []
    instruction = ('按文档空 SUM 保留 NULL：请用独立 WHERE 过滤明细的 SUM 分子，或 '
        'SUM(CASE WHEN 格式条件 THEN 明细单价*购买数量 END)/FILTER；不能用 ELSE 0 或 COALESCE '
        '冒充空集 NULL。保留原期间和金额单位，分母仍按原问为同期全部曲目明细 '
        'SUM(invoice_line.unit_price * invoice_line.quantity)，不受分子格式限制；'
        '零分母用 NULLIF' +
        ('。本次已单独核对S1工具最终百分数两位显示策略，请仅保留最终最外层ROUND(...,2)，不要提前舍入分子或分母。'
         if program_display else '，未明确百分比位数时不要加 ROUND。'))
    for aggregate in list(transformed.find_all(exp.Sum)):
        value = aggregate.this
        while isinstance(value, exp.Paren):
            value = value.this
        if not isinstance(value, exp.Case):
            continue
        branches = value.args.get('ifs') or []
        if (value.this is not None or len(branches) != 1 or
                value.args.get('default') is not None and not isinstance(value.args['default'], exp.Null)):
            _deny(instruction)
        branch = branches[0]
        amount = branch.args.get('true')
        if amount is None or branch.this is None:
            _deny(instruction)
        bare = aggregate.copy()
        bare.set('this', amount.copy())
        filtered = exp.Filter(this=bare, expression=exp.Where(this=branch.this.copy()))
        records.append({'method': 'case_else_null_to_filter',
            'actual_expression': aggregate.sql(dialect='postgres'),
            'proof_expression': filtered.sql(dialect='postgres'),
            'aggregate_null_policy': 'empty_numerator_sum_stays_null',
            'raw_SQL_and_results_mutated': False})
        aggregate.replace(filtered)
    if any(isinstance(n, exp.Case) for n in transformed.walk()):
        _deny(instruction)
    return transformed, records


def validate_document_metric_lineage(sql, catalog, dependencies, *, question, identity_context=None,
                                      s1_percent_display_context=None):
    """A call-local SQL/source proof, not a persisted semantic intent/state."""
    kind = document_metric_target(question)
    if kind is None or catalog.database != 'chinook':
        _deny('未知文档指标或非 Chinook 目录不授予执行证明。')
    request = _request(question, kind)
    definition = _definition(dependencies, kind)
    if kind == '曲目销售额':
        from qa_agent.sql.ratio_scope_guard import validate_typed_ratio_scope
        # Reuse its existing physical measure, FK grain, operand, period,
        # precision/scale and NULLIF proof. This local adapter is derived only
        # from the exact original request + document, never from model state.
        contract = {'task_type': 'ratio', 'metric': 'detail_revenue', 'filters': [],
            'time_scope': {'current': request['period']}, 'query_scope': {
                'numerator': {'metric': 'detail_revenue', 'period': request['period'],
                    'filters': [{'column': request['column'], 'operator': '=', 'value': request['value']}]},
                'denominator': {'metric': 'detail_revenue', 'period': request['period'], 'filters': []}}}
        from qa_agent.sql.repair_guard import _qualified
        tree = _qualified(sql, catalog)
        if len(tree.expressions) != 1 or any(isinstance(n, exp.Coalesce) for n in tree.walk()):
            _deny('本原问只请求一个比例；不能增加隐藏零填充或其它指标。')
        from qa_agent.sql.s1_percent_display import s1_percent_display_policy
        document_text = '\n'.join(str(e.get('text') or '') for dep in dependencies.values()
            if dep.get('source') == 'documents' for e in dep.get('evidences', ()))
        display = s1_percent_display_policy(sql, question, s1_percent_display_context,
            evidence_text=document_text)
        actual_display_expression = tree.expressions[0].sql(dialect='postgres') if display else None
        proof_tree, normalizations = _null_case_proof_tree(tree, program_display=display)
        if display:
            # Separate lossy display quantization from mathematical/physical
            # operand proof; never rewrite executed SQL or claim equivalence.
            output = proof_tree.expressions[0]
            while isinstance(output, (exp.Alias, exp.Paren)):
                output = output.this
            if not isinstance(output, exp.Round):
                _deny('S1展示证明没有对应本次最终ROUND，不能据不相符标记跳过SQL校验。')
            proof_display_expression = output.sql(dialect='postgres')
            output.replace(output.this.copy())
        physical = validate_typed_ratio_scope(proof_tree.sql(dialect='postgres'), catalog, contract)
        if physical.get('mode') in {'no_complete_typed_ratio_contract', 'not_a_typed_ratio', 'invoice_only_ratio_delegated'} or not physical.get('verified'):
            _deny('未建立真实明细比例消费证明。')
        if normalizations:
            physical['equivalent_null_case_normalizations'] = normalizations
        if display:
            physical['program_display_quantization'] = {**display,
                'actual_display_expression': actual_display_expression,
                'proof_copy_display_expression': proof_display_expression,
                'mathematical_proof_expression': proof_tree.expressions[0].sql(dialect='postgres'),
                'physical_operand_scope_NULL_and_period_checks_preserved': True,
                'executed_SQL_and_raw_results_mutated': False,
                'meaning': 'S1 tool display quantization is checked separately; not user precision authority or lossless mathematical equivalence.'}
    else:
        from qa_agent.sql.helper_identity import resolved_playlist_identity
        identity = resolved_playlist_identity(dependencies, catalog, identity_context)
        physical = _quantity(sql, catalog, request, identity)
    return {'verified': True, 'proofs': [{**definition, 'source_request': request,
        'physical_consumption': physical, 'authority': 'actual_document_and_original_request_SQL_proof_not_semantic_state'}],
        'not_verified': []}
