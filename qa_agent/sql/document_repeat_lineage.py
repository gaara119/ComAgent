"""Bounded invoice/customer qualification proof through transparent CTEs.

Both direct and transparent-derived employee-grouped qualifications are proved.
This is not arbitrary SQL equivalence: filtered/aggregated/set-valued customer
sources fail closed. Every
accepted customer key is traced to a real PK occurrence, joined to the counted
invoice by its real FK. Names, example results and evaluation labels are unused.
"""
from dataclasses import dataclass
import re

from sqlglot import exp

from qa_agent.sql.validator import SQLValidationError


@dataclass(frozen=True)
class Field:
    occurrence: tuple
    table: str
    column: str


@dataclass
class Relation:
    fields: dict
    customer: Field | None = None
    employee: Field | None = None
    owner_member: bool = False


def prove_direct_customer_group_grain(scope,catalog):
    """Shared legacy direct-table grain check, including global repeat counts.

    Real to-one customer/employee attributes may be redundantly grouped with
    customer PK. Invoice IDs/dates and detail attributes split a customer's
    qualification and are never accepted as customer-grain keys.
    """
    def deny():raise SQLValidationError('复购客户与发票粒度：GROUP BY 必须保持每客户一组，不能按发票日期、发票ID、明细或未知表达式拆散资格。')
    from qa_agent.sql.semantic_guard import _mandatory_atoms
    sources={a:s for a,(_,s)in scope.selected_sources.items()}
    invoices={a for a,s in sources.items()if isinstance(s,exp.Table)and s.name=='invoice'and(s.db or'public')=='public'}
    if len(invoices)!=1:deny()
    reached=set(invoices)
    edges=[]
    for join in scope.expression.args.get('joins')or[]:
        if join.side or join.kind not in {'','INNER'}:continue
        for atom in _mandatory_atoms(join.args.get('on')).values():
            if isinstance(atom,exp.EQ)and isinstance(atom.left,exp.Column)and isinstance(atom.right,exp.Column):
                edges.append((atom.left,atom.right))
    while True:
        before=set(reached)
        for left,right in edges:
            for child,parent in((left,right),(right,left)):
                source,target=sources.get(child.table),sources.get(parent.table)
                if child.table not in reached or not isinstance(source,exp.Table)or not isinstance(target,exp.Table):continue
                if target.name not in{'customer','employee'}or(target.db or'public')!='public':continue
                physical=catalog.get_table(source.name,source.db or'public')
                true_fk=any(v.get('columns')==[child.name]and v.get('references',{}).get('table')==target.name
                    and v.get('references',{}).get('schema','public')=='public'
                    and v.get('references',{}).get('columns')==[parent.name]for v in physical.foreign_keys)
                if true_fk and catalog.get_table(target.name).primary_key==(parent.name,):reached.add(parent.table)
        if reached==before:break
    group=scope.expression.args.get('group')
    if group is None or not group.expressions or any(not isinstance(v,exp.Column)for v in group.expressions)or any(group.args.get(k)for k in('rollup','cube','grouping_sets')):deny()
    customer_key=False
    for column in group.expressions:
        source=sources.get(column.table)
        if not isinstance(source,exp.Table)or column.table not in reached:deny()
        if source.name=='invoice':
            if column.name!='customer_id':deny()
            customer_key=True
        elif source.name=='customer':customer_key=customer_key or column.name=='customer_id'
        elif source.name!='employee':deny()
    if not customer_key:deny()
    return{'verified':True,'mode':'same_customer_PK_functional_dependency_group_grain'}


