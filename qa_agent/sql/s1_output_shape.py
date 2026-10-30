"""A bounded S1 SQL-tool result shape, never a semantic/default certificate.

Only literal column counts and closed scalar requests are supported. The latter
require an independent, context-free question. Grouped/multipart/ambiguous tasks
are not inferred. Generated SQL is not edited; bounded existing repair handles
a mismatch. Business review and the original raw comparator remain separate.
"""
from hashlib import sha256
import re
import unicodedata

import sqlglot
from sqlglot import exp

from qa_agent.sql.validator import SQLValidationError


def requested_shape(question, *, brief='', has_history=False, composed=False):
    if not isinstance(question, str) or not question.strip() or composed:
        return None
    text = unicodedata.normalize('NFKC', question)
    if re.search(r"例如|比如|示例|举例|假设|如果|不要|不只|不单|别只|不能只|并非|[“”\"'‘’「」『』]", text):
        return None
    # Asking which of two objects is larger and by how much does not specify
    # a projection layout. Winner+difference and operands+difference may both
    # answer it; only an explicit user column count can constrain their width.
    if len(re.findall(r'[?？]', text)) > 1 or re.search(r'另外|此外|顺便|同时再|另给|再给|并(?:告诉|给|列|输出|返回)|折合|折算|[;；]|呢[?？]?', text):
        return None
    explicit = re.search(r'(?:只(?:要|输出|返回)|仅(?:输出|返回))\s*(?P<n>[1-6一二两三四五六])\s*(?:个)?(?:列|字段)', text)
    numbers = {'一':1,'二':2,'两':2,'三':3,'四':4,'五':5,'六':6}
    if explicit:
        counts = [numbers.get(value) or int(value) for value in
                  re.findall(r'([1-6一二两三四五六])\s*(?:个)?(?:列|字段)', text)]
        if len(set(counts)) != 1 or re.search(r'或者|或许|也可以|均可|任选|不限', text):
            return None
        width = numbers.get(explicit['n']) or int(explicit['n'])
        return _requirement(question, 'literal_column_count', width, False, explicit[0])
    # A persistent display rule or a continuing question may require additional
    # fields not repeated in this turn. Do not infer its output shape here.
    if brief.strip() or has_history:
        return None
    # A comma-separated delivery request is an additional output obligation,
    # even without an additive word such as "并". Do not turn a count/total
    # question with "给出姓名" into a one-column scalar that deletes the name.
    if re.search(r'[，,]\s*(?:请|也|还|同时)?\s*(?:给(?:出|我)|返回|显示|展示|输出|附(?:上|带)|提供)', text):
        return None
    extreme_gap = re.search(r'最高.{0,16}(?:比|与|和)最低.{0,16}(?:多|差).{0,10}多少', text)
    if extreme_gap and not re.search(r'分别|每|逐|分组|各|以及|列出|名单|同时|另外', text):
        return _requirement(question, 'single_extreme_difference', 1, True, extreme_gap[0])
    # A two-period extreme difference asks for the difference itself. It
    # does not request extra operands and says nothing about a signed value.
    if (re.search(r'(?:最大|最高|最小|最低).{0,18}(?:比|与|和).{0,28}(?:最大|最高|最小|最低).{0,14}(?:多|少|差).{0,8}(?:多少钱|多少)', text)
            and not re.search(r'分别|每|逐|分组|各|以及|列出|名单|同时|另外|两边|两项|各自', text)):
        return _requirement(question, 'single_period_extreme_difference', 1, True, text)
    if (len(re.findall(r'[?？]', text)) > 1
            or re.search(r'分别|同时|另外|此外|并且|以及|顺便|逐|每|各|名单|列表|列出|分组|按月|按年|按国|哪(?:个|位|些|张|首)|是谁|谁的|换算|两种|多种|(?:前|top\s*)\d', text, re.I)):
        return None
    rank = r'第\s*(?:\d+|[一二两三四五六七八九十]+)\s*(?:名|位)?'
    rank_gap = re.search(rank + r'.{0,48}' + rank + r'.{0,24}(?:差|多|少).{0,12}(?:多少钱|多少|几元)', text)
    if not rank_gap:
        rank_gap = re.search(rank + r'.{0,24}(?:比|与|和)' + rank + r'.{0,16}(?:多|少|差).{0,12}(?:多少钱|多少|几元)', text)
    if not rank_gap:
        rank_gap = re.search(r'(?:花钱|消费|金额|销售额)最多的.{0,8}(?:比|与|和)' + rank
            + r'.{0,16}(?:多|少|差).{0,12}(?:多少钱|多少|几元)', text)
    if rank_gap:
        return _requirement(question, 'single_rank_difference', 1, True, rank_gap[0])
    # Only a closed fraction without any requested identities, group/list,
    # additional measure, explicit percent, or precision convention.
    if (re.search(r'占.{0,8}(?:多大|多少)?比例|占比', text)
            and not re.search(r'百分|%|每百|千分|万分|‰|100|小数|保留|精度|四舍五入|公式|以及|同时|另外|各自|各占|分别|谁|哪|名单|列出|各有|多少钱', text)):
        return _requirement(question, 'single_raw_fraction', 1, True, text)
    # Outside the narrow rank-difference pattern, coordination or a ratio can
    # contain several measures. A matching word such as '总额' is insufficient.
    if re.search(r'和|与|及|、|占|比例|百分|比率|率|%', text):
        return None
    if ((re.search(r'总时长|时长加起来|总播放时长|总存储|存储空间', text)
            or re.search(r'所有.{0,12}(?:曲子|曲目|歌曲).{0,14}(?:连起来|连续).{0,10}(?:放|播)', text))
            and re.search(r'一共|总共|总计|合计|加起来|多少|多长|多大', text)):
        return _requirement(question, 'single_total_measure', 1, True, text)
    if (re.search(r'总数|总金额|总销售额|发票总额|消费总额|共(?:有)?多少|一共(?:有)?几|总共(?:有)?几', text)
            and re.search(r'多少|几(?:人|位|张|首|条|个|名)|多少钱', text)):
        return _requirement(question, 'single_total_or_count', 1, True, text)
    return None


