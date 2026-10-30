"""Bounded, source-backed S1 advice/checks for two customer-period roles.

This is not a semantic state builder or a default policy.  A literal user rule
must define a customer SUM threshold and explicitly say that changing period
changes that qualification period.  Only then can a literal current question
(or an explicit continuation of a real user turn) supply the two date roles.
Unknown sources and SQL shapes are left unverified; nothing rewrites SQL.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import re

from sqlglot import exp
from sqlglot.optimizer.scope import Scope, build_scope, walk_in_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.validator import SQLValidationError


_YEAR = r"(?<!\d)([12]\d{3})\s*年(?!代)"
_NON_ASSERTION = re.compile(r"例如|比如|示例|假设|假如|不要|不用|无需|无须|不必|不需要|不是|并非|不按|取消|[\"“”「」『』]")
_DEFINITION = re.compile(
    r"(?P<term>[\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9]{0,10}客户)[，,:：]\s*"
    r"(?P<period>主(?:复盘)?期(?:间)?|指定期间|当前期间)内"
    r"(?:发票金额合计|开票总额|发票总额|开票金额合计)\s*"
    r"(?:不低于|至少为|达到|>=|≥)\s*(?P<threshold>\d+(?:\.\d+)?)\s*(?:的)?客户")


def _ref(source_id, text, start, end):
    return {"source_id": source_id, "quote": text[start:end], "start": start,
            "end": end, "source_sha256": sha256(text.encode("utf-8")).hexdigest()}


def _year(text):
    matches = list(re.finditer(_YEAR, text))
    if (len(matches) != 1 or len(re.findall(r"(?<!\d)[12]\d{3}(?!\d)", text)) != 1
            or _NON_ASSERTION.search(text)
            or re.search(r"月|季度|半年|同比|环比|前年|去年|最近|至今|或|还是|截至|截止|不止", text)):
        return None
    m = matches[0]
    if re.match(r"\s*(?:之前|以前|之后|以后|以来|前|后|起|底|初|末)", text[m.end():]):
        return None
    return int(m[1]), m


def _rules(source_text):
    result = []
    for definition in _DEFINITION.finditer(source_text):
        term = definition["term"]
        # This is an explicit user-written conditional rule, not an inferred
        # default. Keep its exact wording and offset independent of the date.
        policy = re.search(
            r"如果我换了期间问[‘'“\"]?" + re.escape(term)
            + r"[’'”\"]?[，,]\s*门槛不变[，,]\s*只是把统计的期间换成我说的那个", source_text)
        if not policy:
            continue
        sentence_start = max(source_text.rfind("。", 0, definition.start()),
                             source_text.rfind("\n", 0, definition.start())) + 1
        if re.search(r"例如|比如|示例|假设|不要|不是|并非|不采用", source_text[sentence_start:definition.start()]):
            continue
        policy_start = max(source_text.rfind("。", 0, policy.start()),
                           source_text.rfind("\n", 0, policy.start())) + 1
        if re.search(r"例如|比如|示例|假设|不要|不是|并非|不采用", source_text[policy_start:policy.start()]):
            continue
        result.append((definition, policy))
    return result


def _users(user_history):
    if not isinstance(user_history, (tuple, list)):
        return []
    return [(f"user_history_{n + 1}", item if isinstance(item, str) else item.get("user", ""))
            for n, item in enumerate(user_history) if isinstance(item, str)
            or isinstance(item, dict) and item.get("role") in (None, "user")]


def _roles(text, term):
    # An explicitly different qualification year stays independent from the
    # measure year. The finite syntax is intentionally not a date NLP parser.
    separate = re.fullmatch(
        r"\s*(?:按|以)\s*(?P<qualification>[12]\d{3})\s*年(?:的|算出的|确定的)?"
        + re.escape(term) + r"(?:名单|资格)?[，,：:\s]*(?:统计|计算|查看|看)\s*"
        r"(?P<measure>[12]\d{3})\s*年(?:的)?(?:发票金额|开票金额|销售额|发票总额)"
        r"(?:合计|总额)?(?:是多少|多少|各是多少)?[。！？?]?\s*", text)
    if separate:
        return int(separate["qualification"]), int(separate["measure"]), separate
    parsed = _year(text)
    if parsed and term in text and not re.search(r"资格期|主复盘期|主期间|按主|名单.{0,4}不变|资格.{0,4}不变", text):
        return parsed[0], parsed[0], parsed[1]
    return None


def _population_advice(current, role_text, role_id, brief, term, history):
    """One closed two-tier invoice question and literal user owner rules.

    This does not infer an owner merely from a customer name, a result value,
    or an absent binding. The source-defined market is a measurement range;
    the separately closed customer-SUM definition contains no market filter.
    """
    if re.search(r"客户所在地|客户国家|客户档案|customer\.|billing_country|认定|资格.{0,8}(?:只|仅)|门槛.{0,8}(?:只|仅)", current):
        return None
    # A different persistent user qualification restriction must not be lost.
    for _, user in _users(history):
        if isinstance(user, str):
            if re.search(r"客户所在地|客户国家|客户档案|customer\.", user):
                return None  # lifecycle of an earlier owner override is not inferred here
            if term in user and re.search(
                    r"(?:以后|接下来|从现在|资格|门槛).{0,20}(?:只|仅|限定).{0,12}(?:国家|地区|市场)", user):
                return None
    customer_rule = re.search(r"凡是主语是客户的问题[^。\n]{0,150}地区一律按客户所在地来算", brief)
    invoice_rule = re.search(r"凡是主语是发票的问题[^。\n]{0,150}地区按发票上的账单地址国家来算", brief)
    if not customer_rule or not invoice_rule:
        return None
    for match in (customer_rule, invoice_rule):
        start = max(brief.rfind("。", 0, match.start()), brief.rfind("\n", 0, match.start())) + 1
        if re.search(r"不要|不是|不采用|示例|例如|假设", brief[start:match.start()]):
            return None
    regions = list(re.finditer(
        r"(?P<values>[A-Za-z][A-Za-z ]{0,40}(?:[、,，]\s*[A-Za-z][A-Za-z ]{0,40}){1,20})"
        r"\s*(?P<count>[一二三四五六七八九十\d]+)\s*个国家算(?P<name>[\u4e00-\u9fff]{2,10}市场)", brief))
    regions = [m for m in regions if m['name'] in role_text]
    if len(regions) != 1:
        return None
    region = regions[0]
    region_start = max(brief.rfind('。', 0, region.start()), brief.rfind('\n', 0, region.start())) + 1
    tail = re.split(r'[。\n]', brief[region.end():], maxsplit=1)[0]
    if re.search(r'不要|不用|无需|不采用|不是|示例|例如|举例|假设|[“”\"‘’「」『』]', brief[region_start:region.start()]) or re.search(r'不采用|不生效|示例|举例|未确认|待确认|假设', tail):
        return None
    values = [v.strip() for v in re.split(r"[、,，]", region['values'])]
    count = int(region['count']) if region['count'].isdigit() else {'一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}.get(region['count'])
    if count != len(values) or len(values) != len(set(values)) or any(not re.fullmatch(r"[A-Za-z]+(?: [A-Za-z]+)*", v) for v in values):
        return None
    # Full finite source coverage prevents a trailing qualification exception
    # or an extra owner/region choice from inheriting this source proof.
    name = re.escape(region['name']); customer = re.escape(term)
    pattern = (r"\s*(?:(?:接着|继续|沿用)\s*)?(?:刚才的?)?\s*[12]\d{3}\s*年\s*" + name
        + r"[，,]?\s*按(?:咱们|我们)?的?\s*" + customer + r"门槛分成\s*" + customer
        + r"(?:和|与)其他客户(?:两档|两组)[，,]?\s*(?:各自|分别)(?:开了多少钱|发票金额是多少)[？?。]?\s*")
    if not re.fullmatch(pattern, role_text):
        return None
    # Explicit extra qualification geography elsewhere in the user body is
    # outside this closed definition, even if the first definition looks simple.
    if re.search(customer + r"[^。\n]{0,25}(?:只|仅|限定)[^。\n]{0,20}(?:地区|国家|市场)", brief):
        return None
    if re.search(r"资格[^。\n]{0,25}(?:地区|国家|市场)|(?:地区|国家|市场)[^。\n]{0,25}资格", brief):
        return None
    return {"qualification_population": "all_customer_invoices_in_the_source_qualification_period",
            "qualification_country_filter_authorized": False,
            "measurement_region": {"field_identity": "public.invoice.billing_country",
                                   "operator": "IN", "values": values, "source_name": region['name']},
            "source_refs": [_ref('brief', brief, customer_rule.start(), customer_rule.end()),
                            _ref('brief', brief, invoice_rule.start(), invoice_rule.end()),
                            _ref('brief', brief, region.start(), region.end()),
                            _ref(role_id, role_text, 0, len(role_text))],
            "authority": "closed_literal_user_definition_and_two_distinct_source_roles",
            "business_semantics_verified": False, "state_committed": False}


def _quarter_text(text):
    """One literal natural quarter; never a season/default or endpoint guess."""
    calendar = list(re.finditer(
        r'(?P<year>[12]\d{3})\s*年\s*(?:第(?P<quarter>[一二三四1-4])季度|'
        r'(?P<start>1[0-2]|[1-9])\s*月(?:到|至)(?P<end>1[0-2]|[1-9])\s*月底)', text))
    if len(calendar) != 1 or len(re.findall(r'(?<!\d)[12]\d{3}(?!\d)', text)) != 1:
        return None
    match = calendar[0]; year = int(match['year'])
    if match['quarter']:
        q = {'一': 1, '二': 2, '三': 3, '四': 4}.get(match['quarter'])
        month = ((q or int(match['quarter'])) - 1) * 3 + 1
    else:
        month = int(match['start'])
        if month not in (1, 4, 7, 10) or int(match['end']) != month + 2:
            return None
    end_year, end_month = (year + 1, 1) if month == 10 else (year, month + 3)
    return {'start': f'{year}-{month:02}-01', 'end': f'{end_year}-{end_month:02}-01'}, match


def _quarter_role_source(question, term, user_history):
    """Close a literal quarter qualification list and its immediate batch followup.

    This links date roles only. It does not select a genre/entity or certify any
    other predicate, ranking rule, metric, default or state.
    """
    def normalized(text, match=None):
        if match:
            text = text[:match.start()] + 'QPERIOD' + text[match.end():]
        return re.sub(r'[\s，,。；;：:？！?!（）()、]', '', text)

    def qualification(text):
        quarter = _quarter_text(text)
        if quarter is None or _NON_ASSERTION.search(text):
            return None
        period, span = quarter
        pattern = (r'(?:(?:接着|继续)刚才(?:那个|的)?(?:旺季|期间))?QPERIOD'
            r'(?:这三个月里)?给(?:咱们|我们)?开过发票的客户按(?:旺季期间|这段期间|该期间)的?'
            r'合计金额看(?:够得上|达到|符合)(?:咱们|我们)?的?' + re.escape(term)
            + r'门槛的?(?:都有谁|有谁)(?:把客户(?:全名|姓名)和合计金额列出来按合计从高到低排)?')
        return (period, span) if re.fullmatch(pattern, normalized(text, span)) else None

    direct = qualification(question)
    if direct:
        return {'period': direct[0], 'role': 'direct_quarter_qualification_list',
                'refs': [_ref('current', question, direct[1].start(), direct[1].end()),
                         _ref('current', question, 0, len(question))]}
    history = [(sid, text) for sid, text in _users(user_history)
               if isinstance(text, str) and text.strip() and text != question]
    if not history:
        return None
    sid, previous = history[-1]
    prior = qualification(previous)
    if prior is None:
        return None
    current_quarter = _quarter_text(question)
    if current_quarter is None and re.search(r'[12]\d{3}|第.{0,2}季度|\d\s*月', question):
        return None
    if current_quarter is not None and current_quarter[0] != prior[0]:
        return None  # a new independent operand period is outside this shortcut
    pattern = (r'(?:(?:接着|继续)刚才(?:那个|的)?(?:旺季|期间))?(?:QPERIOD)?那批'
        r'(?:够得上|达到|符合)(?:咱们|我们)?的?' + re.escape(term)
        + r'门槛的(?:人|客户)这三个月里买了多少(?:件|首)(?P<genre>[\w&/\-·]{1,80})'
        r'流派的曲目花了多少钱')
    matched = re.fullmatch(pattern, normalized(question, current_quarter[1] if current_quarter else None))
    if not matched or re.search(r'只|仅|排除|不含|除了|国家|地区|超过|资格|而且', matched['genre']):
        return None
    return {'period': prior[0], 'role': 'immediate_literal_quarter_batch_continuation',
            'refs': [_ref(sid, previous, 0, len(previous)),
                     _ref('current', question, 0, len(question))]}


def build_s1_source_scope_hint(source_question, *, source_text="", user_history=(),
                               enabled=False, catalog=None):
    """Return source-scoped advice only, or None when a role is unproved.

    The caller owns the real S1-on/gate-off switch. Inputs must be the current
    original user text, complete original brief and real user-only history.
    Planner prose, model references and previous SQL are never accepted.
    """
    if (enabled is not True or not isinstance(source_question, str)
            or not isinstance(source_text, str) or not source_text
            or _NON_ASSERTION.search(source_question)
            or not re.search(r"多少钱|金额|销售额|开了多少", source_question)):
        return None
    try:
        invoice = catalog.get_table("invoice", "public")
        customer = catalog.get_table("customer", "public")
        if (catalog.database != "chinook" or not {"invoice_id", "customer_id", "invoice_date", "total"} <= invoice.column_names
                or customer.primary_key != ("customer_id",)):
            return None
    except Exception:
        return None
    candidates = [(d, p) for d, p in _rules(source_text) if d["term"] in source_question]
    if len(candidates) != 1:
        return None
    definition, policy = candidates[0]
    term = definition["term"]
    quarter = _quarter_role_source(source_question, term, user_history)
    if quarter:
        return {'kind': 'source_customer_qualification_periods', 'customer_term': term,
                'qualification_predicate': {'metric_identity': 'public.invoice.total SUM per customer',
                    'operator': '>=', 'threshold': definition['threshold']},
                'periods': {'qualification': dict(quarter['period']), 'measure': dict(quarter['period'])},
                'source_refs': [_ref('brief', source_text, definition.start(), definition.end()),
                    _ref('brief', source_text, policy.start(), policy.end()), *quarter['refs']],
                'source_period_role_mode': quarter['role'],
                'advice': '真实当轮已在明确季度按客户金额门槛建立名单；紧邻续问的那批保留同一季度资格，再独立限定实际测量季度。不得退回主自然年资格；其他实体、数量、金额及筛选仍须按原问保留，本提示不认证它们。',
                'semantic_verified': False, 'state_committed': False, 'default_authorized': False,
                'business_semantics_verified': False, 'other_source_predicates_verified': False}
    role_text, role_id = source_question, "current"
    roles = _roles(role_text, term)
    if roles is None:
        if re.search(r"[12]\d{3}|今年|去年|前年|月|季度|半年|资格期|主期间|主复盘期", source_question):
            return None  # an unresolved current date/role must not be replaced by history
        if not re.search(r"刚才|上一轮|接着|沿用|那两档|这两档", source_question):
            return None
        # Only the immediately preceding real user turn may establish this
        # continuation. Skip a store's duplicate current turn, never assistant.
        history = [(sid, text) for sid, text in _users(user_history)
                   if isinstance(text, str) and text.strip() and text != source_question]
        if not history:
            return None
        role_id, role_text = history[-1]
        if _NON_ASSERTION.search(role_text):
            return None
        roles = _roles(role_text, term)
    if roles is None:
        return None
    qyear, myear, match = roles
    periods = {role: {"start": f"{year}-01-01", "end": f"{year + 1}-01-01"}
               for role, year in (("qualification", qyear), ("measure", myear))}
    result = {"kind": "source_customer_qualification_periods", "customer_term": term,
            "qualification_predicate": {"metric_identity": "public.invoice.total SUM per customer",
                                        "operator": ">=", "threshold": definition["threshold"]},
            "periods": periods,
            "source_refs": [_ref("brief", source_text, definition.start(), definition.end()),
                            _ref("brief", source_text, policy.start(), policy.end()),
                            _ref(role_id, role_text, match.start(), match.end()),
                            _ref("current", source_question, 0, len(source_question))],
            "advice": "分别保持客户资格计算期间和金额测量期间；明确两期不同不能互相覆盖。这里只链接逐字用户定义，不批准默认、筛选范围或执行。",
            "semantic_verified": False, "state_committed": False,
            "default_authorized": False, "business_semantics_verified": False}
    population = (_population_advice(source_question, role_text, role_id, source_text, term, user_history)
                  if 'billing_country' in invoice.column_names and 'country' in customer.column_names else None)
    if population:
        result['source_population_roles'] = population
        result['advice'] += '资格集合按独立客户金额定义计算，不把测量市场先筛进资格；发票金额的地区按原文账单国家，不能以客户所在地替代。'
    if (re.fullmatch(r"\s*刚才那两档[，,]\s*金额差是多少[？?]\s*就用" + re.escape(term)
                     + r"那档减其他客户那档[。]?\s*", source_question)):
        result['output_roles_advisory'] = {
            'requested_metric': 'difference_of_the_two_existing_tiers',
            'advice': '本轮新增所问指标为两档差额，保留原文减法方向；不要无依据把它扩成新的分组任务。正文若另有明确额外列交付要求仍须保留。',
            'source_ref': _ref('current', source_question, 0, len(source_question)),
            'enforced_projection_width': None, 'business_semantics_verified': False}
    return result


def _un(node):
    while isinstance(node, (exp.Alias, exp.Paren)):
        node = node.this
    return node


def _atoms(node):
    node = _un(node)
    if isinstance(node, exp.And):
        return _atoms(node.left) + _atoms(node.right)
    return [node] if node is not None else []


def _date(node):
    node = _un(node)
    if isinstance(node, exp.Cast):
        if str(node.args.get("to")).upper() not in {"DATE", "TIMESTAMP", "TIMESTAMPNTZ"}:
            return None
        node = _un(node.this)
    if not isinstance(node, exp.Literal) or not node.is_string:
        return None
    try:
        dt = datetime.fromisoformat(node.this)
        if dt.tzinfo or (dt.hour, dt.minute, dt.second, dt.microsecond) != (0, 0, 0, 0):
            return None
        return dt.date().isoformat()
    except ValueError:
        return None


def _period(scope, alias):
    where = scope.expression.args.get("where")
    if where is None:
        return None
    atoms = _atoms(where.this)
    start, end = [], []
    for atom in atoms:
        if isinstance(atom, exp.Or):
            return None
        columns = [c for c in atom.find_all(exp.Column) if c.table == alias and c.name == "invoice_date"]
        if not columns:
            continue
        if not isinstance(atom, (exp.GTE, exp.LT, exp.GT, exp.LTE)):
            return None
        left, right = _un(atom.left), _un(atom.right)
        if isinstance(left, exp.Column) and left.table == alias and left.name == "invoice_date":
            value, op = _date(right), type(atom)
        elif isinstance(right, exp.Column) and right.table == alias and right.name == "invoice_date":
            value, op = _date(left), {exp.GTE: exp.LTE, exp.LT: exp.GT, exp.GT: exp.LT, exp.LTE: exp.GTE}[type(atom)]
        else:
            return None
        if value is None:
            return None
        if op is exp.GTE:
            start.append(value)
        elif op is exp.LT:
            end.append(value)
        else:
            return None
    if len(start) == len(end) == 1:
        return {"start": start[0], "end": end[0]}
    return None


def _physical(scope):
    return {alias: source for alias, (_, source) in scope.selected_sources.items()
            if isinstance(source, exp.Table)}


def _invoice(scope):
    found = [(a, t) for a, t in _physical(scope).items()
             if (t.db or "public") == "public" and t.name == "invoice"]
    return found[0][0] if len(found) == 1 else None


def _sum_total(node, alias):
    node = _un(node)
    return (isinstance(node, exp.Sum) and isinstance(_un(node.this), exp.Column)
            and _un(node.this).table == alias and _un(node.this).name == "total")


def _amount_origins(column, scope, depth=0):
    """Resolve only an untransformed invoice-total column across live CTEs.

    This identifies the date-bearing physical stream, not its multiplicity or
    any complete population proof. An aggregate/limited intermediary is opaque.
    """
    if depth > 4 or not isinstance(column, exp.Column):
        return None
    selected = scope.selected_sources.get(column.table)
    if selected is None:
        return None
    source = selected[1]
    if isinstance(source, exp.Table):
        if (source.db or "public") == "public" and source.name == "invoice" and column.name == "total":
            return [(scope, column.table)]
        return None
    if not isinstance(source, Scope):
        return None
    projections = [p for p in source.expression.selects if p.alias_or_name == column.name]
    if len(projections) != 1:
        return None
    return _projection_origins(source, source.expression.selects.index(projections[0]), depth + 1)


def _projection_origins(scope, index, depth):
    """Follow only transparent SELECT or positional UNION ALL projections.

    UNION column names come from its first branch. A right-branch alias is
    therefore not an identity proof; the actual output position must resolve
    to an untransformed invoice.total in every consumed branch.
    """
    if depth > 4 or any(scope.expression.args.get(k) for k in ("group", "having", "limit", "offset", "distinct")):
        return None
    if isinstance(scope.expression, exp.Union):
        if scope.expression.args.get('distinct') is not False or len(scope.set_operation_scopes) != 2:
            return None
        origins = []
        width = len(scope.expression.selects)
        for branch in scope.set_operation_scopes:
            if len(branch.expression.selects) != width:
                return None
            found = _projection_origins(branch, index, depth + 1)
            if not found:
                return None
            origins.extend(found)
        return origins
    if not isinstance(scope.expression, exp.Select) or index >= len(scope.expression.selects):
        return None
    return _amount_origins(_un(scope.expression.selects[index]), scope, depth)


def _qualification(scope, alias, threshold, catalog):
    select = scope.expression
    if (not isinstance(select, exp.Select) or any(select.args.get(k) for k in ("limit", "offset", "distinct"))
            or select.args.get("having") is None or select.args.get("group") is None):
        return False
    having = _un(select.args["having"].this)
    if not isinstance(having, exp.GTE) or not _sum_total(having.left, alias):
        return False
    value = _un(having.right)
    if not isinstance(value, exp.Literal) or value.is_string:
        return False
    try:
        if Decimal(value.this) != Decimal(threshold):
            return False
    except InvalidOperation:
        return False
    group = select.args["group"].expressions
    if len(group) != 1 or not isinstance(_un(group[0]), exp.Column):
        return False
    physical = _physical(scope)
    grouped = _un(group[0])
    if len(physical) == 1:
        return grouped.table == alias and grouped.name == "customer_id"
    # The only supported extra table is the real customer FK parent; never a
    # detail fanout or an alias which happens to be called customer.
    if len(physical) != 2:
        return False
    parents = [a for a, t in physical.items() if a != alias
               and (t.db or "public") == "public" and t.name == "customer"]
    if len(parents) != 1 or (grouped.table, grouped.name) not in {(alias, "customer_id"), (parents[0], "customer_id")}:
        return False
    invoice = catalog.get_table("invoice", "public")
    fk = any(f.get("columns") == ["customer_id"] and (f.get("references") or {}).get("table") == "customer"
             and (f.get("references") or {}).get("schema", invoice.schema) == "public"
             and (f.get("references") or {}).get("columns") == ["customer_id"]
             for f in invoice.foreign_keys)
    joins = select.args.get("joins") or []
    if not fk or len(joins) != 1 or joins[0].args.get("side") or joins[0].args.get("kind") not in (None, "", "INNER"):
        return False
    on = _un(joins[0].args.get("on"))
    return (isinstance(on, exp.EQ) and all(isinstance(_un(c), exp.Column) for c in (on.left, on.right))
            and {(on.left.table, on.left.name), (on.right.table, on.right.name)}
            == {(alias, "customer_id"), (parents[0], "customer_id")})


def _country_filters(scope):
    """Read finite positive physical country predicates; never resolve aliases by name."""
    where = scope.expression.args.get('where')
    result = []
    for atom in _atoms(where.this if where else None):
        country_columns = [c for c in atom.find_all(exp.Column) if c.name in {'country', 'billing_country'}]
        if not country_columns:
            continue
        if len(country_columns) != 1 or len(list(atom.find_all(exp.Column))) != 1:
            return None
        column = country_columns[0]
        selected = scope.selected_sources.get(column.table)
        if not selected or not isinstance(selected[1], exp.Table):
            return None
        table = selected[1]
        identity = f'{table.db or "public"}.{table.name}.{column.name}'
        if identity not in {'public.invoice.billing_country', 'public.customer.country'}:
            return None
        if isinstance(atom, exp.In) and atom.this is column and not atom.args.get('query'):
            values = atom.expressions
        elif isinstance(atom, exp.EQ) and (atom.left is column or atom.right is column):
            values = [atom.right if atom.left is column else atom.left]
        else:
            return None
        if not values or any(not isinstance(v, exp.Literal) or not v.is_string for v in values):
            return None
        result.append({'field_identity': identity, 'values': [v.this for v in values],
                       'actual_predicate': atom.sql(dialect='postgres')})
    return result


def _population_conflicts(hint, qualification_streams, measure_streams):
    source = hint.get('source_population_roles')
    if source is None:
        return [], {'status': 'not_verified', 'reason': 'no_closed_source_population_roles'}
    expected = source['measurement_region']
    conflicts, observed = [], []
    for scope, _ in qualification_streams:
        filters = _country_filters(scope)
        if filters is None:
            return [], {'status': 'not_verified', 'reason': 'unknown_qualification_country_predicate'}
        for predicate in filters:
            conflicts.append({'role': 'qualification_population', 'actual_country_filter': predicate,
                              'source_rule': 'customer_SUM_threshold_has_no_market_filter'})
    for scope, _ in measure_streams:
        filters = _country_filters(scope)
        if filters is None:
            return conflicts, {'status': 'not_verified', 'reason': 'unknown_measure_country_predicate'}
        matches = [p for p in filters if set(p['values']) == set(expected['values'])]
        if len(matches) != 1:
            return conflicts, {'status': 'not_verified', 'reason': 'market_membership_not_uniquely_located'}
        observed.append(matches[0])
        if matches[0]['field_identity'] != expected['field_identity']:
            conflicts.append({'role': 'measurement_region_owner', 'actual_country_filter': matches[0],
                              'source_field_identity': expected['field_identity']})
    return conflicts, {'status': 'checked_country_roles_only', 'measurement_predicates': observed,
                       'business_semantics_verified': False, 'all_other_qualification_filters_verified': False}


def _direct_detail_period_stream(total, scope, catalog):
    """Date-bearing invoice for a consumed, physical line amount/count only.

    No genre, population, aggregation or complete business proof is granted.
    The caller limits this extension to final projections of the literal
    quarter-batch source family; derived/other expressions remain unknown.
    """
    if not any(total in list(p.walk()) for p in scope.expression.selects):
        return None
    physical = _physical(scope)
    invoices = [a for a, t in physical.items() if (t.db or 'public') == 'public' and t.name == 'invoice']
    lines = [a for a, t in physical.items() if (t.db or 'public') == 'public' and t.name == 'invoice_line']
    if len(invoices) != 1 or len(lines) != 1:
        return None
    invoice, line = invoices[0], lines[0]
    value = _un(total.this)
    quantity = isinstance(value, exp.Column) and (value.table, value.name) == (line, 'quantity')
    product = (isinstance(value, exp.Mul)
        and all(isinstance(_un(c), exp.Column) for c in (value.left, value.right))
        and {_un(value.left).table, _un(value.right).table} == {line}
        and {_un(value.left).name, _un(value.right).name} == {'unit_price', 'quantity'})
    if not quantity and not product:
        return None
    parent = catalog.get_table('invoice', 'public')
    child = catalog.get_table('invoice_line', 'public')
    if parent.primary_key != ('invoice_id',) or not any(
        f.get('columns') == ['invoice_id'] and (f.get('references') or {}).get('table') == 'invoice'
        and (f.get('references') or {}).get('schema', child.schema) == 'public'
        and (f.get('references') or {}).get('columns') == ['invoice_id'] for f in child.foreign_keys):
        return None
    required = {(invoice, 'invoice_id'), (line, 'invoice_id')}
    for join in scope.expression.args.get('joins') or []:
        if join.side or join.kind not in ('', 'INNER'):
            continue
        for atom in _atoms(join.args.get('on')):
            if (isinstance(atom, exp.EQ) and isinstance(atom.left, exp.Column)
                    and isinstance(atom.right, exp.Column)
                    and {(atom.left.table, atom.left.name), (atom.right.table, atom.right.name)} == required):
                return scope, invoice
    return None


def validate_s1_source_scope(sql, catalog, source_question, *, source_text="",
                             user_history=(), enabled=False):
    """Check only provable consumed qualification/measurement date literals.

    A passing result is a local source/SQL consistency check, not a complete
    business proof. A source-proved contradiction uses ordinary SQL repair.
    """
    def no(reason):
        return {"verified": False, "status": "not_verified", "reason": reason,
                "business_semantics_verified": False, "state_committed": False}
    hint = build_s1_source_scope_hint(source_question, source_text=source_text,
                                     user_history=user_history, enabled=enabled, catalog=catalog)
    if hint is None:
        return no("No complete literal user qualification/date-role source")
    try:
        tree = _qualified(sql, catalog)
        root = build_scope(tree)
        if root is None:
            return no("No supported SQL scope")
        consumed, seen = [], set()
        def visit(scope):
            if id(scope) in seen:
                return
            seen.add(id(scope)); consumed.append(scope)
            for _, source in scope.selected_sources.values():
                if isinstance(source, Scope):
                    visit(source)
            for child in scope.subquery_scopes:
                visit(child)
            # Live set-operation branches are not selected_sources in SQLGlot.
            # Do not visit cte_scopes: an unused CTE supplies no active role.
            for child in scope.set_operation_scopes:
                visit(child)
        visit(root)
        qualifications, measures = [], []
        qualification_streams, measure_streams = [], []
        for scope in consumed:
            alias = _invoice(scope)
            if not alias:
                continue
            period = _period(scope, alias)
            if _qualification(scope, alias, hint["qualification_predicate"]["threshold"], catalog):
                qualification_streams.append((scope, alias))
                if period is not None:
                    qualifications.append(period)
        measurement_unknown = False
        for scope in consumed:
            for total in (n for n in walk_in_scope(scope.expression) if isinstance(n, exp.Sum)):
                if hint.get('source_period_role_mode') and scope is root:
                    detail = _direct_detail_period_stream(total, scope, catalog)
                    if detail:
                        stream, alias = detail
                        period = _period(stream, alias)
                        if period is None:
                            measurement_unknown = True
                        elif period not in measures:
                            measures.append(period)
                        if not any(s is stream and a == alias for s, a in measure_streams):
                            measure_streams.append((stream, alias))
                        continue
                # Preserve the existing bounded CASE stream check. Arithmetic
                # inside SUM is not a transparent invoice-total projection.
                if not isinstance(_un(total.this), (exp.Column, exp.Case)):
                    measurement_unknown = True
                    continue
                found_origin = False
                for column in total.find_all(exp.Column):
                    origins = _amount_origins(column, scope)
                    if origins is None:
                        continue
                    found_origin = True
                    for stream, alias in origins:
                        if (_qualification(stream, alias, hint["qualification_predicate"]["threshold"], catalog)
                                and not (stream is root and hint.get('source_period_role_mode')
                                         == 'direct_quarter_qualification_list')):
                            continue
                        period = _period(stream, alias)
                        if period is None:
                            measurement_unknown = True
                        elif period not in measures:
                            measures.append(period)
                        if not any(s is stream and a == alias for s, a in measure_streams):
                            measure_streams.append((stream, alias))
                if not found_origin:
                    measurement_unknown = True
        if len(qualification_streams) != 1 or len(qualifications) != 1:
            return no("No unique consumed customer SUM qualification with a proved half-open interval")
        conflicts = []
        for role, periods in (("qualification", qualifications), ("measure", measures)):
            if any(p != hint["periods"][role] for p in periods):
                conflicts.append({"role": role, "actual_periods": periods, "source_period": hint["periods"][role]})
        population_conflicts, population_check = _population_conflicts(hint, qualification_streams, measure_streams)
        conflicts.extend(population_conflicts)
        evidence = {"mode": "S1_literal_customer_qualification_periods", "source_hint": hint,
                    "checked_qualification_periods": qualifications, "checked_measure_periods": measures,
                    "measurement_lineage_status": ("not_verified" if measurement_unknown or not measures
                                                   else "checked_period_streams_only"),
                    "population_roles_check": population_check,
                    "conflicts": conflicts, "sql_sha256": sha256(sql.encode()).hexdigest(),
                    "business_semantics_verified": False, "state_committed": False}
        if conflicts:
            message = "本轮客户资格期间与金额统计期间必须分别按真实用户来源保留，不能把主复盘年份套入已明确切换的资格名单。"
            if population_conflicts:
                message += ("原文的客户金额门槛是独立资格定义，不把测量用的市场国家条件提前加进资格集合；"
                            "发票开了多少钱按原文账单国家范围计算，不能用客户所在地替代。保留原门槛、两段期间、市场名单和NULL。")
            error = SQLValidationError(message + str(conflicts))
            error.source_scope_evidence = evidence
            raise error
        # A known contradiction above cannot be hidden by an unrelated unknown
        # measurement shape. Without a contradiction, unknown stays unverified.
        if measurement_unknown or not measures:
            return {**no("Measurement SQL lineage/date syntax outside the finite transparent stream check"),
                    **evidence}
        return {"verified": True, "status": "checked", **evidence}
    except SQLValidationError:
        raise
    except Exception:
        return no("SQL lineage/date syntax outside this finite source consistency check")
