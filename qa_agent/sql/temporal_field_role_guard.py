"""Check an actual program-grounded employee hire-date period in SQL WHERE."""
import re
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _active_scopes, _midnight_date
from qa_agent.sql.validator import SQLValidationError


def validate_temporal_field_role(sql,catalog,intent,*,question=''):
    get=lambda k,d=None:intent.get(k,d)if isinstance(intent,dict)else getattr(intent,k,d)
    role=(get('query_scope',{})or{}).get('temporal_field_role')
    explicit_hire=bool(re.search(r'入职.{0,10}员工|员工.{0,10}入职|\bhire_date\b|employees?.{0,12}hired|hired.{0,12}employees?',question,re.I))
    current=((get('time_scope',{})or{}).get('current')or{})
    named_period=bool(re.search(r'(?<!\d)(?:19|20)\d{2}|(?:上|下)半年|(?:今|去|前)年|(?:上|本|下)月|季度|早于|晚于|之前|之后',question))
    display_only=bool(re.search(r'列出|展示|显示|查看|给出|\b(?:list|show|display)\b',question,re.I)
                      and re.search(r'入职(?:日期|时间)|\bhire_date\b',question,re.I)
                      and not named_period and not re.search(r'筛选|过滤|范围|期间',question))
    needs_hire_filter=explicit_hire and (named_period or bool(current)) and not display_only
    if role is None and not needs_hire_filter:return{'verified':True,'mode':'no_explicit_temporal_field_role'}
    def deny(message):raise SQLValidationError('时间字段角色：'+message)
    if not isinstance(role,dict)or role.get('column')!='employee.hire_date'or role.get('role')!='hire_date':
        deny('用户明确问员工入职，但当前权威状态缺少真实employee.hire_date角色，不能由正确SQL反填状态。')
    evidence=role.get('source_evidence')
    if role.get('source')!='program:explicit_temporal_field_role'or not isinstance(evidence,str)or not evidence.strip():
        deny('入职日期角色没有程序重建的实际原文证据。')
    if question and re.sub(r'\s+','',evidence)not in re.sub(r'\s+','',question):
        deny('入职字段来源不是当前真实问题的原文片段。')
    qualifications=(get('query_scope',{})or{}).get('qualification_filters')
    if qualifications is not None and (not isinstance(qualifications,list) or qualifications):
        deny('尚有未证明的独立资格条件；当前有界入职证明仅支持已归一的同源期间，不能忽略额外筛选。')
    period=((get('time_scope',{})or{}).get('current')or{})
    if not period.get('start')or not period.get('end'):
        deny('入职筛选没有完整当前半开期间。')
    tree=_qualified(sql,catalog);scopes=_active_scopes(list(traverse_scope(tree)))
    checked=[]
    for scope in scopes:
        aliases={alias for alias,(_,source)in scope.selected_sources.items()if isinstance(source,exp.Table)and source.name=='employee'and(source.db or'public')=='public'}
        if not aliases:continue
        where=scope.expression.args.get('where')
        if where is None:deny('实际员工来源没有WHERE入职期间，SELECT/HAVING中的日期不能代替筛选。')
        if where.find(exp.Or)is not None:deny('当前有界入职范围证明不允许OR分支绕开时间条件。')
        boundaries={alias:set()for alias in aliases}
        def atoms(node):
            if isinstance(node,(exp.Where,exp.Paren)):return atoms(node.this)
            if isinstance(node,exp.And):return atoms(node.left)+atoms(node.right)
            return[node]
        for node in atoms(where):
            uses_role=any(c.table in aliases and c.name=='hire_date'for c in node.find_all(exp.Column))
            if not isinstance(node,(exp.GTE,exp.GT,exp.LT,exp.LTE,exp.EQ)):
                if uses_role:deny('入职边界必须是直接必然成立的比较，不能藏在NOT、CASE或其它表达式里。')
                continue
            op=node.key;column,value=node.left,node.right
            if isinstance(value,exp.Column)and not isinstance(column,exp.Column):
                column,value=value,column;op={'gte':'lte','gt':'lt','lte':'gte','lt':'gt'}.get(op,op)
            if not isinstance(column,exp.Column)or column.table not in aliases or column.name!='hire_date':
                if uses_role:deny('入职日期不能经函数或字段类型变换改变真实范围。')
                continue
            date=_midnight_date(value)
            if(op,date)==('gte',period['start']):boundaries[column.table].add('start')
            elif(op,date)==('lt',period['end']):boundaries[column.table].add('end')
            elif op in{'gte','gt','lte','lt','eq'}:
                deny('入职日期实际条件与当前半开期间不同，不能只保留其中两条正确边界掩盖额外缩期。')
        if any(found!={'start','end'}for found in boundaries.values()):
            deny('每个实际员工来源都须按真实hire_date保留>=开始/<结束两端，不能换成birth_date或只过滤一端。')
        checked.append({'employee_aliases':sorted(aliases),'period':period})
    if not checked:deny('实际结果未消费任何员工物理来源，未使用的正确CTE不能作证。')
    return{'verified':True,'mode':'program_grounded_physical_hire_date_half_open_period',
           'column':'employee.hire_date','scopes':checked,'source_evidence':evidence}
