"""Deterministic business presentation of actual database results.

Raw table values remain unchanged for auditing. No model or reference answer is
used to format percentages, compare counts, or produce Chinese display labels.
"""
from decimal import Decimal, InvalidOperation
import re


LABELS = {
    "customer_full_name": "客户姓名", "full_name": "姓名",
    "invoice_revenue": "发票销售额", "total_revenue": "销售额合计", "average_customer_amount": "平均每位客户金额",
    "detail_revenue": "销售明细金额", "average_invoice_amount": "平均每张发票金额", "revenue_share_pct": "销售额占比", "revenue_share_percent": "销售额占比",
    "revenue_share": "销售额占比", "customer_id": "客户编号", "customer_name": "客户姓名", "first_name": "名字", "last_name": "姓氏",
    "employee_id": "员工编号", "employee_name": "员工姓名", "employee_last_name": "员工姓氏",
    "artist_id": "艺术家编号", "artist_name": "艺术家名称", "album_id": "专辑编号", "album_title": "专辑名称",
    "track_id": "曲目编号", "track_name": "曲目名称", "playlist_name": "歌单名称", "genre_name": "流派名称",
    "country": "国家", "billing_country": "账单国家", "name": "名称", "title": "名称",
    "revenue": "销售额", "sales": "销售额", "sales_amount": "销售额", "total_amount": "金额合计",
    "total_spent": "消费金额", "amount": "金额", "invoice_count": "发票张数", "customer_count": "客户数",
    "track_count": "曲目首数", "album_count": "专辑数", "purchased_quantity": "购买数量", "quantity": "数量",
    "support_rep_id": "客户负责员工编号", "repeat_customer_count": "期间内复购客户数", "employee_count": "员工人数",
    "month": "月份", "year": "年份", "share": "占比", "ratio": "比例", "growth_rate": "增长率",
    "percentage": "百分比", "rank": "名次", "total_bytes": "存储字节数", "total_milliseconds": "总时长（毫秒）",
    "total": "合计", "count": "数量", "difference": "差额", "diff": "差额",
}


def column_labels(columns):
    result = {}
    for index, name in enumerate(columns):
        lower = name.casefold()
        label = LABELS.get(lower)
        if not label and "market" in lower:
            prefix = "非重点市场" if re.search(r"other|rest|non", lower) else "重点市场" if re.search(r"key|focus|priority", lower) else "市场"
            label = prefix + ("销售额" if re.search(r"revenue|sales|amount", lower) else "数量" if "count" in lower else "")
        if not label and re.search(r"diff|difference|gap", lower):
            label = "销售额差额" if re.search(r"revenue|sales|amount", lower) else "差值"
        result[name] = label or name
    return result


def _number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
        return number if number.is_finite() else None
    except InvalidOperation:
        return None


def _global_tie_fields(sql):
    """Trace every actual secondary key; unsupported expressions stay silent."""
    import sqlglot
    from sqlglot import exp
    from sqlglot.optimizer.scope import build_scope
    root=build_scope(sqlglot.parse_one(sql,read='postgres'))
    if root is None or not isinstance(root.expression,exp.Select):return []
    order=root.expression.args.get('order')
    if order is None or len(order.expressions)<2:return []
    def field(node,owner,depth=0):
        if depth>12:return None
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        if not isinstance(node,exp.Column):return None
        if not node.table:
            projection=next((p for p in owner.expression.selects if p.alias_or_name==node.name),None)
            if projection is not None and not(isinstance(projection,exp.Column)and not projection.table and projection.name==node.name):
                return field(projection,owner,depth+1)
            selected=list(owner.selected_sources.values())
            return node.name if len(selected)==1 and isinstance(selected[0][1],exp.Table)else None
        source=owner.sources.get(node.table)
        if isinstance(source,exp.Table):return node.name
        if source is None or not isinstance(source.expression,exp.Select):return None
        projection=next((p for p in source.expression.selects if p.alias_or_name==node.name),None)
        return field(projection,source,depth+1)if projection is not None else None
    result=[]
    for item in order.expressions[1:]:
        physical=field(item.this,root);label=LABELS.get(physical.casefold())if physical else None
        if label is None:return []
        result.append(label+('降序'if item.args.get('desc')else'升序'))
    return result


