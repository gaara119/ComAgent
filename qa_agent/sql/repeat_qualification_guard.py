"""Consume the registered per-customer repeat qualification, not a final count >=2."""
import json
from pathlib import Path
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from qa_agent.context import current_context
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _active_scopes,_physical_field,_invoice_grain_is_preserved,_midnight_date
from qa_agent.sql.validator import SQLValidationError,validate_value_bindings

ROOT=Path(__file__).resolve().parents[2]
DEFINITION_PATH='data/rules/metric_definitions.json'
DEFINITION_REF=DEFINITION_PATH+'#metric_id=repeat_customer_count'


def validate_repeat_qualification(sql,catalog,intent):
    get=lambda k,d=None:intent.get(k,d)if isinstance(intent,dict)else getattr(intent,k,d)
    typed=(get('query_scope',{})or{}).get('repeat_qualification')
    if typed is None:return{'verified':True,'mode':'no_typed_repeat_qualification'}
    def deny(message):raise SQLValidationError('已注册复购资格：'+message)
    required={'group_by':'invoice.customer_id','aggregate':'COUNT','column':'invoice.invoice_id',
        'operator':'>=','value':2,'source':'program:approved_registered_repeat_metric','definition_ref':DEFINITION_REF}
    if not isinstance(typed,dict)or any(typed.get(k)!=v for k,v in required.items())or isinstance(typed.get('value'),bool):
        deny('字段、客户粒度、发票计数阈值或已注册来源不一致，不能把最终客户人数>=2当复购。')
    definition=json.loads((ROOT/DEFINITION_PATH).read_text(encoding='utf-8'))
    metric=next((v for v in definition.get('metrics',[])if v.get('id')=='repeat_customer_count'),None)
    if definition.get('review_status')!='approved'or metric is None or metric.get('expression')!='COUNT of customers with COUNT(invoice_id) >= 2 in period':
        deny('当前本地已确认注册定义不能支持该资格，不能只信模型写出的ref。')
    invoice=catalog.get_table('invoice')
    if invoice.primary_key!=('invoice_id',)or not{'invoice_id','customer_id','invoice_date'}<=set(invoice.column_names):
        deny('真实invoice主键/客户键/日期与注册定义不一致。')
    evidence=typed.get('source_evidence');ctx=current_context()
    actual=[ctx.current_user_message,ctx.text]if ctx else[]
    if not isinstance(evidence,str)or not evidence.strip()or not any(evidence in(text or'')for text in actual):
        deny('资格来源短语没有实际当前用户输入或完整正文依据，不能由模型标签自证。')
    time=get('time_scope',{})or{};period=time.get('current')or{};all_data=time.get('all_data')is True
    ref=typed.get('period_ref')
    if ref not in{'time_scope','time_scope.current','time_scope.all_data'}:deny('期间引用不是当前权威time_scope。')
    if ref=='time_scope.current'and not period:deny('期间ref指向不存在的current。')
    if ref=='time_scope.all_data'and not all_data:deny('没有全数据授权，ref不能自行新增默认。')
    if bool(period.get('start'))!=bool(period.get('end'))or not period.get('start')and not all_data:
        deny('当前期间或全数据授权缺失，不能默认为任意期间复购。')
    if period and all_data:deny('current与all_data同时存在，期间权威有冲突。')
    bindings=[b for b in(get('filters',[])or[])if b.get('binding_scope','global')in{None,'global','eligibility'}]
    scopes=list(traverse_scope(_qualified(sql,catalog)));active=_active_scopes(scopes);candidates=[]
    def strip(n):
        while isinstance(n,(exp.Alias,exp.Paren)):n=n.this
        return n
    def atoms(n):
        if n is None:return[]
        n=strip(n)
        if isinstance(n,(exp.Where,exp.Having)):return atoms(n.this)
        if isinstance(n,exp.And):return atoms(n.left)+atoms(n.right)
        return[n]
    for scope in active:
        q=scope.expression;group=q.args.get('group');having=q.args.get('having')
        if not group or not having:continue
        if any(not isinstance(strip(v),exp.Column)for v in group.expressions):continue
        keys=[_physical_field(v,scope)for v in group.expressions]
        if not any(k in{'invoice.customer_id','customer.customer_id'}for k in keys):continue
        if any(k not in{'invoice.customer_id','customer.customer_id','customer.support_rep_id'}for k in keys):continue
        predicates=atoms(having)
        if len(predicates)!=1:continue
        atom=predicates[0]
        if not isinstance(atom,(exp.GTE,exp.GT)):continue
        count,threshold=strip(atom.left),strip(atom.right)
        if not isinstance(count,exp.Count)or not isinstance(threshold,exp.Literal)or threshold.is_string or(atom.key,threshold.this)not in{('gte','2'),('gt','1')}:continue
        target=count.this
        if isinstance(target,exp.Distinct):
            if len(target.expressions)!=1:continue
            target=target.expressions[0]
        if not isinstance(target,exp.Star)and(not isinstance(strip(target),exp.Column)or _physical_field(target,scope)!='invoice.invoice_id'):continue
        # The minimal registered definition has no track-side existence filter
        # or fanout. Even COUNT DISTINCT cannot authorize an unrelated JOIN.
        if not _invoice_grain_is_preserved(scope,catalog):continue
        if q.args.get('limit')or q.args.get('offset')or q.args.get('qualify'):deny('资格客户集合不能先截断或再次窗口筛选。')
        seen_dates=set();matched=set()
        for predicate in atoms(q.args.get('where')):
            if isinstance(predicate,(exp.GTE,exp.LT))and isinstance(strip(predicate.left),exp.Column)and _physical_field(predicate.left,scope)=='invoice.invoice_date':
                seen_dates.add((predicate.key,_midnight_date(predicate.right)));continue
            accepted=[]
            for index,binding in enumerate(bindings):
                clone=q.copy();clone.set('expressions',[exp.Literal.number(1)]);clone.set('where',exp.Where(this=predicate.copy()))
                for key in('with_','group','having','order','limit','offset','qualify'):clone.set(key,None)
                try:validate_value_bindings(clone.sql(dialect='postgres'),catalog,[{**binding,'binding_scope':'global'}]);accepted.append(index)
                except ValueError:pass
            if not accepted:deny('资格计数存在当前未授权额外筛选，不能沿用退休名单或OR旁路。')
            matched.update(accepted)
        expected={('gte',period['start']),('lt',period['end'])}if period.get('start')else set()
        if seen_dates!=expected:deny('每客户发票资格计数未严格使用当前期间。')
        if matched!=set(range(len(bindings))):deny('资格计数遗漏当前已确认筛选。')
        candidates.append(q.sql(dialect='postgres'))
    if not candidates:deny('实际被消费的SQL没有真实每客户发票COUNT>=2资格，不能用全局客户COUNT或未用CTE冒充。')
    output=None
    if get('metric')=='repeat_customer_count'and not get('grouping'):
        from qa_agent.sql.repeat_count_guard import validate_repeat_customer_count_output
        output=validate_repeat_customer_count_output(sql,catalog,intent,qualified_scope_sqls=set(candidates))
    return{'verified':True,'mode':'registered_repeat_qualification_consumed','definition_ref':DEFINITION_REF,
        'source_evidence':evidence,'period_ref':ref,'period':period,'all_data':all_data,
        'qualified_scopes':candidates,'global_output_proof':output,
        'grouped_output_boundary':'existing document/semantic proofs retain responsibility for grouped output shape'}