def _requirement(question, kind, width, single_row, quote):
    start = question.find(quote)
    # NFKC may alter glyphs; retain the full actual original in that case.
    if start < 0:
        quote = question; start = 0
    return {'policy':'s1_source_output_shape_v1', 'kind':kind, 'width':width,
        'single_row':single_row, 'source':{'quote':quote, 'start':start,
            'end':start+len(quote), 'sha256':sha256(question.encode()).hexdigest()},
        'authority':'declared_SQL_tool_result_shape_not_business_semantic_certificate',
        'business_correctness_asserted':False, 'state_committed':False}


def _deny(requirement, actual):
    error = SQLValidationError('①SQL结果结构约定：本轮只需'
        f"{requirement['width']}列" + ('、一行标量' if requirement['single_row'] and requirement['width'] == 1 else '、一行' if requirement['single_row'] else '')
        + '；去掉未要求的身份、排行、单位换算或常量显示列，保留全部原筛选、聚合人口、指标及单位。'
        + ('本轮无正文或历史展示约定，未要求百分数或精度，单一比例保留原始未舍入分数，不乘100。'
           if requirement['kind'] == 'single_raw_fraction' else '')
        + '这只是返回结构修复，不得为匹配结果改条件或数值。')
    error.output_shape_evidence = {'requirement':requirement, 'actual':actual}
    raise error


def validate_projection(sql, requirement):
    if requirement is None:
        return {'status':'not_verified','reason':'no_closed_source_output_shape','business_correctness_asserted':False}
    tree = sqlglot.parse_one(sql, read='postgres')
    if not isinstance(tree, exp.Select) or any(item.find(exp.Star) is not None for item in tree.expressions):
        return {'status':'not_verified','reason':'unknown_projection_shape','business_correctness_asserted':False}
    if len(tree.expressions) != requirement['width']:
        _deny(requirement, {'projection_width':len(tree.expressions)})
    return {'status':'verified_output_structure_only', 'requirement':requirement,
        'projection_width':len(tree.expressions), 'business_correctness_asserted':False}


def validate_result(columns, table, requirement):
    if requirement is None:
        return
    if len(columns) != requirement['width'] or requirement['single_row'] and len(table) != 1:
        _deny(requirement, {'actual_columns':len(columns),'actual_rows':len(table)})


def validate_source_fraction(sql, question, *, brief='', has_history=False, composed=False):
    """Bounded implementation of the declared raw-fraction SQL-tool policy.

    This checks a visible final scalar arithmetic form, never the denominator,
    population or business metric. Context or an explicit display instruction
    makes this policy inapplicable; unknown expressions receive no certificate.
    """
    no = {'status':'not_verified','business_correctness_asserted':False}
    if not isinstance(question,str) or brief.strip() or has_history or composed:
        return no
    text=unicodedata.normalize('NFKC',question)
    if (not re.search(r'占比|比例',text)
            or re.search(r'百分|%|每百|千分|万分|‰|100|小数|保留|精度|四舍五入|乘|倍|公式|例如|比如|示例|假设|假如|如果|不要|不需要|不计算|不算|无需|不用|不必|只解释|仅解释|只说明|并非|[“”"\x27‘’「」]|percent|round',text,re.I)):
        return no
    try:
        tree=sqlglot.parse_one(sql,read='postgres')
        if not isinstance(tree,exp.Select) or len(tree.expressions)!=1:
            return no
        rounded=False
        def un(node):
            nonlocal rounded
            while isinstance(node,(exp.Alias,exp.Paren,exp.Cast,exp.Round)):
                rounded=rounded or isinstance(node,exp.Round)
                node=node.this
            return node
        def hundred(node):
            node=un(node)
            return isinstance(node,exp.Literal) and not node.is_string and float(node.this)==100
        node=un(tree.expressions[0]);scale100=False
        if isinstance(node,exp.Mul):
            if hundred(node.this):node=un(node.expression);scale100=True
            elif hundred(node.expression):node=un(node.this);scale100=True
            else:return no
        if not isinstance(node,exp.Div):return no
        numerator=un(node.this)
        if isinstance(numerator,exp.Mul):
            if hundred(numerator.this) or hundred(numerator.expression):scale100=True
            else:return no
        if not scale100 and not rounded:
            return no  # Absence of this visible conflict proves no semantics.
    except (ValueError,TypeError,sqlglot.errors.ParseError):
        return no
    error=SQLValidationError('①SQL工具原始比例结构：实际本轮仅问占比/比例，未指定百分数或小数位，'
        '且没有正文或历史展示约定。SQL保留未舍入的原始分数，不乘100、不在最终比例外自行ROUND；'
        '只修展示尺度，保留原分子、分母、期间、人口、筛选及NULL语义，不改成金额或计数。')
    error.output_shape_evidence={'policy':'declared_S1_raw_fraction_without_display_instruction',
        'source':{'quote':question,'sha256':sha256(question.encode()).hexdigest()},
        'visible_times100':scale100,'visible_round':rounded,
        'business_correctness_asserted':False}
    raise error
