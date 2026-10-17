"""Prove complementary invoice-market sums and their actual difference.

The set belongs to the comparison operands, not a global WHERE. Uses current
typed contract, actual SQL lineage, catalog cardinality and standard SQL NULL
semantics; neither reference answers nor evaluation IDs enter this checker.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _physical_field, _invoice_grain_is_preserved, _midnight_date
from qa_agent.sql.validator import SQLValidationError


def validate_partition_comparison(sql, catalog, intent):
    contract = (getattr(intent, "query_scope", {}) or {}).get("comparison_partition")
    if not contract:
        return {"verified": True, "mode": "not_a_typed_partition_comparison"}
    field = contract.get("column")
    values = contract.get("values")
    if (field != "invoice.billing_country" or contract.get("metric") != "invoice_revenue" or
            contract.get("source") != "program:confirmed_comparison_partition" or
            not isinstance(contract.get("source_evidence"), str) or not contract["source_evidence"].strip() or
            not isinstance(contract.get("question_evidence"), str) or not contract["question_evidence"].strip() or
            not isinstance(values, list) or not values or any(not isinstance(value, str) for value in values) or
            len(values) != len(set(values)) or contract.get("other_operator") != "NOT IN" or
            contract.get("difference") != {"left": "focus", "right": "other"}):
        raise SQLValidationError("分组比较合同缺少可核验的名单、发票金额口径或差额方向。")
    expected = set(values)
    tree = _qualified(sql, catalog)
    scopes = list(traverse_scope(tree))
    root = next(scope for scope in scopes if scope.parent is None)
    by_expression = {id(scope.expression): scope for scope in scopes}
    domains = frozenset({"focus", "other", "unknown"})
    current = (getattr(intent, "time_scope", None) or {}).get("current") or {}
    global_filters = getattr(intent, "filters", None) or []

    def fail(message):
        raise SQLValidationError("分组比较：" + message)

    def strip(node):
        while isinstance(node, (exp.Alias, exp.Paren)):
            node = node.this
        return node

    def has_country(node, scope):
        return any(_physical_field(column, scope) == field for column in node.find_all(exp.Column))

    def authorized_global_atom(node, scope):
        if isinstance(node, (exp.GTE, exp.LT)) and _physical_field(node.left, scope) == 'invoice.invoice_date':
            return _midnight_date(node.right) == current.get('start' if isinstance(node, exp.GTE) else 'end') and bool(current)
        operators = {exp.EQ:'=', exp.NEQ:'!=', exp.GT:'>', exp.GTE:'>=', exp.LT:'<', exp.LTE:'<='}
        operator = operators.get(type(node))
        if operator and isinstance(node.right, exp.Literal):
            column = _physical_field(node.left, scope)
            for item in global_filters:
                if item.get('column') != column or str(item.get('operator')).upper() != operator:
                    continue
                if node.right.is_string:
                    if item.get('value') == node.right.this:
                        return True
                else:
                    try:
                        if Decimal(str(item.get('value'))) == Decimal(node.right.this):
                            return True
                    except InvalidOperation:
                        pass
        return False

    def mask(node, scope, *, strict=False):
        node = strip(node)
        if isinstance(node, (exp.Where, exp.Having)):
            return mask(node.this, scope, strict=strict)
        if isinstance(node, exp.And):
            return mask(node.left, scope, strict=strict) & mask(node.right, scope, strict=strict)
        if isinstance(node, exp.Or):
            if has_country(node, scope) and (not has_country(node.left, scope) or not has_country(node.right, scope)):
                fail("国家分支不能与其它行条件通过OR混用后仍宣称完整名单。")
            return mask(node.left, scope, strict=strict) | mask(node.right, scope, strict=strict)
        negated = isinstance(node, exp.Not)
        inner = strip(node.this) if negated else node
        if isinstance(inner, exp.In) and _physical_field(inner.this, scope) == field:
            literals = inner.expressions
            if inner.args.get("query") is not None or any(not isinstance(value, exp.Literal) or not value.is_string for value in literals):
                fail("名单分支必须使用合同中的实际字符串集合。")
            actual = [str(value.this) for value in literals]
            if len(actual) != len(set(actual)) or set(actual) != expected:
                fail("名单分支漏成员或加入了定义外成员。")
            return frozenset({"other" if negated else "focus"})
        if isinstance(inner, exp.Is) and isinstance(inner.expression, exp.Null) and _physical_field(inner.this, scope) == field:
            effective_not = negated != bool(inner.args.get("negate"))
            return frozenset({"focus", "other"}) if effective_not else frozenset({"unknown"})
        if isinstance(node, exp.Boolean):
            return domains if node.this else frozenset()
        if strict or has_country(node, scope):
            fail("分支条件没有证明真实IN/NOT IN集合，不能靠别名或当前碰巧相同的结果代替。")
        if not authorized_global_atom(node, scope):
            fail("额外行筛选没有当前期间或已确认全局条件的依据。")
        return domains

    def zero(node):
        node = strip(node)
        if node is None or isinstance(node, exp.Null):
            return True
        try:
            return isinstance(node, exp.Literal) and not node.is_string and Decimal(node.this) == 0
        except InvalidOperation:
            return False

    def coefficient(node, scope):
        node = strip(node)
        if zero(node):
            return 0
        if _physical_field(node, scope) == "invoice.total":
            return 1
        if isinstance(node, exp.Neg) and _physical_field(strip(node.this), scope) == "invoice.total":
            return -1
        fail("金额分支必须真实使用invoice.total或其负值/0，不得改字段、放大金额或混入明细。")

    scalar_cache = {}

    def scalar(scope, seen=None):
        seen = set() if seen is None else set(seen)
        if id(scope) in seen:
            return False
        if id(scope) in scalar_cache:
            return scalar_cache[id(scope)]
        seen.add(id(scope))
        query = scope.expression
        if not isinstance(query, exp.Select) or query.args.get("group") or query.args.get("having") or query.args.get("offset") or scope.external_columns:
            return False
        if query.args.get("limit") and str(query.args["limit"].expression) == "0":
            return False
        if _invoice_grain_is_preserved(scope, catalog):
            if query.args.get("joins"):
                return False
            # The polynomial classifier below additionally requires every
            # projected result to be made from real aggregate expressions.
            valid = all(any(isinstance(node, exp.AggFunc) and node.find_ancestor(exp.Select) is query for node in item.walk()) for item in query.selects)
        else:
            if query.args.get("where") or any(
                    join.args.get("on") is not None or join.args.get("using") or
                    str(join.args.get("side") or "").upper() in {"LEFT", "RIGHT", "FULL"}
                    for join in query.args.get("joins") or []):
                return False
            sources = [source for _, source in scope.selected_sources.values()]
            valid = all(not isinstance(source, exp.Table) and scalar(source, seen) for source in sources)
        scalar_cache[id(scope)] = valid
        return valid

    def polynomial(node, scope, depth=0):
        if depth > 24:
            fail("表达式超过有界的字段谱系深度。")
        node = strip(node)
        if isinstance(node, exp.Round):
            precision = node.args.get("decimals")
            if not isinstance(precision, exp.Literal) or precision.is_string or not str(precision.this).isdigit() or int(precision.this) < 2:
                fail("金额舍入不能损失当前发票金额的两位小数。")
            return polynomial(node.this, scope, depth + 1)
        if isinstance(node, exp.Cast):
            if node.args['to'].this==exp.DataType.Type.DECIMAL and not node.args['to'].expressions:
                return polynomial(node.this,scope,depth+1)
            fail("本比较的金额转换没有无损证明，请保留数据库原始金额类型。")
        if isinstance(node, exp.Column):
            source = scope.sources.get(node.table)
            if source is None or isinstance(source, exp.Table) or not scalar(source):
                fail("派生比较值不是已证明单行的真实聚合。")
            projection = next((item for item in source.expression.selects if item.alias_or_name == node.name), None)
            if projection is None:
                fail("比较字段没有实际投影来源。")
            return polynomial(projection, source, depth + 1)
        if isinstance(node, exp.Subquery):
            child = by_expression.get(id(node.this))
            if child is None or not scalar(child) or len(child.expression.selects) != 1:
                fail("标量子查询必须真实产生一项发票金额聚合。")
            return polynomial(child.expression.selects[0], child, depth + 1)
        if isinstance(node, (exp.Add, exp.Sub)):
            left = polynomial(node.left, scope, depth + 1)
            right = polynomial(node.right, scope, depth + 1)
            sign = -1 if isinstance(node, exp.Sub) else 1
            return tuple(a + sign * b for a, b in zip(left, right))
        if isinstance(node, exp.Neg):
            return tuple(-value for value in polynomial(node.this, scope, depth + 1))
        if isinstance(node, exp.Sum):
            if not _invoice_grain_is_preserved(scope, catalog) or scope.expression.args.get("joins"):
                fail("金额聚合的关联没有证明每张发票仅计算一次。")
            active = mask(scope.expression.args["where"], scope) if scope.expression.args.get("where") else domains
            contributions = {name: 0 for name in domains}
            term = strip(node.this)
            if isinstance(term, exp.Case):
                if term.this is not None:
                    fail("请使用明确IN/NOT IN的搜索CASE，不能猜枚举标签。")
                remaining = set(domains)
                for branch in term.args.get("ifs", []):
                    chosen = set(mask(branch.this, scope, strict=True)) & remaining
                    amount = coefficient(branch.args.get("true"), scope)
                    for name in chosen:
                        contributions[name] = amount
                    remaining -= chosen
                default = coefficient(term.args.get("default"), scope)
                for name in remaining:
                    contributions[name] = default
            else:
                amount = coefficient(term, scope)
                contributions = {name: amount for name in domains}
            return tuple(contributions[name] if name in active else 0 for name in ("focus", "other", "unknown"))
        if zero(node):
            return (0, 0, 0)
        fail("输出不能由常量、未消费聚合、任意缩放或其它口径冒充分组金额。")

    if not scalar(root):
        fail("最终比较必须由单行聚合组成，不能通过多行JOIN放大或遗漏结果。")
    # The shared physical-field resolver intentionally strips casts for other
    # uses. Here a lossy cast inside SUM/CASE changes the monetary operands.
    from qa_agent.sql.semantic_guard import _active_scopes
    for scope in _active_scopes(scopes):
        for node in scope.expression.find_all(exp.Cast):
            if node.find(exp.Column) is not None and (node.args['to'].this!=exp.DataType.Type.DECIMAL or node.args['to'].expressions or
                    _physical_field(node.this,scope)=='invoice.billing_country'):
                fail("金额或国家字段的类型转换没有无损证明。")
    if root.expression.args.get("where") and not _invoice_grain_is_preserved(root, catalog):
        fail("派生比较层不能额外过滤已算出的两组金额。")
    roles = {}
    for index, projection in enumerate(root.expression.selects):
        vector = polynomial(projection, root)
        role = {(1, 0, 0): "focus", (0, 1, 0): "other", (1, -1, 0): "difference"}.get(vector)
        if role is not None:
            roles[role] = {"column": projection.alias_or_name, "position": index}
    if set(roles) != {"focus", "other", "difference"}:
        fail("须返回完整名单金额、NOT IN非名单金额和名单减非名单的真实差额；未知国家不能静默归入其余市场。")
    if current:
        from qa_agent.clarify.sql_guard import validate_confirmed_invoice_period
        validate_confirmed_invoice_period(sql, catalog, current)
    return {"verified": True, "mode": "typed_partition_invoice_amount_lineage", "roles": roles,
            "values": values, "null_handling": "unknown_country_excluded_from_both_groups",
            "difference": "focus_minus_other", "future_unknown_country_policy": "requires_human_confirmation",
            "proof_scope": "operand_membership_invoice_measure_period_and_difference_expression",
            "empty_group_semantics": "preserve_actual_SQL_NULL_or_zero_expression; no_global_equivalence_claim"}