def prove_direct_global_customer_membership(scope,catalog):
    """A nullable responsible-employee INNER is not the universe of customers.

    A real to-one LEFT lookup of employee names preserves unassigned customers;
    this is allowed, unlike rejecting every mention of the employee table.
    """
    from qa_agent.sql.semantic_guard import _mandatory_atoms
    sources={a:s for a,(_,s)in scope.selected_sources.items()}
    employee_aliases={a for a,s in sources.items()if isinstance(s,exp.Table)and s.name=='employee'and(s.db or'public')=='public'}
    if not employee_aliases:return{'verified':True,'mode':'no_nullable_employee_membership_restriction'}
    if not next(c for c in catalog.get_table('customer').columns if c.name=='support_rep_id').nullable:
        return{'verified':True,'mode':'catalog_nonnullable_responsible_employee_FK'}
    def deny():raise SQLValidationError('全体复购客户范围：可空负责员工的 INNER/成员筛选会删除未指派客户，不能把负责员工客户子集当全体客户。')
    for alias in employee_aliases:
        join=next((j for j in scope.expression.args.get('joins')or[]if j.this.alias_or_name==alias),None)
        if join is None or join.side!='LEFT' or join.kind not in{'','OUTER'}:deny()
        supported=False
        for atom in _mandatory_atoms(join.args.get('on')).values():
            if not isinstance(atom,exp.EQ)or not isinstance(atom.left,exp.Column)or not isinstance(atom.right,exp.Column):continue
            for key,owner in((atom.left,atom.right),(atom.right,atom.left)):
                source=sources.get(owner.table)
                if (key.table==alias and key.name=='employee_id'and isinstance(source,exp.Table)
                        and source.name=='customer'and(source.db or'public')=='public'and owner.name=='support_rep_id'):
                    supported=True
        if not supported:deny()
    where=scope.expression.args.get('where')
    if where is not None:
        for column in where.find_all(exp.Column):
            source=sources.get(column.table)
            if (column.table in employee_aliases or isinstance(source,exp.Table)and source.name=='customer'and column.name=='support_rep_id'):
                deny()
    return{'verified':True,'mode':'nullable_employee_LEFT_to_one_preserves_unassigned_customers'}


