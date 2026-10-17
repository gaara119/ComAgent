"""Source obligations derived from the actual user request, never eval labels."""
from __future__ import annotations

import re


def definition_target(question: str) -> str | None:
    from qa_agent.fusion.obligations import asks_definition_only
    if asks_definition_only(question):
        return None
    if not re.search(r"手册|口径|定义", question):
        return None
    if not re.search(r"计算|算|多少|数量|人数|客户数|金额", question):
        return None
    # These are existing project metrics; this function does not define their
    # formula. The actual definition must still be retrieved and verified.
    match = re.search(r"复购客户(?:数)?|客单价|平均每张发票金额|平均每位客户金额", question)
    return match.group() if match else None


def normalize_definition_plan(question, plan, available, *, catalog=None):
    """Require definition -> SQL, keeping SQL dimensions in the DB catalog.

    A manual lacking a requested employee grouping does not negate a metric
    definition it actually contains. Do not ask the document tool to supply
    physical join mappings already owned by the authenticated SQL catalog.
    """
    target = definition_target(question)
    if not target:
        return _remove_unrequested_catalog_definition(question,plan,available,catalog=catalog)
    from qa_agent.fusion.composed import PlanStep, ToolPlan
    steps = [item.model_copy(deep=True) for item in plan.steps]
    sql_ids = {item.step_id for item in steps if item.tool == "sql"}
    manuals = [key for key, doc in available.items() if doc.get("entity_ref") == "chinook:business-metrics"]
    definition_steps = [item for item in steps if item.tool == "doc" and
        not (set(item.depends_on) & sql_ids) and
        ((len(item.doc_ids) == 1 and item.doc_ids[0] in manuals) or
         (not item.doc_ids and definition_target(item.question) == target))]
    changes = []
    if not definition_steps:
        # Select only an unambiguous registered manual, never guessed doc IDs.
        if len(manuals) != 1:
            raise ValueError("没有唯一可核验的指标口径手册，不能补出文档定义。")
        free = next((f"s{i}" for i in range(1,7) if f"s{i}" not in {item.step_id for item in steps}), None)
        if free is None:
            raise ValueError("计划已达到6步上限，不能遗漏必要定义。")
        definition_steps = [PlanStep(step_id=free, tool="doc", question=target + "的计算定义", doc_ids=manuals)]
        steps = definition_steps + steps
        changes.append("added_registered_metric_definition_step")
    for item in definition_steps:
        if not item.doc_ids:
            if len(manuals) != 1:
                raise ValueError("指标定义步骤缺少唯一允许的手册来源。")
            item.doc_ids = manuals
        item.question = (f"只依据本手册提取“{target}”的计算定义、统计对象、判定条件、期间规则和单位。"
                         "不要求手册提供员工/地区等数据库维度的关联；关联属于后续数据库目录。")
    all_sql_steps = [item for item in steps if item.tool == "sql"]
    definition_original_ids = {item.step_id for item in definition_steps}
    target_stem = target.removesuffix("数")
    sql_steps = [item for item in all_sql_steps if target_stem in item.question or
                 set(item.depends_on) & definition_original_ids]
    if len(all_sql_steps) == 1 and not sql_steps and not re.search(r"冠军|第一名|最高.*艺术家|最多.*乐队", all_sql_steps[0].question):
        sql_steps = all_sql_steps
    if not sql_steps:
        free = next((f"s{i}" for i in range(1,7) if f"s{i}" not in {item.step_id for item in steps}), None)
        if free is None:
            raise ValueError("计划已达到6步上限，不能遗漏必要计算。")
        metric_question = question
        if all_sql_steps:
            # An added metric node must not re-run an existing independent
            # champion lookup or a document introduction as its own SQL task.
            metric_question = re.split(r"(?:[，,；;。]\s*)?(?:并(?:且)?|再|另(?:外)?)\s*(?:介绍|讲讲|描述|查询冠军|查冠军)", question, maxsplit=1)[0].strip(" ，,；;。")
            if target_stem not in metric_question or metric_question == question:
                raise ValueError("复杂请求缺少独立的指标计算步骤，无法安全补出局部查询；请明确各子任务。")
        item = PlanStep(step_id=free, tool="sql", question=metric_question)
        steps.append(item)
        sql_steps = [item]
        changes.append("added_required_database_computation")
    # Reassign IDs through old object identity, so an inserted definition
    # cannot accidentally alias an existing s1 or leave dangling dependencies.
    original = [(item, list(item.depends_on)) for item in steps]
    old_to_new = {}
    for index, item in enumerate(steps, 1):
        old_to_new.setdefault(item.step_id, f"s{index}")
    identity_ids = {id(item): f"s{index}" for index, item in enumerate(steps, 1)}
    definition_ids = [identity_ids[id(item)] for item in definition_steps]
    for item, dependencies in original:
        item.step_id = identity_ids[id(item)]
        item.depends_on = list(dict.fromkeys(old_to_new.get(key, key) for key in dependencies))
        if item in sql_steps:
            item.depends_on = list(dict.fromkeys(item.depends_on + definition_ids))
            # Preserve the complete user's dimensions, time and return shape;
            # no planner paraphrase may erase them.
            if len(all_sql_steps) <= 1 and item in all_sql_steps or not all_sql_steps:
                # For the ordinary single-calculation request preserve its full
                # dimensions. Other SQL nodes keep their own atomic task.
                item.question = question
    # Put the required definition before SQL. A larger unknown cyclic plan is
    # rejected by ToolPlan rather than silently stripping dependencies.
    ordered = definition_steps + [item for item in steps if item not in definition_steps]
    final_ids = {item.step_id: f"s{index}" for index, item in enumerate(ordered, 1)}
    for item in ordered:
        old_id = item.step_id
        item.depends_on = [final_ids[key] for key in item.depends_on]
        item.step_id = final_ids[old_id]
    return ToolPlan.model_validate({"steps": [item.model_dump() for item in ordered]}), changes + ["definition_scope_separated_from_database_dimensions"]


