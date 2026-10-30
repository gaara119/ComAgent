"""Project one SQL tool's role without replaying a planner's free conditions.

The count comes from the validated ToolPlan, never the model's free text. This
does not choose filters, periods, defaults or a confirmed semantic state.
"""
from copy import deepcopy


POLICY = 'single_SQL_purpose_only_v1'


def single_sql_step(context):
    return (isinstance(context, dict) and context.get('kind') == 'composed'
        and type(context.get('sql_step_count')) is int and context['sql_step_count'] == 1)


def tool_purpose(context, fallback):
    from qa_agent.sql.helper_identity import identity_lookup_role
    role=identity_lookup_role(context)
    if role:
        return role['tool_purpose']
    if not single_sql_step(context):
        return fallback
    if context.get('debut_identity_lookup') is True:
        return ('本步是程序核验的首专查证前置身份查询：只查原问艺术家的真实主键与名称，'
                '保留全部同名身份供后续文档核验；不查专辑/曲目，不聚合、不推断首专。'
                '本提示不授予任何期间、默认或执行权限，仍须独立身份查询校验。')
    return ('已验证计划只有一个SQL步骤：只完成真实原问中的数据库计算部分，'
            '文档事实由文档工具处理，实际前序结果及真实身份谓词须消费。'
            '期间、人数、筛选和默认不能从规划子问产生；以真实原问、正文和仍有效用户条件为准。'
            '不得直接执行文档SQL；首专由实际文档身份限定，不以编号或首行推断。')


def model_context(context):
    """Keep real evidence/guard fields; never mutate the audit/server context."""
    from qa_agent.sql.helper_identity import identity_lookup_role
    role=identity_lookup_role(context)
    if not single_sql_step(context) and not role:
        if isinstance(context,dict) and '_program_composed_plan' in context:
            return {k:v for k,v in context.items() if k!='_program_composed_plan'}
        return context
    result = deepcopy(context)
    result.pop('_program_composed_plan',None)
    step = result.get('sql_step')
    if isinstance(step, dict):
        result['sql_step'] = {k: v for k, v in step.items() if k != 'question'}
    delegated = result.get('delegated_document_steps')
    if isinstance(delegated, list):
        result['delegated_document_steps'] = [
            {k: v for k, v in item.items() if k != 'question'}
            if isinstance(item, dict) else item for item in delegated]
    result['instructions'] = tool_purpose(context, '')
    result['planner_context_policy'] = 'program_identity_preparation_scope_v1' if role else POLICY
    result['dependencies_authority'] = ('真实工具事实或定义，保留实际归属；'
        '依赖回答的自由解释不是用户期间、筛选或默认授权。')
    return result