def prove_derived_customer_qualification(scope, catalog, *, question=""):
    """Return an auditable proof or reject an unsupported derived qualification.

    The caller supplies an actually consumed scope. Qualification has one real
    invoice source and only real to-one customer/employee sources. A derived
    customer may rename/project its PK and support FK through <=12 levels;
    only a mandatory responsible-employee non-NULL filter is supported there.
    """
    from qa_agent.sql.semantic_guard import _midnight_date

    def deny(message):
        raise SQLValidationError("复购派生客户谱系：" + message)

    def strip(node):
        while isinstance(node, (exp.Alias, exp.Paren)):
            node = node.this
        return node

    def atoms(node):
        if node is None:
            return []
        node = strip(node)
        if isinstance(node, (exp.Where, exp.Having)):
            return atoms(node.this)
        if isinstance(node, exp.And):
            return atoms(node.left) + atoms(node.right)
        return [node]

    employee_domain = bool(re.search(r"(?:各|每|按).{0,24}(?:销售|支持|负责|员工)", question))
    customer = catalog.get_table("customer")
    invoice = catalog.get_table("invoice")
    employee = catalog.get_table("employee")
    if customer.primary_key != ("customer_id",) or invoice.primary_key != ("invoice_id",) or employee.primary_key != ("employee_id",):
        deny("真实主键不符合当前已支持的客户/发票/员工关系。")
    if any(next(c for c in table.columns if c.name == key).nullable
           for table, key in ((customer, "customer_id"), (invoice, "invoice_id"), (employee, "employee_id"))):
        deny("资格计数和关联必须使用真实非空主键。")

    def fk(table, column, target, key):
        return any(v.get("columns") == [column] and v.get("references", {}).get("table") == target
                   and v.get("references", {}).get("schema", "public") == "public"
                   and v.get("references", {}).get("columns") == [key] for v in table.foreign_keys)

    if not fk(invoice, "customer_id", "customer", "customer_id") or not fk(customer, "support_rep_id", "employee", "employee_id"):
        deny("真实外键不能支持当前发票→客户→负责员工的身份关联。")

    def get_field(node, relations):
        node = strip(node)
        if not isinstance(node, exp.Column):
            deny("身份/分组键必须透明投影，不能用 CAST、函数、常量或子查询替换。")
        relation = relations.get(node.table)
        value = relation.fields.get(node.name) if relation else None
        if value is None:
            deny("当前作用域字段没有真实、唯一的来源投影。")
        return value

    def nonnull_support(node, relations):
        node = strip(node)
        if isinstance(node, exp.Not):
            node = strip(node.this)
        elif isinstance(node, exp.Is) and node.args.get("negate"):
            pass
        else:
            return False
        if not isinstance(node, exp.Is) or not isinstance(node.expression, exp.Null):
            return False
        field = get_field(node.this, relations)
        return employee_domain and field.table == "customer" and field.column == "support_rep_id"

    memo = {}

    def relation_for(source, owner, alias, depth=0):
        if depth > 12:
            deny("客户透传超过有界深度。")
        if isinstance(source, exp.Table):
            if (source.db or "public") != "public" or source.name not in {"customer", "employee", "invoice"}:
                deny("派生资格只支持真实客户、发票与到一负责员工关系，不能引入明细扇出。")
            table = catalog.get_table(source.name)
            occurrence = (id(owner), alias)
            fields = {c.name: Field(occurrence, table.name, c.name) for c in table.columns}
            return Relation(fields, fields.get("customer_id") if source.name == "customer" else None,
                            fields.get("employee_id") if source.name == "employee" else None)
        if source in memo:
            return memo[source]
        q = source.expression
        if not isinstance(q, exp.Select) or any(q.args.get(k) for k in
                ("group", "having", "qualify", "distinct", "limit", "offset", "laterals", "connect", "locks")):
            deny("客户 CTE 必须透明且保持主键唯一，不能聚合、去重、截断或消费集合运算。")
        relations = {a: relation_for(s, source, a, depth + 1) for a, (_, s) in source.selected_sources.items()}
        customer_keys = {r.customer for r in relations.values() if r.customer is not None}
        if len(customer_keys) != 1 or any(any(f.table == "invoice" for f in r.fields.values()) for r in relations.values()):
            deny("客户 CTE 须唯一追溯到一个真实客户 PK，不能混入发票/多客户或常量身份。")
        key = next(iter(customer_keys))
        joins = q.args.get("joins") or []
        if len(joins) != len(relations) - 1:
            deny("客户 CTE 的来源连接数不确定。")
        edges = []
        for join in joins:
            if join.side or join.kind not in {"", "INNER"} or join.args.get("using"):
                deny("客户 CTE 只支持明确 INNER 到一关联，不能凭外连接/笛卡尔积证明。")
            predicates = atoms(join.args.get("on"))
            if not predicates:
                deny("客户 CTE 缺少真实外键到主键的必要关联。")
            for predicate in predicates:
                if not isinstance(predicate, exp.EQ):
                    deny("关联条件含额外筛选或 OR，不能证明当前完整客户范围。")
                left, right = get_field(predicate.left, relations), get_field(predicate.right, relations)
                if left == right:
                    deny("同一字段自等不能证明两来源实际关联。")
                if not any((child.table, child.column, parent.table, parent.column) ==
                           ("customer", "support_rep_id", "employee", "employee_id")
                           for child, parent in ((left, right), (right, left))):
                    deny("客户关联附加了非真实外键条件，不能视作透明客户全集。")
                if not employee_domain and next(c for c in customer.columns if c.name == "support_rep_id").nullable:
                    deny("全体客户范围没有授权按负责员工排除可空未归属客户。")
                edges.append((left, right))
        reached = {key.occurrence}
        while True:
            before = set(reached)
            for left, right in edges:
                for child, parent in ((left, right), (right, left)):
                    if child.occurrence in reached and child.table == "customer" and child.column == "support_rep_id" and parent.table == "employee" and parent.column == "employee_id":
                        reached.add(parent.occurrence)
            if reached == before:
                break
        actual_occurrences = {f.occurrence for r in relations.values() for f in r.fields.values()}
        if reached != actual_occurrences:
            deny("客户 CTE 关联未证明真实客户→员工 N:1 主键关系。")
        nonnull_owner=False
        for predicate in atoms(q.args.get("where")):
            if not nonnull_support(predicate, relations):
                deny("客户 CTE 存在未授权额外筛选；国家、金额或 OR 不能当透明客户全集。")
            nonnull_owner=True
        fields = {}
        for projection in q.selects:
            if not projection.alias_or_name:
                deny("透明客户投影缺少唯一字段名。")
            if projection.alias_or_name in fields:
                deny("客户投影名重复，身份来源不唯一。")
            fields[projection.alias_or_name] = get_field(projection, relations)
        if key not in fields.values():
            deny("客户 CTE 必须实际保留真实客户 PK，不能只保留负责员工或假同名字段。")
        result = Relation(fields, key, owner_member=(nonnull_owner or any(r.owner_member or r.employee is not None for r in relations.values())))
        memo[source] = result
        return result

    q = scope.expression
    if not isinstance(q, exp.Select) or any(q.args.get(k) for k in ("limit", "offset", "qualify", "distinct", "laterals")):
        deny("客户资格聚合不能先截断、去重或窗口筛选。")
    relations = {alias: relation_for(src, scope, alias) for alias, (_, src) in scope.selected_sources.items()}
    invoice_aliases = {alias for alias, (_, src) in scope.selected_sources.items()
                       if isinstance(src, exp.Table) and src.name == "invoice" and (src.db or "public") == "public"}
    if len(invoice_aliases) != 1:
        deny("资格计数必须来自唯一真实 invoice 源。")
    invoice_alias = next(iter(invoice_aliases))
    invoice_occurrence = relations[invoice_alias].fields["invoice_id"].occurrence
    edges = []
    for join in q.args.get("joins") or []:
        if join.side or join.kind not in {"", "INNER"} or join.args.get("using"):
            deny("资格关联只支持真实 INNER 外键到主键，不能用外连接/笛卡尔积放大发票。")
        predicates = atoms(join.args.get("on"))
        if not predicates:
            deny("资格来源之间缺少真实必要关联。")
        for predicate in predicates:
            if not isinstance(predicate, exp.EQ):
                deny("资格关联包含额外筛选或 OR，无法证明完整期间客户范围。")
            left, right = get_field(predicate.left, relations), get_field(predicate.right, relations)
            if left == right:
                deny("自等关联不能证明实际客户身份。")
            if not any((child.table, child.column, parent.table, parent.column) in {
                    ("invoice", "customer_id", "customer", "customer_id"),
                    ("customer", "support_rep_id", "employee", "employee_id")}
                    for child, parent in ((left, right), (right, left))):
                deny("资格关联附加了非真实外键条件，不能证明当前完整发票集合。")
            if (not employee_domain and any(f.table == "employee" for f in (left, right))
                    and next(c for c in customer.columns if c.name == "support_rep_id").nullable):
                deny("全体客户范围不能因关联可空负责员工而丢失未归属客户。")
            edges.append((left, right))
    seen = {invoice_occurrence}
    while True:
        before = set(seen)
        for left, right in edges:
            for child, parent in ((left, right), (right, left)):
                if child.occurrence not in seen:
                    continue
                legal = ((child.table, child.column, parent.table, parent.column) in {
                    ("invoice", "customer_id", "customer", "customer_id"),
                    ("customer", "support_rep_id", "employee", "employee_id")})
                if legal:
                    seen.add(parent.occurrence)
        if seen == before:
            break
    # A derived customer already proved all its internal sources to one.
    required = {r.customer.occurrence if r.customer else r.employee.occurrence if r.employee else
                next(iter(r.fields.values())).occurrence for r in relations.values()}
    if seen != required:
        deny("实际 COUNT 发票与分组客户没有经真实 FK→PK 同一身份绑定，或存在发票扇出。")
    group = q.args.get("group")
    if group is None or any(not isinstance(v, exp.Column) for v in group.expressions) or any(group.args.get(k) for k in ("rollup", "cube", "grouping_sets")):
        deny("复购必须按真实客户粒度分组，不能按常量、转换或分组小计。")
    keys = [get_field(v, relations) for v in group.expressions]
    # Every actual customer/employee source is already proven N:1 from the
    # same invoice.customer_id. Its transparent attributes are functionally
    # dependent on that customer key, so redundant name grouping is harmless.
    # Invoice dates/IDs/amounts are not functionally dependent on the customer.
    if not any(k.table in {"customer", "invoice"} and k.column == "customer_id" for k in keys) or any(
            k.table not in {"customer","employee"} and (k.table,k.column)!=("invoice","customer_id") for k in keys):
        deny("GROUP BY 不是每客户一组，额外日期/发票键会拆散资格。")
    predicates = atoms(q.args.get("having"))
    if len(predicates) != 1 or not isinstance(predicates[0], (exp.GTE, exp.GT, exp.LTE, exp.LT)):
        deny("资格须唯一必要 COUNT(invoice_id)>=2，不能附加门槛或 OR。")
    predicate = predicates[0]
    count, number, op = strip(predicate.left), strip(predicate.right), predicate.key
    if isinstance(number, exp.Count):
        count, number = number, count
        op = {"lte": "gte", "lt": "gt", "gte": "lte", "gt": "lt"}[op]
    if not isinstance(count, exp.Count) or not isinstance(number, exp.Literal) or number.is_string or (op, str(number.this)) not in {("gte", "2"), ("gt", "1")}:
        deny("真实资格阈值不是每客户至少两张发票。")
    target = strip(count.this)
    if isinstance(target, exp.Distinct):
        if len(target.expressions) != 1:
            deny("DISTINCT 发票键必须唯一。")
        target = target.expressions[0]
    if not isinstance(target, exp.Star) and get_field(target, relations) != relations[invoice_alias].fields["invoice_id"]:
        deny("资格必须 COUNT 实际非空 invoice PK，不能数客户或同名假字段。")
    year = re.search(r"(?<!\d)(20\d{2}|19\d{2})\s*年", question)
    expected = {("gte", f"{year[1]}-01-01"), ("lt", f"{int(year[1])+1}-01-01")} if year else set()
    dates = set();nonnull_owner=False
    for predicate in atoms(q.args.get("where")):
        if nonnull_support(predicate, relations):
            nonnull_owner=True
            continue
        if not isinstance(predicate, (exp.GTE, exp.LT, exp.LTE, exp.GT)):
            deny("资格存在未授权额外筛选或 OR，不能改变实际客户发票集合。")
        left, right, op = strip(predicate.left), strip(predicate.right), predicate.key
        if isinstance(right, exp.Column):
            left, right = right, left
            op = {"lte": "gte", "lt": "gt", "gte": "lte", "gt": "lt"}[op]
        field = get_field(left, relations)
        if field != relations[invoice_alias].fields["invoice_date"]:
            deny("额外条件不是当前资格发票日期，不能缩小客户/金额范围。")
        value = _midnight_date(right)
        if value is None:
            deny("期间边界不是可证明等价的日期或零点时间戳。")
        dates.add((op, value))
    if dates != expected:
        deny("资格计数未严格使用用户指定完整年份，或新增未授权期间。")
    key_projections, owner_projections = [], []
    for projection in q.selects:
        target=strip(projection)
        if not isinstance(target,exp.Column):
            continue
        field=get_field(target,relations)
        if field.table in {"customer","invoice"} and field.column=="customer_id":
            key_projections.append(projection.alias_or_name)
        if field.table=="customer" and field.column=="support_rep_id":
            owner_projections.append(projection.alias_or_name)
    return {"verified": True, "mode": "consumed_transparent_customer_PK_invoice_FK_qualification",
            "invoice_aliases": sorted(invoice_aliases), "group_fields": [f"{v.table}.{v.column}" for v in keys],
            "period": sorted(dates), "transparent_customer_sources": len(memo),
            "qualified_customer_columns": key_projections, "qualified_owner_columns": owner_projections,
            "owner_membership_verified": nonnull_owner or any(r.owner_member or r.employee is not None for r in relations.values()),
            "proof": "true non-null invoice PK COUNT>=2; unique same-customer PK/FK lineage; no additional selection"}