def present(question, table, columns, formats, *, metric=None, brief="", task_type=None, sql=None,
            query_scope=None, partition_proof=None, ratio_basis=None, groupwise_proof=None, comparison_proof=None,
            catalog=None, semantic_intent=None):
    if len(set(columns)) != len(columns):
        raise ValueError('结果包含重复列名，无法保持每个值的独立身份；请为投影提供不同列名。')
    labels = column_labels(columns)
    meanings = {}
    if sql:
        from qa_agent.sql.projection_labels import projection_labels_from_sql
        for column, label in projection_labels_from_sql(sql, columns, include_simple=True).items():
            # A generic COUNT(*) proof must not erase an already recognized
            # specific business measure; a proved detail amount can refine it.
            if label != '数量' or labels.get(column) == column:
                labels[column] = label
        from qa_agent.sql.projection_semantics import projection_semantics
        meanings = projection_semantics(sql, columns, catalog=catalog)
        for column, meaning in meanings.items():
            # Existing singleton/pivot entity labels are already proved by
            # their real predicates; keep their entity context for comparison.
            # Their older unit renderer does not describe casts/rounding;
            # retain only its proved subject before the actual transform label.
            if ' · ' in labels.get(column,'')and meaning.get('label_protected'):
                labels[column]=labels[column].split(' · ',1)[0]+' · '+meaning['label']
            elif ' · ' not in labels.get(column, ''):
                labels[column] = meaning['label']
        # SQL exists but its projected meaning was unsupported: do not invent
        # money/market/difference semantics from a model-chosen output alias.
        for column in columns:
            if column not in meanings and not any(x in labels.get(column,'') for x in [' · ', ' − ']):
                labels[column] = column
        from qa_agent.sql.projection_semantics import proved_repeat_count_labels
        for column,label in proved_repeat_count_labels(sql,columns,catalog=catalog,semantic_intent=semantic_intent).items():
            if not meanings.get(column,{}).get('label_protected'):labels[column]=label
    # The actual validated ratio expression establishes the output role.
    # An arbitrary model alias must not leak an English implementation label
    # into a business answer whose requested headings are Chinese.
    for column, rule in formats.items():
        if column in labels and rule.get('kind','percentage')=='percentage' and meanings.get(column,{}).get('kind')not in {'count','money','rank','field'}:
            current=meanings.get(column,{})
            labels[column] = (current['label']if current.get('kind')=='ratio'and current.get('label')!='占比'
                              else'增长率'if task_type in {'growth','yoy'}else'占比')
    partition_columns = set()
    if partition_proof and partition_proof.get("mode") == "typed_partition_invoice_amount_lineage":
        for role, item in partition_proof["roles"].items():
            column = item["column"]
            role_label = {"focus":"重点市场发票金额", "other":"其余市场发票金额",
                          "difference":"重点市场减其余市场的差额"}[role]
            meaning=meanings.get(column,{})
            if meaning.get('transformed')or meaning.get('filtered'):
                role_label+='（'+meaning['label']+'）'
            labels[column]=role_label
            partition_columns.add(column)
    # All proof- and format-specific labels are final before collision handling.
    # Preserve real condition identities; identical/unsupported labels retain
    # their original output keys rather than inventing positional subjects.
    collisions={label for label in labels.values() if list(labels.values()).count(label)>1}
    for column in columns:
        if labels[column] in collisions:
            labels[column] += ' ['+column+']'
    from qa_agent.sql.percentage_precision import requested_percent_digits
    def precision_error(message):
        raise ValueError(message)
    requested = requested_percent_digits({'query_scope': query_scope or {}}, precision_error)
    percent_source=(query_scope or{}).get('percent_precision_source')or{}
    percent_raw=percent_source.get('source')=='program:explicit_percent_precision_removed'
    if percent_source.get('source')=='program:explicit_percent_precision_pending':
        raise ValueError('百分比展示精度仍待确认，不能回退正文格式。')
    # A real task source (including removal) outranks persistent brief text.
    if requested is None and not percent_source:
        requested=requested_percent_digits({'output_requirements':[brief]},precision_error)
    places=requested if requested is not None else 2
    money_source=(query_scope or{}).get('money_precision_source')
    money_places=2;money_raw=False
    if money_source is not None:
        from qa_agent.sql.money_precision_source import valid_money_precision_metadata
        if not valid_money_precision_metadata(money_source):
            raise ValueError('金额展示精度缺少合法程序来源或尚待确认。')
        money_raw=money_source['status']=='removed'
        if not money_raw:money_places=money_source['digits']

    def display(value, column):
        if value is None:
            return "无可汇总数据"
        number = _number(value)
        rule=formats.get(column)or{}
        percent=bool(rule)and rule.get('kind','percentage')=='percentage'and meanings.get(column,{}).get('kind')not in {'count','money','rank','field'}
        if percent and number is not None:
            from qa_agent.sql.result_format import display_numeric
            return str(display_numeric(value,{'kind':'percentage','scale':formats[column]['scale'],
                'digits':None if percent_raw else places,'source':'actual_sql_projection','rounding':'half_even'}))
        money = (meanings.get(column,{}).get('kind')=='money' or column in partition_columns) if sql else (
            bool(re.search(r'(?:销售额|销售额合计|销售明细金额|销售明细金额合计|消费金额|平均每.*金额|金额合计|发票金额|销售额差额)$',labels.get(column,''))) or any(word in column.casefold() for word in ("revenue", "sales", "amount", "spent", "消费", "金额", "销售额"))
                 or len(columns) == 1 and metric in {"invoice_revenue", "detail_revenue", "average_invoice_amount", "average_customer_amount"})
        if number is not None and money:
            from qa_agent.sql.result_format import display_numeric
            return str(display_numeric(value,{'kind':'money','digits':None if money_raw else money_places,
                'source':'actual_sql_projection','rounding':'half_even'}))
        if number is not None and number == number.to_integral_value() and (meanings.get(column,{}).get('kind')in{'count','rank'} or re.search(r"count|quantity|bytes|milliseconds|_id$|^year$|^month$|数量|人数|首数|张数", column, re.I)):
            return str(int(number))
        return str(value)

    if not table:
        answer = "按当前条件未查到记录；没有改动期间、地区或统计口径。"
    elif len(table) == 1 and len(columns) == 1:
        answer = "查询结果：" + display(table[0].get(columns[0]), columns[0]) + "。"
        if _number(table[0].get(columns[0])) == 0 and re.search(r"count|数量|人数|首数|张数", columns[0], re.I):
            answer += "按当前条件和计数口径，计入的记录数为0。"
    else:
        per_group = (query_scope or {}).get("ranking_scope") == "per_group"
        verified_ratio_rank = bool(ratio_basis and ratio_basis.get("source") == "program:proved_ratio_operands" and ratio_basis.get("ranking"))
        show_rank = (task_type == "ranking" or verified_ratio_rank) and (not per_group or (query_scope or {}).get("per_group_limit") == 1) and not any(labels.get(column)=='名次' or re.search(r"^rank$|^rnk$|^rn$|名次", column, re.I) for column in columns)
        lines = ["查询结果如下：", ("名次 | " if show_rank else "") + " | ".join(labels[column] for column in columns)]
        per_group = (query_scope or {}).get("ranking_scope") == "per_group"
        lines.extend((str(1 if per_group else index + 1) + " | " if show_rank else "") +
                     " | ".join(display(row.get(column), column) for column in columns)
                     for index, row in enumerate(table[:20]))
        answer = "\n".join(lines)
        if len(table) > 20:
            answer += f"\n本次业务说明展示前20行，实际查询返回{len(table)}行；完整结果在结果面板。"
        if len(table) == 2 and not (comparison_proof or {}).get('requires_display') and re.search(r"哪个.{0,20}更多|多几(?:首|个|张|位)|差多少", question):
            numeric = [column for column in columns if all(_number(row.get(column)) is not None for row in table)]
            names = [column for column in columns if all(isinstance(row.get(column), str) and _number(row.get(column)) is None for row in table)]
            if len(numeric) == 1 and len(names) == 1:
                measure, name = numeric[0], names[0]
                ordered = sorted(table, key=lambda row: _number(row[measure]), reverse=True)
                difference = _number(ordered[0][measure]) - _number(ordered[1][measure])
                answer += (f"\n{ordered[0][name]} 比 {ordered[1][name]} 多 {difference}。" if difference
                           else "\n两项数量相同，差为0。")
        if len(table) == 1 and not (comparison_proof or {}).get('requires_display') and re.search(r"哪个.{0,20}更多|多几(?:首|个|张|位)", question):
            counted = [column for column in columns if _number(table[0].get(column)) is not None
                       and re.search(r"· (?:曲目首数|专辑数|客户数|发票张数|数量)$", labels[column])]
            if len(counted) == 2:
                more, less = sorted(counted, key=lambda column: _number(table[0][column]), reverse=True)
                delta = _number(table[0][more]) - _number(table[0][less])
                answer += f"\n{labels[more]}比{labels[less]}多{delta}。" if delta else "\n两项数量相同，差为0。"
        if task_type == "ranking" and sql and per_group:
            from hashlib import sha256
            proof=groupwise_proof or {}
            if (proof.get('verified')is True and proof.get('source')=='program:proved_groupwise_window'
                    and proof.get('mode')=='physical_partition_measure_and_rank_filter'
                    and proof.get('sql_sha256')==sha256(sql.encode('utf-8')).hexdigest()):
                proofs=proof.get('proofs')or[]
                orders=[p.get('tie_breakers')for p in proofs if p.get('tie_breakers_verified')and p.get('order_source')=='actual_consumed_ROW_NUMBER_window']
                if orders and len(orders)==len(proofs)and orders[0]and all(order==orders[0]for order in orders):
                    parts=[]
                    for item in orders[0]:
                        name=item['field'].rsplit('.',1)[-1];label=LABELS.get(name.casefold())
                        if label is None:parts=[];break
                        parts.append(label+('降序'if item['direction']=='desc'else'升序'))
                    if parts:answer+='\n每组主指标并列时，按'+'、'.join(parts)+'排列。'
        elif task_type == "ranking" and sql:
            keys=_global_tie_fields(sql)
            if keys:answer+='\n并列时按'+'、'.join(keys)+'排列。'
    if partition_columns:
        answer += "\n其余市场指重点名单以外的已知账单国家；账单国家为空的记录不归入任一组。"
    if ratio_basis and ratio_basis.get("source") in {"program:proved_ratio_operands", "program:proved_invoice_share", "program:proved_customer_winner_ratio"}:
        answer += "\n" + ratio_basis["text"]
    return answer + "\n数据来源：数据库。", labels
