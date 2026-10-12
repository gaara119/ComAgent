"""Prove an Oct12-authorized same-period share of all invoice amounts.

Only conditional country amount / unconditional invoice total is accepted.
The country applies to the numerator, never the global denominator. This is a
bounded proof, not a general SQL rewriter or a new business default provider.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
import re

from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.validator import SQLValidationError


def _unparen(node):
    while isinstance(node, (exp.Paren, exp.Alias, exp.Cast)):
        node = node.this
    return node


def _number(node, value):
    node = _unparen(node)
    try:
        return isinstance(node, exp.Literal) and not node.is_string and Decimal(node.this) == Decimal(value)
    except Exception:
        return False



def _period_literal_date(node):
    """Prove a static date or timezone-free exact midnight boundary.

    Never truncate non-midnight timestamps, strip timezone offsets, or evaluate
    dynamic expressions. Cast types remain visible during this proof.
    """
    while isinstance(node, (exp.Paren, exp.Alias, exp.Cast)):
        if isinstance(node, exp.Cast):
            kind = node.args["to"].sql(dialect="postgres").upper()
            if not re.fullmatch(r"DATE|TIMESTAMP(?:\(\d+\))?(?: WITHOUT TIME ZONE)?", kind):
                return None
        node = node.this
    if not isinstance(node, exp.Literal) or not node.is_string:
        return None
    value = str(node.this)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[ T]00:00:00(?:\.0+)?)?", value):
        return None
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return None


def validate_invoice_share(sql, catalog, bindings, context):
    if context.get("task_type") != "ratio" or not any(b.get("column") in
             {"customer.country", "invoice.billing_country"} for b in bindings):
        return False

    def deny(message):
        raise SQLValidationError("发票金额占比作用域未通过：" + message + "；不能把分子国家放入全局 WHERE 改变分母。")

    denominator = str(context.get("denominator") or "")
    metric = str(context.get("metric") or "")
    # A customer-count share cannot inherit invoice-amount defaults.
    if any(word in metric for word in ("客户数", "customer_count")):
        return False
    if not (any(word in denominator for word in ("全部", "所有", "全球", "全库", "all")) and
            any(word in denominator for word in ("发票", "invoice")) and
            any(word in denominator for word in ("金额", "销售额", "总额", "收入", "amount", "revenue"))):
        return False
    if len(bindings) != 1 or bindings[0].get("operator") != "=":
        deny("目前只证明单国家等值分子，其它筛选不能丢失")
    bound = bindings[0]
    table, column_name = bound["column"].split(".")[-2:]
    numerator_text = str(context.get("numerator") or "")
    known_surfaces = [str(bound["value"]), *(str(value) for value in context.get("verified_original_surfaces") or [])]
    if numerator_text and not any(surface and surface.casefold() in numerator_text.casefold() for surface in known_surfaces):
        deny("当前分子文字与实际已核验国家绑定不一致")
    if context.get("region_scope") not in {None, bound["column"]}:
        deny("地区归属与国家绑定冲突")
    tree = _qualified(sql, catalog)
    scopes = list(traverse_scope(tree))
    if (len(scopes) != 1 or not isinstance(tree, exp.Select) or len(tree.selects) != 1 or
            any(tree.args.get(key) for key in ("group", "having", "distinct", "qualify", "with_", "offset")) or
            any(isinstance(node, (exp.Window, exp.Subquery)) for node in tree.walk())):
        deny("需要单个 SELECT、单比例列、无额外分组/子查询")
    sources = {alias: source for alias, (_, source) in scopes[0].selected_sources.items()}
    expected_tables = ["invoice"] if table == "invoice" else ["customer", "invoice"]
    if (sorted(source.name for source in sources.values() if isinstance(source, exp.Table)) != expected_tables or
            any(not isinstance(source, exp.Table) or source.db != "public" for source in sources.values())):
        deny("真实发票及客户来源不能重复扫描或换成明细")

    def col(node, owner, name):
        node = _unparen(node)
        source = sources.get(node.table) if isinstance(node, exp.Column) else None
        return isinstance(source, exp.Table) and source.name == owner and node.name == name

    def total(node):
        node = _unparen(node)
        return isinstance(node, exp.Sum) and col(node.this, "invoice", "total")

    joins = tree.args.get("joins") or []
    if table == "customer":
        invoice = catalog.get_table("invoice")
        customer = catalog.get_table("customer")
        valid_fk = any(fk["columns"] == ["customer_id"] and fk["references"]["table"] == "customer" and
                       fk["references"]["columns"] == ["customer_id"] for fk in invoice.foreign_keys)
        nullable = next(c.nullable for c in invoice.columns if c.name == "customer_id")
        if not valid_fk or nullable or customer.primary_key != ("customer_id",):
            deny("目录不能证明每张发票恰好属于一个客户")
        if len(joins) != 1 or joins[0].args.get("side") or joins[0].args.get("kind") not in (None, "", "INNER"):
            deny("客户关联必须使用完整的内连接外键")
        on = _unparen(joins[0].args.get("on"))
        if not (isinstance(on, exp.EQ) and any(col(a, "invoice", "customer_id") and col(b, "customer", "customer_id")
                                             for a, b in ((on.left, on.right), (on.right, on.left)))):
            deny("关联只能 invoice.customer_id=customer.customer_id")
    elif joins:
        deny("账单国家占比不需要其它连接")

    current = (context.get("time_scope") or {}).get("current") or {}
    start, end = current.get("start"), current.get("end")
    where = tree.args.get("where")
    if start or end:
        try:
            if date.fromisoformat(str(start)) >= date.fromisoformat(str(end)):
                raise ValueError()
        except ValueError:
            deny("期间边界缺失或无效")

        def boundary(node):
            node = _unparen(node.this if isinstance(node, exp.Where) else node)
            if isinstance(node, exp.And):
                return boundary(node.left) | boundary(node.right)
            if isinstance(node, (exp.GTE, exp.LT)) and col(node.left, "invoice", "invoice_date"):
                pair = (">=" if isinstance(node, exp.GTE) else "<", _period_literal_date(node.right))
                if pair in {(">=", str(start)), ("<", str(end))}:
                    return {pair}
            deny("分母 WHERE 只允许相同期间两边界")

        if boundary(where) != {(">=", str(start)), ("<", str(end))}:
            deny("必须保留完整同期期间")
    elif where is not None:
        deny("全部数据口径不能增加国家或未确认期间")

    projected = _unparen(tree.selects[0])
    if isinstance(projected, exp.Round):
        projected = _unparen(projected.this)
    protected = False
    if isinstance(projected, exp.Case):
        branches = projected.args.get("ifs") or []
        if len(branches) != 1 or not isinstance(_unparen(branches[0].args.get("true")), exp.Null):
            deny("外层 CASE 只能保护零或 NULL 分母")

        def zero_guard(node):
            node = _unparen(node)
            if isinstance(node, exp.Or):
                return zero_guard(node.left) and zero_guard(node.right)
            if isinstance(node, exp.EQ):
                return any(total(a) and _number(b, 0) for a, b in ((node.left, node.right), (node.right, node.left)))
            return isinstance(node, exp.Is) and total(node.this) and isinstance(node.expression, exp.Null)

        if not zero_guard(branches[0].this):
            deny("CASE 保护必须检查真实全部发票金额")
        protected = True
        projected = _unparen(projected.args.get("default"))
    if isinstance(projected, exp.Mul):
        if _number(projected.left, 100):
            projected = _unparen(projected.right)
        elif _number(projected.right, 100):
            projected = _unparen(projected.left)
        else:
            deny("比例只允许明确的百分比缩放")
    if not isinstance(projected, exp.Div):
        deny("需要真实金额分子除以金额分母")
    numerator, divisor = _unparen(projected.left), _unparen(projected.right)
    if isinstance(numerator, exp.Mul):
        numerator = (_unparen(numerator.right) if _number(numerator.left, 100) else
                     _unparen(numerator.left) if _number(numerator.right, 100) else numerator)
    if isinstance(divisor, exp.Nullif):
        if not total(divisor.this) or not _number(divisor.expression, 0):
            deny("NULLIF 必须保护全部发票金额的零分母")
    elif not (protected and total(divisor)):
        deny("分母必须是无条件 SUM(invoice.total) 且有零保护")
    case = _unparen(numerator.this) if isinstance(numerator, exp.Sum) else None
    if not isinstance(case, exp.Case) or len(case.args.get("ifs") or []) != 1:
        deny("分子必须按国家 CASE 累计发票金额")
    branch = case.args["ifs"][0]
    condition = _unparen(branch.this)
    if not (col(branch.args.get("true"), "invoice", "total") and isinstance(condition, exp.EQ) and
            any(col(a, table, column_name) and isinstance(b, exp.Literal) and b.is_string and b.this == str(bound["value"])
                for a, b in ((condition.left, condition.right), (condition.right, condition.left)))):
        deny("分子字段、标准国家或累计金额与确认条件不同")
    default = _unparen(case.args.get("default"))
    if default is not None and not isinstance(default, exp.Null) and not _number(default, 0):
        deny("国家外分子只能为 0 或 NULL")
    return True
