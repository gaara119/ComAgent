"""Bounded, original-question obligations, independent of model plan coverage.

This is deliberately not a general semantic judge. It protects the already
supported database numeric requests and artist formation/style facts from being
silently dropped by a syntactically valid tool plan. It never reads labels,
entity answers, files or model history, and never authorizes an extra tool.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import re

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import build_scope,Scope


@dataclass(frozen=True)
class RequestObligation:
    kind: str
    evidence: str
    object: str | None = None
    entity: str | None = None
    fact_detail: str | None = None

    def public(self):
        return asdict(self)


_COUNTS = {
    "album": r"专辑|albums?", "track": r"曲目|歌曲|tracks?|songs?",
    "customer": r"客户|customers?", "invoice": r"发票|invoices?",
    "employee": r"员工|employees?", "playlist": r"歌单|playlists?",
    "artist": r"艺术家|乐队|artists?|bands?",
}
_COUNT = r"多少|几(?:张|个|位|名|首|条|支)|数量|总数|首数|张数|人数|\bcount\b|\bhow many\b|\bnumber\s+of\b"
_AMOUNT = r"销售(?:明细)?(?:额|金额)|发票(?:总额|金额|销售额)|消费金额|(?<![a-z0-9_])revenue(?![a-z0-9_])|(?<![a-z0-9_])sales\s+amount(?![a-z0-9_])"
_SALES_MEASURE = r"(?<![a-z0-9_])sales(?:\s+volume)?(?![a-z0-9_])|销量"
_NUMERIC_REQUEST = r"多少|计算|统计|求|合计|总额|最高|最低|排名|返回|列出|\b(?:what|show|return|calculate|total|sum|how much)\b"
# Keep original-question classification and proposed-step matching on the same
# bounded date vocabulary. A date fact is still distinct from people/background.
_FORMATION_DATE = r"何时|什么时候|哪(?:一)?年|何年|几年|时间|年份|\bwhen\b|\bdate\b|\byear\b"
_FACTS = {
    "formation": r"(?:何时|什么时候|哪(?:一)?年|何年|几年|谁|哪些人|when|who).{0,12}(?:成立|组建|formed|founded)|(?:成立|组建)(?:时间|年份|背景|经过|于哪|在哪年|于何年)|(?:组建者|创始人).{0,8}(?:是谁|有哪些|包括谁)|\b(?:formation|founding)\s+(?:date|year)\b|\b(?:when|(?:what|which)\s+year)\b[^，,；;。！？!?\n]{0,48}\b(?:formed|founded)\b",
    "music_style": r"(?:介绍|说明|描述|什么|哪些|哪种|怎样|如何).{0,14}(?:音乐风格|音乐类型|曲风|风格|(?<![a-z0-9_])style(?![a-z0-9_]))|(?:音乐风格|曲风|风格).{0,10}(?:是什么|有哪些|怎样)|\b(?:music(?:al)?\s+style)\b|\bwhat\b.{0,45}\b(?:style|genre)\b|(?<![a-z0-9_])genre(?![a-z0-9_])(?:\s*(?:是什么|有哪些|怎样))?\s*$",
}


def _clauses(question):
    return [part.strip() for part in re.split(r"[。！？!?；;，,\n]", question) if part.strip()]


def _entity_names(documents):
    names = set()
    for document in documents:
        ref = document.get('entity_ref', '') or ''
        if ref.startswith('chinook:artist:') and len(ref.split(':',3)) == 4:
            names.add(ref.split(':',3)[3])
    return sorted(names, key=len, reverse=True)


def _named_entities(question, names):
    return tuple(name for name in names if re.search(r'(?<![A-Za-z0-9])'+re.escape(name)+r'(?![A-Za-z0-9])',question,re.I))


def _check_explicit_entity_list(prefix,names):
    """An explicitly coordinated unknown target must not disappear.

    This is only a finite name-list check, not open-domain entity recognition.
    With a partially registered list, unexplained subject text is unverified.
    """
    if not _named_entities(prefix,names)or not re.search(r'和|与|及|、|\band\b|&',prefix,re.I):
        return
    head=re.split(r'各有|分别有|各自有|有多少|的专辑|的曲目|并(?:且)?|以及|同时',prefix,maxsplit=1)[0]
    for name in names:
        head=re.sub(re.escape(name),'',head,flags=re.I)
    head=re.sub(r'根据|依据|文档|资料|介绍|请问|乐队|艺术家|歌手|分别|各自|各|它们|这两支|这两个|的|和|与|及|、|\band\b|&|\s','',head,flags=re.I)
    if head.strip('，,：:()（）“”"「」'):
        raise ValueError('显式多实体名单中存在未能对应实际登记来源的对象，不能只回答其中已知对象。')


def _negated(clause, match):
    # Only a local negative request suppresses this obligation. A name alone,
    # unrelated preceding clause or a document quotation does not add a tool.
    prefix = clause[max(0, match.start() - 32):match.start()]
    return bool(re.search(r"(?:不要|无需|不用|不必|(?<!分)别)(?:再|去|额外)?[^，,；;。并但而只]{0,22}$", prefix))


def _set_selector(clause, count):
    """These demonstratives select an existing set; they do not ask its size."""
    return (count.group().startswith('几') and bool(re.search(
        r'(?:那|这|哪|某|上述|前述|关注的|提到的)\s*$',clause[:count.start()])))


def _numeric_entities(clause, clause_entities, whole_entities):
    # Only an explicit singular artist anaphor with one registered antecedent.
    # A bare generic numeric question does not inherit arbitrary artist names.
    if clause_entities:
        return clause_entities
    if len(whole_entities)==1 and re.search(
            r'(?:这位|该|这个|此)(?:\s*)(?:artist|艺术家|乐队|歌手)|\bthis\s+artist\b',clause,re.I):
        return whole_entities
    return (None,)


def request_obligations(question: str, *, documents=()) -> list[RequestObligation]:
    obligations = []
    names = _entity_names(documents)
    whole_entities = _named_entities(question, names)
    for clause in _clauses(question):
        if asks_definition_only(clause):
            continue
        clause_entities=_named_entities(clause,names)
        def add_count(obj):
            for entity in clause_entities or (None,):
                obligations.append(RequestObligation('database_quantity',clause,obj,entity))
        clause_quantity=False
        for count in re.finditer(_COUNT, clause, re.I):
            if _negated(clause,count) or _set_selector(clause,count):
                continue
            following=[]
            preceding=[]
            for obj, pattern in _COUNTS.items():
                # Count attaches to a nearby noun, not every noun occurring in
                # a multi-part clause ("band formed ... how many albums").
                for noun in re.finditer(pattern,clause,re.I):
                    if count.end()<=noun.start()<=count.end()+5:
                        following.append((noun.start()-count.end(),obj))
                    elif (noun.end()<=count.start()<=noun.end()+6
                          and not re.search(_AMOUNT,clause[noun.end():count.start()],re.I)
                          and not re.search(r'总额|金额',clause[noun.end():count.start()])):
                        preceding.append((count.start()-noun.end(),obj))
            closest=following or preceding
            if closest:
                add_count(min(closest)[1])
                clause_quantity=True
        for obj,pattern in _COUNTS.items():
            noun_count=re.search(r'(?:'+pattern+r')(?:的)?(?:数量|总数|首数|张数|人数|数)',clause,re.I)
            if noun_count and not _negated(clause,noun_count):
                add_count(obj)
                clause_quantity=True
        for kind, pattern in _FACTS.items():
            match = re.search(pattern, clause, re.I)
            if match and not _negated(clause, match):
                _check_explicit_entity_list(clause[:match.start()],names)
                entities = _named_entities(clause,names)
                if not entities and len(whole_entities)==1:
                    entities = whole_entities
                if not entities and len(whole_entities)>1:
                    if re.search(r'分别|各(?:自)?',clause):
                        entities=whole_entities
                    else:
                    # An unbound pronoun after several entities is not proof
                    # that any one named document covers all of them.
                        raise ValueError('多个实际登记实体的文档子问题未明确对应对象，完整性尚未核实。')
                for entity in entities or (None,):
                    detail=('people'if re.search(r'谁|哪些人|组建者|创始人|\bwho\b',clause,re.I)
                            else'date'if re.search(_FORMATION_DATE,clause,re.I)
                            else'background') if kind=='formation'else None
                    obligations.append(RequestObligation(kind, clause, entity=entity,fact_detail=detail))
        amount=re.search(_AMOUNT,clause,re.I)
        if (amount and not _negated(clause,amount)
                and re.search(_NUMERIC_REQUEST, clause,re.I)
                and not re.search(r"(?:定义|口径).{0,8}(?:是什么|如何解释|说明)$", clause)):
            for entity in _numeric_entities(clause,clause_entities,whole_entities):
                obligations.append(RequestObligation("database_amount",clause,entity=entity))
        measure=re.search(_SALES_MEASURE,clause,re.I)
        if (measure and not amount and not clause_quantity and not _negated(clause,measure)
                and re.search(_NUMERIC_REQUEST,clause,re.I)):
            for entity in _numeric_entities(clause,clause_entities,whole_entities):
                obligations.append(RequestObligation("database_measure",clause,entity=entity))
    return list(dict.fromkeys(obligations))


def clearly_database_question(question: str) -> bool:
    """Only positive database requests; selecting documents is not a request."""
    obligations = request_obligations(question)
    if any(o.kind in _FACTS for o in obligations):
        return False
    if any(o.kind.startswith("database_") for o in obligations):
        return True
    return bool(re.search(r"发票|销售额|销售金额|消费金额|购买数量|账单", question)
                and re.search(r"多少|统计|计算|求|汇总|排名|最高|最低|合计|总额", question)
                and not re.search(r"定义|口径|手册|资料|文档|正文|解释", question))


def asks_definition_only(question: str) -> bool:
    """Explain a formula is not authorization to calculate a database value."""
    if not re.search(r'手册|口径|定义|公式',question):
        return False
    if not re.search(r'怎么算|如何计算|计算方法|计算公式|公式是什么|定义是什么|什么定义|解释|说明',question):
        return False
    # A separate request for a real value/dimension is still a computation;
    # its missing period belongs to the existing clarification gate.
    calculation=re.sub(r'怎么算|如何计算|计算方法|计算公式','',question)
    return not bool(re.search(r'算一下|计算一下|求出|算出|计算.{0,18}(?:客户|美国|加拿大|销售额|发票|\d{4}\s*年)|\d{4}\s*年.{0,18}(?:客单价|金额)|客单价(?:数值|是多少)',calculation))


def explicit_new_task(question: str) -> bool:
    """A complete new query must not be captured by a bare ^按/^用 prefix.

    Short slot replies such as 按发票张数/按2024年 remain genuine resumes.
    A client-supplied card ID is checked separately and always takes priority.
    """
    return bool(re.search(r'统计|查询|列出|计算',question)
                and re.search(r'\d{4}\s*年',question)
                and clearly_database_question(question))


def _matches(obligation, question):
    if obligation.kind == "formation":
        if not re.search(r"成立|组建|创始人|\bformed\b|\bfounded\b|\bformation\b", question, re.I):
            return False
        detail={'people':r'谁|哪些人|组建者|创始人|\bwho\b|\bfounders?\b',
                'date':_FORMATION_DATE,
                'background':r'背景|经过|过程|\bbackground\b'}.get(obligation.fact_detail)
        return detail is None or bool(re.search(detail,question,re.I))
    if obligation.kind == "music_style":
        return bool(re.search(r"音乐风格|音乐类型|曲风|风格|(?<![a-z0-9_])(?:style|genre)(?![a-z0-9_])", question, re.I))
    proposed = request_obligations(question)
    if obligation.kind=='database_measure':
        # An unspecified sales measure asks for a numeric database result, not
        # an invented monetary default. A sale quantity is eligible, a catalog
        # album count is not. The SQL semantic gate still determines the metric.
        return any(p.kind in {'database_measure','database_amount'} or
                   (p.kind=='database_quantity' and re.search(
                       r'购买|卖出|售出|销售|销量|\b(?:sold|purchased|sales)\b',question,re.I))
                   for p in proposed)
    return any(p.kind == obligation.kind and p.object == obligation.object for p in proposed)


def _derived_artist_request(question):
    return bool(re.search(r'(?:最高|第一|冠军|最多).{0,10}(?:艺术家|乐队|歌手)|(?:艺术家|乐队|歌手).{0,12}(?:最高|第一|冠军|最多)',question))


def _actual_artist_refs(dependencies,outputs,documents,catalog=None):
    """Bounded lineage: physical artist PK/name projections and real rows.

    Direct, CTE and derived-table transparent columns are supported. Arithmetic,
    casts, constants, set operations and unrelated unused CTEs cannot establish
    identity. A step name or free-form model prose is not an entity binding.
    """
    registry={d['entity_ref'] for d in documents if (d.get('entity_ref')or'').startswith('chinook:artist:')}
    found=set()
    for dependency in dependencies:
        output=outputs.get(dependency)or{}
        if output.get('source')!='database'or output.get('status')!='SUCCEEDED':
            continue
        try:
            if catalog is not None:
                from qa_agent.sql.repair_guard import _qualified
                tree=_qualified(output.get('sql')or'',catalog)
            else:
                tree=sqlglot.parse_one(output.get('sql')or'',read='postgres')
            scope=build_scope(tree)
        except (sqlglot.errors.SqlglotError,ValueError):
            continue
        if not isinstance(tree,exp.Select)or not scope:
            continue
        if len({p.alias_or_name for p in tree.expressions})!=len(tree.expressions):
            continue
        def identity(node,owner,depth=0):
            if depth>12 or node is None:return None
            while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
            if not isinstance(node,exp.Column):return None
            selected=owner.selected_sources.get(node.table)
            if selected is None and not node.table and len(owner.selected_sources)==1:
                selected=next(iter(owner.selected_sources.values()))
            source=selected[1]if selected else None
            if isinstance(source,exp.Table):
                return node.name if(source.db or'public')=='public'and source.name=='artist'and node.name in{'name','artist_id'}else None
            if isinstance(source,Scope)and isinstance(source.expression,exp.Select):
                projections=[p for p in source.expression.expressions if p.alias_or_name==node.name]
                return identity(projections[0],source,depth+1)if len(projections)==1 else None
            return None
        keys={}
        for projection in tree.expressions:
            field=identity(projection,scope)
            if field:keys[field]=projection.alias_or_name
        # Chinook artist.name is not UNIQUE. Name coincidence cannot choose a
        # registered document for a different real artist with the same name.
        if 'artist_id'not in keys:
            continue
        for row in output.get('table')or[]:
            if not isinstance(row,dict):
                continue
            for ref in registry:
                parts=ref.split(':',3)
                matches=[]
                if len(parts)==4 and keys.get('artist_id')in row:
                    matches.append(str(row[keys['artist_id']])==parts[2])
                if len(parts)==4 and keys.get('name')in row:
                    matches.append(str(row[keys['name']]).casefold()==parts[3].casefold())
                if matches and all(matches):
                    found.add(ref)
    return found


def prove_obligation_coverage(question, plan, *, allowed_tools, outputs=None, documents=(),catalog=None):
    """Verify supported explicit obligations against actual plan/tool outputs.

    A fact needs a document/context step which actually asks that fact. A
    database numeric request needs a matching SQL step when SQL is authorized. Source
    restrictions remain upper bounds: this function cannot grant SQL or RAG.
    RAG correctness and literal citations are still checked by their own tool.
    """
    records = []
    documents = tuple(documents)
    doc_entities = {d.get('doc_id'):_entity_names([d]) for d in documents}
    for obligation in request_obligations(question,documents=documents):
        database_obligation = obligation.kind.startswith("database_")
        tools = ({"sql"} if database_obligation else {"doc", "context"}) & set(allowed_tools)
        # A body-only question can count facts in the body; it is not an
        # implicit request to query the similarly named database table.
        if database_obligation and "sql" not in allowed_tools:
            tools = {"context", "doc"} & set(allowed_tools)
        def entity_matches(step):
            if obligation.entity is None:
                if obligation.kind not in _FACTS:
                    return True
                if step.tool=='context':
                    return obligation.evidence in step.question or question in step.question
                # An unregistered named entity cannot be substituted by any
                # convenient registered artist document. Only a genuinely
                # requested SQL-selected artist can acquire its identity later.
                return (_derived_artist_request(question) and bool(step.depends_on)
                        and any(prior.step_id in step.depends_on and prior.tool=='sql'for prior in plan.steps))
            named = _named_entities(step.question,[obligation.entity])
            selected = {name for doc_id in step.doc_ids for name in doc_entities.get(doc_id,())}
            return bool(named or obligation.entity in selected)
        matches = [step for step in plan.steps if step.tool in tools and _matches(obligation, step.question) and entity_matches(step)]
        if not matches:
            raise ValueError("执行计划未覆盖原问题明确要求的" + obligation.kind + "，未将不完整计划交付为成功答案。")
        actual = []
        if outputs is not None:
            for step in matches:
                value = outputs.get(step.step_id)
                if not isinstance(value, dict):
                    continue
                expected = {"sql": "database", "doc": "documents", "context": "user_session_context"}[step.tool]
                if value.get("source") != expected:
                    continue
                if step.tool == "sql" and not value.get("sql"):
                    continue
                if step.tool == "doc" and value.get("status") == "SUCCEEDED" and not value.get("evidences"):
                    continue
                if step.tool == 'doc' and obligation.entity:
                    returned = {name for evidence in value.get('evidences',()) for name in doc_entities.get(evidence.get('doc_id'),())}
                    if obligation.entity not in returned and value.get('status')=='SUCCEEDED':
                        continue
                if step.tool=='doc'and obligation.kind in _FACTS and obligation.entity is None:
                    expected_refs=_actual_artist_refs(step.depends_on,outputs,documents,catalog)
                    returned_refs={d.get('entity_ref')for d in documents if any(e.get('doc_id')==d.get('doc_id')for e in value.get('evidences',()))}
                    if not expected_refs or not expected_refs<=returned_refs:
                        continue
                if step.tool == "context" and not value.get("quotes"):
                    continue
                actual.append(step.step_id)
            if not actual:
                raise ValueError("原问题要求的" + obligation.kind + "没有对应的真实工具证据，不能交付完整成功答案。")
        records.append({**obligation.public(), "planned_step_ids": [s.step_id for s in matches],
                        "actual_step_ids": actual if outputs is not None else None})
    return {"verified": True, "bounded_supported_obligations": records,
            "boundary": "Only explicit supported quantities, monetary/generic sales numeric requests and formation/music-style facts; generic measure does not select a metric. Not a general semantic proof."}