def prove_grouped_repeat_output(scopes, qualified_proofs, catalog):
    """Prove grouped employee COUNT actually consumes the proven customer rows.

    An active but irrelevant scalar/cross-join reference is insufficient. Only
    transparent row forwarding, actual owner-key grouping and customer COUNT
    are supported. A final real employee-PK name lookup may be to-one INNER.
    """
    def deny(message):
        raise SQLValidationError("复购分组输出消费："+message)
    def strip(node):
        while isinstance(node,(exp.Alias,exp.Paren)):
            node=node.this
        return node
    def clean(q,*,final=False,allow_owner_where=False):
        if not isinstance(q,exp.Select) or any(q.args.get(k) for k in
                ("having","qualify","distinct","offset","laterals")) or (q.args.get("where") is not None and not allow_owner_where):
            deny("人数层/透传层含额外筛选、集合操作或去重，不能由旁边资格集合背书。")
        limit=q.args.get("limit")
        if limit is not None:
            deny("按各员工问数没有 TopN 授权，原始 SQL 不能截断分组或透明外层；系统执行展示上限应在此证明后添加。")
    def rows(source,depth=0):
        if depth>12:deny("资格行透传超出有界深度。")
        if source in qualified_proofs:
            proof=qualified_proofs[source]
            return ({v:"customer" for v in proof['qualified_customer_columns']} | {v:"owner" for v in proof['qualified_owner_columns']},
                    proof['owner_membership_verified'])
        if isinstance(source,exp.Table):deny("最终 COUNT 没有消费真实复购客户资格行。")
        q=source.expression;clean(q)
        if q.args.get("group") or q.args.get("joins"):deny("资格透传不能附加聚合或连接。")
        selected=source.selected_sources
        if len(selected)!=1:deny("资格透传没有唯一真实来源。")
        alias,(_,child)=next(iter(selected.items()));fields,membership=rows(child,depth+1);output={}
        for projection in q.selects:
            target=strip(projection)
            if not isinstance(target,exp.Column) or target.table!=alias or target.name not in fields:
                deny("资格行的客户/员工键被转换、替换或混入无关列。")
            output[projection.alias_or_name]=fields[target.name]
        return output,membership
    root=next(s for s in scopes if s.parent is None)
    cursor=root;visited=set();requested={p.alias_or_name for p in root.expression.selects}
    while True:
        if cursor in visited:deny("最终结果出现循环谱系。")
        visited.add(cursor)
        q=cursor.expression;clean(q,final=True,allow_owner_where=any(isinstance(strip(p),exp.Count)for p in q.selects))
        if any(isinstance(strip(p),exp.Count) and p.alias_or_name in requested for p in q.selects):break
        if any(isinstance(strip(p),exp.Count) for p in q.selects):deny("最终没有输出实际复购客户计数，不能仅展示旁边员工字段。")
        if q.args.get("group") or q.args.get("joins"):deny("最终结果不是唯一真实分组客户计数。")
        selected=cursor.selected_sources
        if len(selected)!=1:deny("最终结果存在无关来源/常量，资格 CTE 没有决定人数。")
        alias,(_,source)=next(iter(selected.items()))
        if isinstance(source,exp.Table):deny("最终结果不是资格客户计数的透明投影。")
        if any(not isinstance(strip(p),exp.Column) or strip(p).table!=alias for p in q.selects):
            deny("最终投影包含无关子查询或数学替换。")
        # A final SELECT cannot silently drop the actual count projection.
        required={strip(p).name for p in q.selects if p.alias_or_name in requested}
        if not any(p.alias_or_name in required and isinstance(strip(p),exp.Count) for p in source.expression.selects):
            # Permit another transparent layer, but eventually its selected
            # field names must expose the same count, not a side computation.
            if any(isinstance(strip(p),exp.Count) for p in source.expression.selects):
                deny("最终未投影实际复购客户计数。")
        requested=required;cursor=source
    selected=cursor.selected_sources
    qualified=[];employees={};customers={}
    for alias,(_,source) in selected.items():
        if isinstance(source,exp.Table):
            if source.name not in {"customer","employee"} or (source.db or "public")!="public":deny("人数聚合含无关物理表，资格只被旁路消费。")
            primary="customer_id" if source.name=="customer" else "employee_id"
            if catalog.get_table(source.name).primary_key!=(primary,):deny("实名/归属回查没有真实唯一主键。")
            (customers if source.name=="customer" else employees)[alias]=source
        else:qualified.append((alias,*rows(source)))
    if len(qualified)!=1:deny("人数层须唯一消费实际复购客户行，不能多次连接或跨集合。")
    alias,fields,owner_membership=qualified[0]
    if "customer" not in fields.values():deny("资格行没有保留真实客户键。")
    if len(customers)>1:deny("最终只支持一个真实客户主键回查，不能混合客户实例。")
    linked=set();edges=[]
    for join in q.args.get("joins") or []:
        on=strip(join.args.get("on"))
        if join.side or join.kind not in {"","INNER"} or not isinstance(on,exp.EQ):deny("人数层仅支持员工真实 PK 的 INNER 到一回查。")
        a,b=strip(on.left),strip(on.right)
        if not isinstance(a,exp.Column) or not isinstance(b,exp.Column):deny("最终回查不是透明身份等值。")
        edges.append((a,b))
    linked_customers=set()
    for a,b in edges:
        matched=False
        for key,lookup in ((a,b),(b,a)):
            if key.table==alias and fields.get(key.name)=="customer" and lookup.table in customers and lookup.name=="customer_id":
                linked_customers.add(lookup.table);matched=True
            owner=(key.table==alias and fields.get(key.name)=="owner") or (key.table in customers and key.name=="support_rep_id")
            if owner and lookup.table in employees and lookup.name=="employee_id":
                linked.add(lookup.table);matched=True
        if not matched:deny("最终回查没有按实际资格客户/负责员工主键等值绑定。")
    if (linked!=set(employees) or linked_customers!=set(customers)
            or len(q.args.get("joins") or [])!=len(employees)+len(customers)):
        deny("最终存在未被真实员工主键约束的连接/扇出。")
    group=q.args.get("group")
    if group is None or not group.expressions or any(group.args.get(k) for k in ("rollup","cube","grouping_sets")):
        deny("按员工人数必须按真实员工键分组，不能使用总计分组。")
    owner_key=False
    def field_role(node):
        node=strip(node)
        if not isinstance(node,exp.Column):return None
        if node.table==alias:return fields.get(node.name)
        if node.table in linked_customers and node.name in {"customer_id","support_rep_id"}:
            return "customer" if node.name=="customer_id" else "owner"
        if node.table in employees and node.name in {"employee_id","first_name","last_name"}:
            return "owner" if node.name=="employee_id" else "owner_name"
        return None
    where=q.args.get('where')
    if where is not None:
        def owner_nonnull(node):
            node=strip(node)
            if isinstance(node,(exp.Where,exp.And)):
                return owner_nonnull(node.this) if isinstance(node,exp.Where)else owner_nonnull(node.left)and owner_nonnull(node.right)
            if isinstance(node,exp.Not):node=strip(node.this)
            elif not(isinstance(node,exp.Is)and node.args.get('negate')):return False
            return isinstance(node,exp.Is)and isinstance(node.expression,exp.Null)and field_role(node.this)=='owner'
        if not owner_nonnull(where):deny('最终人数层只允许必要真实员工非空域限制，不能附加国家、金额、OR或其它筛选。')
        owner_membership=True
    if not(owner_membership or linked):
        deny('可空负责员工 FK 尚未由实际 INNER员工PK 或必要 IS NOT NULL 限定，不能把 NULL 桶作为真实员工。')
    for expression in group.expressions:
        role=field_role(expression)
        if role not in {"owner","owner_name"}:deny("最终分组不是负责员工身份，不能按客户或同名显示值误聚合。")
        owner_key=owner_key or role=="owner"
    if not owner_key:deny("仅员工姓名不保证实体唯一，须保留真实员工键分组。")
    counts=0;visible_owner=False
    for projection in q.selects:
        node=strip(projection)
        if isinstance(node,exp.Count):
            target=strip(node.this)
            if isinstance(target,exp.Distinct):
                if len(target.expressions)!=1:deny("人数 DISTINCT 不是唯一客户键。")
                target=target.expressions[0]
            if not isinstance(target,exp.Star) and field_role(target)!="customer":deny("最终应计资格客户行/客户键，不能数员工、常量或无关字段。")
            if projection.alias_or_name in requested:counts+=1
        elif field_role(node) not in {"owner","owner_name"}:
            deny("最终交付包含未由真实资格客户人数支持的表达式。")
        elif projection.alias_or_name in requested:
            visible_owner=True
    if not counts:deny("最终未实际输出复购客户 COUNT。")
    if not visible_owner:deny("按员工问数须展示实际员工键/姓名，不能交付无法对应员工的裸人数行。")
    return {"verified":True,"mode":"grouped_COUNT_consumes_verified_customer_qualification_rows",
            "count_projections":counts,"employee_PK_lookups":sorted(linked)}