def _remove_unrequested_catalog_definition(question,plan,available,*,catalog=None):
    """Do not make an ordinary catalog query depend on an invented manual.

    Only a root definition/dictionary lookup in the registered metric manual
    may be removed. Explicit document/definition requests and entity facts
    remain obligations. No document facts or SQL values are inferred here.
    """
    if re.search(r'手册|口径|定义|资料|文档|政策|标准|规则|依据|计算方法|怎么算|如何计算|什么意思|含义|何谓',question):
        return plan,[]
    if catalog is None:return plan,[]
    # This optimization is bounded to an original, independently meaningful
    # count clause with a real catalog PK. Unknown measures such as net profit
    # are never made executable by removing their missing definition.
    targets={'专辑':('album','album_id'),'曲目':('track','track_id'),
             '客户':('customer','customer_id'),'发票':('invoice','invoice_id'),
             '员工':('employee','employee_id'),'歌单':('playlist','playlist_id'),
             '艺术家':('artist','artist_id')}
    count_pattern=r'(?:多少|几)(?:张|首|位|名|个)?('+ '|'.join(targets)+r')'
    clauses=[part.strip()for part in re.split(r'[？?！!。；;]',question)if part.strip()]
    counts=[part for part in clauses if re.search(count_pattern,part)]
    if len(counts)!=1:return plan,[]
    if any(part!=counts[0] and not re.search(r'成立|组建|音乐风格|名人堂',part)for part in clauses):return plan,[]
    target=re.search(count_pattern,counts[0]).group(1)
    table_name,key=targets[target]
    try:
        table=catalog.get_table(table_name,'public')
        if key not in table.column_names or table.primary_key!=(key,):return plan,[]
    except Exception:return plan,[]
    removable=set()
    rewrites=set()
    for item in plan.steps:
        if item.tool!='doc' or item.depends_on or not item.doc_ids:continue
        if not re.search(r'定义|口径|公式|数据字典|表列|字段映射',item.question):continue
        if not all(doc_id in available and available[doc_id].get('entity_ref')=='chinook:business-metrics'
                   for doc_id in item.doc_ids):continue
        children=[step for step in plan.steps if item.step_id in step.depends_on]
        if len(children)==1 and children[0].tool=='sql' and target in children[0].question:
            removable.add(item.step_id)
            rewrites.add(children[0].step_id)
    if not removable:return plan,[]
    from qa_agent.fusion.composed import ToolPlan
    remaining=[item.model_copy(deep=True)for item in plan.steps if item.step_id not in removable]
    remap={item.step_id:f's{index}'for index,item in enumerate(remaining,1)}
    for item in remaining:
        item.depends_on=[remap[key]for key in item.depends_on if key not in removable]
        if item.step_id in rewrites:item.question=counts[0]+'？'
        item.step_id=remap[item.step_id]
    return ToolPlan(steps=remaining),['removed_unrequested_metric_dictionary_dependency',
        'restored_original_catalog_count_clause']
