"""Write DEV-only SQL and four-metric AI pre-audit reports in new audit dirs.

The semantic findings below are authored for each development question. SQL
execution equality is supporting evidence, not the semantic decision rule.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = Path(__file__).resolve().parent
REPORT = ROOT / "eval/reports/d2-ai-preaudit"
PASS = "AI建议通过"
CONDITIONAL = "AI建议有条件通过"
ERROR = "AI发现错误"
INSUFFICIENT = "证据不足"

# Each reason evaluates the question independently from the EX comparison.
SEMANTICS = {
    "sql-01": "对象为客户表全体记录，customer_id 是非空主键；COUNT(*) 每客户计一次，不受其他可空列影响，不加期间或国家过滤。参考结果为59位。",
    "sql-02": "“来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。",
    "sql-04": "客户国家Brazil筛选，投影customer_id、first_name、last_name、city四列，名字和姓氏分开；customer_id主键升序能确定全部5行次序。",
    "sql-05": "美国映射真实值USA，筛选customer.country；只返回customer_id、city、state，客户编号升序；13行中state按原值返回，没有把城市或账单地区混入客户字段。",
    "sql-06": "比较track.unit_price > 0.99是严格大于，属于目录单价，不能用发票总额；按track_id升序再LIMIT 10，准确返回首10行编号、名称、单价。数据未声明币种。",
    "sql-07": "员工职位字段employee.title精确筛选Sales Support Agent；返回employee_id、first_name、last_name且编号升序，对应3名员工，没有拼接fullname。",
    "sql-09": "题目明确“全部发票”，对invoice.total在发票粒度SUM，不连接invoice_line导致重复金额，不增加默认期间、支付状态或币种。参考总额2328.60（数据库金额单位）。",
    "sql-10": "题目明确全部曲目及毫秒，AVG(track.milliseconds)为每条曲目等权平均，没有除1000转秒或按销售数量加权；milliseconds非空，结果393599.212103910933毫秒。",
    "sql-11": "题目要求发票平均总额与两位小数，ROUND(AVG(invoice.total),2)先按每张发票平均再四舍五入；不是按购买客户均额。参考5.65，数据未声明货币名称。",
    "sql-13": "按customer.country分组COUNT(*)统计客户数，主排序客户数降序、次排序国家名升序；24个国家组完整，数量相等时已有次排序，不将客户国家替换为账单国家。",
    "sql-14": "按track.genre_id分组COUNT(*)统计曲目条数，数量降序、genre_id升序；genre_id可NULL但当前快照NULL数为0，SQL不会擅自删除NULL组。25组完整。",
    "sql-15": "题目明确发票账单国家，字段invoice.billing_country；在invoice粒度SUM(total)，金额降序、国家名升序，24组完整且并列次序确定。不能因当前客户地区与账单地区一致而替换字段。",
    "sql-17": "最长5首按非空track.milliseconds降序，track_id升序作并列规则，然后LIMIT 5；只返回track_id、name、milliseconds，保留毫秒单位。",
    "sql-18": "最高5张发票按invoice.total降序、invoice_id升序确定并列，再LIMIT 5；21.86并列的96和194号先后正确，金额是发票总额。",
    "sql-19": "客户last_name按数据库当前文本排序规则降序，再customer_id升序并列，LIMIT 5；投影编号、first_name、last_name，未误用first_name排序或fullname。",
    "sql-21": "2021年依据invoice.invoice_date，范围[2021-01-01,2022-01-01)，再按invoice_id升序LIMIT 10；返回编号、原始日期和总额，未混用客户创建日期或最近10张。",
    "sql-22": "入职时间取employee.hire_date，严格早于2004-01-01；名字明确仅first_name，不含last_name/fullname；按employee_id升序返回6行，当前hire_date无NULL。",
    "sql-24": "邮箱以@gmail.com结尾用LIKE '%@gmail.com'，不是包含gmail.com或错用公司名；题目名字明确仅first_name，返回编号、first_name、email并按编号升序，8行完整。",
    "sql-26": "题目明确定义company为NULL，使用IS NULL而非等于NULL、空串或COUNT(company)；COUNT(*)得到49位，实库company空字符串为0，未改变NULL语义。",
    "sql-27": "缺少作曲者明确定义composer IS NULL；按track_id升序再LIMIT 10，返回编号和名称，既不将NULL与空串混同，也不把作曲者名称误当艺术家字段。",
    "sql-29": "原值Antarctica在customer.country实际值中不存在，仍保留精确筛选，不猜测其他国家；返回所要求的编号、first_name、last_name及编号排序，空列表表示没有匹配客户，不是标量0或NULL。",
    "sql-31": "客户所在国家Italy精确匹配customer.country；COUNT(*)得到1位，未改用invoice账单国家或新增日期条件。",
    "sql-32": "客户所在国家Canada精确匹配customer.country；COUNT(*)得到8位，区分客户国家与账单国家，未新增发票期间。",
    "sql-33": "题目明确账单国家Canada，筛选invoice.billing_country而非customer.country；SUM(invoice.total)统计全部匹配发票，结果303.96（数据库金额单位），不做明细JOIN重复计额。",
    "sql-34": "最短时长取MIN(track.milliseconds)，milliseconds非空，得到1071毫秒；题目只要最短值，标量聚合正确，无需返回任意一首同长曲目的姓名或编号。",
    "sql-35": "最高目录单价取MAX(track.unit_price)，非空numeric列得到1.99；不把发票总额或明细实际成交价当曲目目录单价，也不推断美元/人民币。",
    "sql-36": "按invoice.billing_city分组COUNT(*)统计发票条数，数量降序、城市名升序，再LIMIT 10；数量14及7的并列均按城市升序，未使用客户城市或销售金额。",
    "sql-37": "按track.media_type_id分组统计曲目条数，媒体类型编号升序；5种媒体类型完整，统计不是流派或媒体文件字节和。",
    "sql-38": "对象为文件字节数最大的3首曲目，字段track.bytes单位字节，排序bytes降序、track_id升序再LIMIT 3，投影编号、名称、字节数。当前bytes为NULL的行数为0，结果与当前题意一致；但bytes在schema可NULL，而PostgreSQL DESC默认NULLS FIRST，未知大小会排在真实最大值之前。需明确本题仅针对无NULL的固定快照，或补充非NULL筛选/NULLS LAST规则后再确认一般语义。",
    "sql-39": "2023年开票数以invoice.invoice_date范围[2023-01-01,2024-01-01)过滤，再COUNT(*)；实库2023年83张，与当前日期无关，不把发票行数当发票数。",
    "sql-40": "题目给定起日含、止日不含，invoice_date >=2022-07-01且<2022-10-01准确实现半开区间；SUM(invoice.total)得到111.87（数据库金额单位），未扩大到全年或改用付款日期。",
    "sql-41": "艺术家名称以The开头且区分大小写，用artist.name LIKE 'The%'而非ILIKE或包含The；按artist_id升序再LIMIT 8，投影编号和名称，空name不匹配。",
    "sql-42": "艺术家artist.name恰好为U2用等号，不用模糊/包含匹配；编号升序返回150号U2，没有将艺术家名称误作专辑/曲目名称。",
    "sql-43": "题目将未填写州信息明确定义state IS NULL，COUNT(*)为29位；不等同空字符串、未知州名，且没有误用invoice.billing_state。",
    "sql-44": "明确保留Wakanda原值，country = 'Wakanda'在实库无匹配；COUNT(*)自然返回0，未纠错到真实国家、未返回空列表或NULL。",
}
VARIANTS = {
    "robust-01": "“巴稀”在国家语境是“巴西”的单字错写，指向Brazil；除错字外查询对象和计数口径未变化。",
    "robust-02": "“美囯”是“美国”的字形错写，指向USA；编号、城市、州投影与升序保持不变。",
    "robust-03": "Sales Suport Agent缺少一个p，实库employee.title真实值Sales Support Agent可唯一支持职位纠错；不新增岗位或员工范围。",
    "robust-06": "“老美”在来自某国家的客户语境为美国俗称USA，仍查询客户所在国家；没有把俗称扩张为北美或其他地区。",
    "robust-07": "意大利为Italy的中文国家名称；译名不改变customer.country计数条件。",
    "robust-08": "加拿大为Canada的中文国家名称；译名不改变customer.country计数条件。",
    "robust-11": "ba xi按国家语境读作“巴西”，保留Brazil客户计数；未增加时间、国家并集或账单条件。",
    "robust-12": "yi da li按国家语境读作“意大利”，保留Italy客户计数；未因候选相似度将其改成India。",
    "robust-13": "jia na da按国家语境读作“加拿大”，保留Canada客户计数；国家对象明确，发音变体未增加题意歧义。",
    "robust-16": "中英混合显式给出country、Brazil、customer，查询customer.country='Brazil'的人数，语义与基题一致。",
    "robust-17": "中英混合显式给出USA、customer_id/city/state及customer_id升序，字段与排序要求未改变。",
    "robust-18": "中英混合显式要求全部invoice的total求和，即发票粒度SUM(total)，没有新增指标或期间。",
    "robust-19": "显式给出billing_country=Canada、invoice及total，保留发票账单国家字段和全量SUM口径，不借当前地区值一致替换customer.country。",
    "robust-21": "“客户表”“一共几个人”明确指客户记录总数，COUNT(*)口径不变。",
    "robust-22": "“帮我数数/几位呀”只是请求语气，巴西客户国家筛选及人数计数均未变化。",
    "robust-23": "基题明确“全部曲目”，变体改为“这批曲目”引入未定义的指代范围；原始请求是该单条消息，scope仅指数据库，已有证据没有提供曲目批次或集合。gold直接AVG全track只在“这批=全库曲目”另行确认时成立，不能用base_id或EX相同替代用户范围证据。",
    "robust-24": "“曲目里最短的一首有几毫秒呀”请求最短时长值，语气变化不引入期间、销量或指定曲目集合；MIN(milliseconds)与基题一致。",
    "robust-26": "“你好/请帮忙/谢谢”属于礼貌冗词，来自巴西的客户人数条件完整且与基题一致，没有新增约束。",
    "robust-27": "礼貌冗词之外明确重申company为NULL，仍用IS NULL统计客户，不将NULL变成空串。",
    "robust-28": "礼貌冗词之外保留2023年开票数量，半开年度范围及COUNT(*)均不变。",
    "robust-29": "礼貌冗词之外保留客户国家Wakanda、原值保护和无匹配返回0，COUNT(*)口径不变。",
}


def evidence(path, *, line=None, section=None, note=None):
    item = {"path": path}
    if line is not None:
        item["line"] = line
    if section is not None:
        item["section"] = section
    if note is not None:
        item["note"] = note
    return item


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT / "eval/reports/d2-acceptance/unified-review.json").read_text(encoding="utf-8"))
    rows = [r for r in data["rows"] if r.get("group") in {"nl2sql", "robust"} and r.get("split") == "dev"]
    metric_rows = [r for r in data["rows"] if r.get("group") == "metric"]
    verification = [json.loads(line) for line in (ART / "sql-verification.jsonl").read_text(encoding="utf-8").splitlines()]
    query_index = {(r["review_id"], r["object"]): (line, r) for line, r in enumerate(verification, 1)}
    summary = json.loads((ART / "sql-verification-summary.json").read_text(encoding="utf-8"))
    assert not summary["errors"] and not summary["failed_value_comparisons"]
    assert summary["query_count"] == summary["expected_query_count"] == 130
    originals = {}
    gold_sources = {}
    gold_source_checks = []
    for group in ("nl2sql", "robust"):
        path = ROOT / f"eval/artifacts/d2/{group}/final/responses.jsonl"
        originals[group] = {}
        for line, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            item = json.loads(text)
            if item["split"] == "dev":
                originals[group][item["id"]] = (line, item)
        dataset_path = ROOT / ("eval/datasets/nl2sql_chinook_d2.jsonl" if group == "nl2sql" else "eval/datasets/robust.jsonl")
        gold_sources[group] = {}
        for line, text in enumerate(dataset_path.read_text(encoding="utf-8").splitlines(), 1):
            item = json.loads(text)
            if item["split"] == "dev":
                gold_sources[group][item["id"]] = (dataset_path.relative_to(ROOT).as_posix(), line, item)
    reviews = []
    for row in rows:
        group, ident = row["group"], row["id"]
        ref, actual = row["expected"], row["actual"]
        gold_path, gold_line, gold = gold_sources[group][ident]
        gold_checks = {key: gold.get(key) == ref.get(key) for key in
                       ("gold_sql", "gold_result", "gold_columns", "column_types", "ordered", "monetary_columns", "integer_columns", "expected_status", "base_id", "variant_type")}
        gold_checks["question"] = gold["question"] == row["title"]
        assert all(gold_checks.values()), row["review_id"]
        gold_source_checks.append({"review_id": row["review_id"], "path": gold_path, "line": gold_line, "dev_only": True, "checks": gold_checks})
        base = ident if group == "nl2sql" else ref["base_id"]
        reason = SEMANTICS[base]
        if group == "robust":
            if ident == "robust-23":
                reason = "基题明确全部曲目及毫秒，基题对应的全库AVG(track.milliseconds)为每条曲目等权平均，没有除1000转秒或按销售数量加权；milliseconds非空，基题的全库结果为393599.212103910933毫秒。该全库结果不能独立证明变体中未定义的“这批”范围。"
            reason = VARIANTS[ident] + " " + reason
        ref_status = CONDITIONAL if ident in {"sql-38", "robust-23"} else PASS
        actual_status = INSUFFICIENT if ident == "robust-23" else CONDITIONAL if ident == "sql-38" else PASS
        source_line, original = originals[group][ident]
        response = original["response"]
        ref_line, ref_verify = query_index[(row["review_id"], "reference")]
        actual_line, actual_verify = query_index[(row["review_id"], "actual")]
        n = len(actual["table"])
        faithful = ""
        if n == 1 and len(actual["table"][0]) == 1:
            value = next(iter(actual["table"][0].values()))
            faithful = f"原自然语言“{actual['answer']}”准确陈述标量{value}，没有补造币种、期间或支付含义。"
        elif n == 0:
            faithful = f"原自然语言“{actual['answer']}”正确说明原条件无记录，没有将空列表当作NULL聚合或零值。"
        else:
            faithful = f"原自然语言“{actual['answer']}”与结果表{n}行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。"
        actual_reason = "已有系统SQL的字段、过滤、聚合和排序与上述题意相符。" + faithful + " 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。"
        if "LIMIT 200" in actual["sql"].upper():
            actual_reason += f" 默认LIMIT 200在本快照仅返回{n}行且未截断，本次建议限于已有快照及输出。"
        if ident == "sql-38":
            actual_reason = "已有SQL和结果在当前bytes无NULL快照下满足最大字节数3首、字节单位、bytes降序和track_id并列升序；自然语言及3行表忠实。actual同样缺少NULLS LAST/bytes IS NOT NULL，故当前值正确而可空字段的一般排序语义需条件确认。"
        if ident == "robust-23":
            actual_reason = "已有SQL、数值393599.212103910933和自然语言确实对应全库track平均毫秒；但系统未澄清“这批”指哪个集合，也未在intent.assumptions中声明全集假设。缺少范围证据，不能确定全库平均是否回答了用户请求，即使gold和EX相同也暂不能判定正确。"
        issues = []
        suggestion = "保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。"
        confirmation = "待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。"
        if ident == "sql-38":
            issues = [{"object": obj, "problem": "track.bytes可NULL且ORDER BY bytes DESC默认NULLS FIRST，缺少未知文件大小处理规则；现存NULL=0，未发现本次实际三行值错误。", "severity": "conditional"} for obj in ("reference", "actual")]
            suggestion = "人工决定最大字节数排行是否仅针对当前无NULL快照，或应规定排除NULL/NULLS LAST；仅提出修订建议，不改gold或系统SQL。"
            confirmation = "需要确认bytes为NULL时的排行规则，以及本题验收是否限定当前无NULL快照。"
        if ident == "robust-23":
            issues = [{"object": "question", "problem": "“全部”改成“这批”新增无前文的指代范围，鲁棒变体未严格保持基题范围。", "severity": "conditional"},
                      {"object": "reference", "problem": "AVG全表是未声明的全集假设；只有确认“这批=全部曲目”后参考才可接受。", "severity": "conditional"},
                      {"object": "actual", "problem": "范围不明仍直接全表AVG，原输出缺少范围澄清，最终正确性证据不足。", "severity": "insufficient_evidence"}]
            suggestion = "人工确认指代集合；若目标为保持基题语义，应将变体范围说清楚，或补充合法上下文再独立核对。不能通过改参考平均值来使系统过关。"
            confirmation = "需要确认“这批”具体指哪些曲目；该确认到位前，实际回答暂不能确定。"
        if ident == "robust-13":
            issues.append({"object": "nlu_trace", "problem": "原NLU把jia na da标为unmatched且bindings为空，但后续已有SQL筛选Canada。最终国家值和计数正确，本次不能据此宣称NLU绑定阶段完成了拼音对齐。", "severity": "informational"})
            actual_reason += " 原值链接trace显示unmatched/无bindings，最终SQL仍正确采用Canada；结果正确性与值链接阶段成功应分开记录。"
            suggestion += " 若评估特定NLU阶段，人工应单独确认拼音对齐由哪一步完成；不改变最终答案建议。"
        if ident == "robust-26":
            issues.append({"object": "rewrite", "problem": "原mention跨度[4,13]包含“帮忙查一下来自巴西”，整体替换Brazil后改写为“你好，请Brazil的客户有多少位，谢谢。”，吞掉了请求词与来自关系。最终已有SQL仍筛选customer.country=Brazil且结果5位正确。", "severity": "rewrite_quality"})
            actual_reason += " 中间rewritten_question吞掉请求词，单独标记改写质量问题；最终SQL仍保留客户国家Brazil的条件和5位计数，不能因此误判最终答案错误。"
            suggestion += " 人工单独核对改写跨度及语句通顺程度；保留最终输出正确性的独立判断。"
        ev = [evidence("eval/reports/d2-acceptance/unified-review.json", section=row["review_id"], note="仅dev题干、参考和已有输出"),
              evidence(gold_path, line=gold_line, note="原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致"),
              evidence(f"eval/artifacts/d2/{group}/final/responses.jsonl", line=source_line, note="原请求、SQL、结果表、答案、intent和步骤"),
              evidence("eval/artifacts/d2-ai-preaudit/sql-verification.jsonl", line=ref_line, note="重执行已有参考SELECT，真实结果与耗时"),
              evidence("eval/artifacts/d2-ai-preaudit/sql-verification.jsonl", line=actual_line, note="重执行已有系统SELECT，真实结果与耗时"),
              evidence("eval/artifacts/d2-ai-preaudit/database-materials.json", section="schema; row_counts; text_values", note="真实字段/可空性/英文值，不以别名候选本身证明题意"),
              evidence("data/catalog/chinook.yaml", section="tables", note="结构、外键、字段含义与单位"),
              evidence("data/rules/metric_definitions.json", section="general; metrics", note="已确认项目口径、半开期间、金额单位及NULL规则")]
        if group == "robust":
            ev.append(evidence("eval/reports/d2-acceptance/unified-review.json", section="nl2sql:" + base, note="基题也属于dev；逐项对照变体是否改变题意"))
        for key in ("nullable-columns", "postgres-desc-null-order") if ident == "sql-38" else ():
            line, _ = query_index[("supplemental:" + key, "audit_select")]
            ev.append(evidence("eval/artifacts/d2-ai-preaudit/sql-verification.jsonl", line=line, note=key))
        common = {
            "review_id": row["review_id"], "id": ident, "group": group, "split": "dev", "title": row["title"],
            "base_id": ref.get("base_id"), "variant_type": ref.get("variant_type"),
            "reference_status": ref_status, "actual_status": actual_status,
            "reason": reason, "actual_reason": actual_reason,
            "issues": issues, "suggestion": suggestion, "human_confirmation": confirmation,
            "evidence": ev, "evidence_complete": ident != "robust-23",
            "evidence_limitation": "缺少“这批曲目”的集合/上下文范围证据" if ident == "robust-23" else None,
            "reference": {"sql": ref["gold_sql"], "result": ref["gold_result"], "ordered": ref["ordered"], "columns": ref["gold_columns"]},
            "existing_actual": {"status": actual["status"], "sql": actual["sql"], "table": actual["table"], "answer": actual["answer"],
                                "rewritten_question": actual.get("rewritten_question"), "trace_id": actual["trace_id"],
                                "truncated": actual["metadata"].get("truncated")},
            "execution_evidence": {"reference_jsonl_line": ref_line, "actual_jsonl_line": actual_line,
                                   "matches_reference_stored_values": ref_verify["matches_stored_values"],
                                   "matches_actual_stored_values": actual_verify["matches_stored_values"]},
            "automatic_EX_matched": row["machine_checks"].get("automatic_EX_matched"),
            "human_fields_modified": False,
        }
        reviews.append(common)
    assert len(reviews) == 56 and len({r["review_id"] for r in reviews}) == 56
    assert set(SEMANTICS) == {r["id"] for r in reviews if r["group"] == "nl2sql"}
    assert set(VARIANTS) == {r["id"] for r in reviews if r["group"] == "robust"}
    write_sql(reviews, summary)
    write_metrics(metric_rows, query_index)
    (ART / "sql-gold-source-checks.json").write_text(json.dumps({"scope": "DEV only; original question/gold/result/type/order projection compared with unified table; no holdout question or answer projected",
                                                               "checked_rows": len(gold_source_checks), "mismatch_count": 0, "rows": gold_source_checks}, ensure_ascii=False, indent=2), encoding="utf-8")
    command_record = {
        "purpose": "Only re-execute existing DEV gold/actual SELECT statements and supplement audit evidence; never request new system predictions",
        "workdir": str(ROOT), "shell": "PowerShell 7.6",
        "command": ".\\.venv\\Scripts\\python.exe -B eval/artifacts/d2-ai-preaudit/verify_sql.py",
        "argv": [".\\.venv\\Scripts\\python.exe", "-B", "eval/artifacts/d2-ai-preaudit/verify_sql.py"],
        "sandbox_permissions": "require_escalated", "reason": "Sandbox local socket restricted; local configured qa_reader SELECT only",
        "exit_code": 0, "started_at_utc": summary["started_at_utc"], "finished_at_utc": summary["finished_at_utc"],
        "statement_configuration": ["SET TRANSACTION READ ONLY", "SET LOCAL statement_timeout = '5000ms'", "rollback after all SELECT evidence"],
        "identity": summary["identity"], "select_count": 130,
        "expected_gold_actual_select_count": 112, "metric_sql_select_count": 6, "supplemental_select_count": 11, "identity_select_count": 1,
        "output_files": ["eval/artifacts/d2-ai-preaudit/sql-verification.jsonl", "eval/artifacts/d2-ai-preaudit/sql-verification-summary.json"],
        "script_sha256": summary["script_sha256"],
        "report_command": ".\\.venv\\Scripts\\python.exe -B eval/artifacts/d2-ai-preaudit/build_sql_review.py",
    }
    (ART / "sql-command-record.json").write_text(json.dumps(command_record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"sql_rows": len(reviews), "sql_reference_status_counts": dict(Counter(r["reference_status"] for r in reviews)),
                      "sql_actual_status_counts": dict(Counter(r["actual_status"] for r in reviews)), "metrics_rows": len(metric_rows)}, ensure_ascii=False))


def write_sql(reviews, summary):
    report = {"title": "D2 SQL与鲁棒开发集AI预审", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "35条nl2sql dev + 21条robust dev；只读审核原题、参考与已存在系统输出；AI建议不等于人工确认",
              "holdout_policy": "当前为开发会话，未提供独立保留集隔离机制；保留题仅统计跳过数量，不审核题干、参考或答案",
              "skipped_holdout_counts": summary["skipped_holdout_counts"],
              "method": "逐题语义审核字段、粒度、过滤、单位、日期、NULL、排序、LIMIT并列与变体歧义；重读原responses，重执行现有SELECT作证据，不生成新预测",
              "read_only_verification": {"select_count": 130, "gold_actual_select_count": 112, "original_prediction_consistency_checked_rows": 56,
                                         "matches_stored_values": 112, "database_role": "qa_reader", "transaction_read_only": True, "statement_timeout_ms": 5000,
                                         "command_record": "eval/artifacts/d2-ai-preaudit/sql-command-record.json"},
              "reference_status_counts": dict(Counter(r["reference_status"] for r in reviews)),
              "actual_status_counts": dict(Counter(r["actual_status"] for r in reviews)),
              "human_review_fields_preserved": True, "business_files_modified": False, "rows": reviews}
    (REPORT / "sql-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    parts = ["# D2 SQL与鲁棒开发集AI预审", "", report["scope"], "", report["holdout_policy"] + "。跳过nl2sql 15条、robust 9条。", "",
             "本次以题意为先逐行审查，重读原始开发responses；112条已有gold/actual SQL及6个口径示例、11条补充SELECT、1条只读身份查询共130条全部完成。112条已有SQL实际值均与原记录一致，但执行成功/EX相同不是语义通过依据。没有调用问答API或模型，没有生成新的系统预测。", "",
             "参考建议：" + json.dumps(report["reference_status_counts"], ensure_ascii=False) + "；实际输出建议：" + json.dumps(report["actual_status_counts"], ensure_ascii=False) + "。", "",
             "sql-38当前快照bytes没有NULL，当前结果正确，但可空列DESC默认NULL先排需确认规则。robust-23“这批”范围未定义，实际答全库平均暂不能确定。robust-26最终回答正确，改写吞掉请求词单独记为rewrite质量问题；robust-13值链接trace未匹配但最终SQL正确，不把最终正确当作NLU阶段成功证据。", "",
             "|review_id|参考|实际|证据完整|主要问题|", "|---|---|---|---|---|"]
    for row in reviews:
        issue_text = "；".join(i["object"] + ": " + i["problem"] for i in row["issues"]) or "逐项审核未发现本次输出的语义错误"
        parts.append(f"|{row['review_id']}|{row['reference_status']}|{row['actual_status']}|{'是' if row['evidence_complete'] else '否'}|{issue_text.replace('|', '/')}|")
    for row in reviews:
        parts.extend(["", "## " + row["review_id"], "", "题目：" + row["title"], "", "参考：" + row["reference_status"] + "。" + row["reason"],
                      "", "实际：" + row["actual_status"] + "。" + row["actual_reason"], "", "已有参考SQL：", "", "```sql", row["reference"]["sql"], "```", "",
                      "已有系统SQL：", "", "```sql", row["existing_actual"]["sql"], "```", "", "已有系统自然语言：" + row["existing_actual"]["answer"],
                      "", "建议：" + row["suggestion"], "", "人工待确认：" + row["human_confirmation"], "", "证据："])
        for item in row["evidence"]:
            location = f"第{item['line']}行" if "line" in item else item.get("section", "")
            parts.append(f"- `{item['path']}`，{location}：{item.get('note', '')}")
    (REPORT / "sql-review.md").write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_metrics(metric_rows, query_index):
    definitions = json.loads((ROOT / "data/rules/metric_definitions.json").read_text(encoding="utf-8"))
    confirmation = json.loads((ROOT / "eval/artifacts/d2/source/metric-human-review.json").read_text(encoding="utf-8"))
    existing_sql = json.loads((ROOT / "eval/artifacts/d2/source/metric-sql-checks.json").read_text(encoding="utf-8"))
    meanings = {
        "sales_revenue": ("revenue_invoice", "发票销售额在invoice粒度SUM(total)，期间依据invoice_date半开范围，示例2024年返回477.53。按曲目/艺术家另用invoice_line.unit_price*quantity，不能明细JOIN后重复SUM发票总额；全库发票与明细对账均2328.60、差0.00。空期间SUM为NULL，不能无声改0。金额仅数据库金额单位，源数据未声明币种或支付状态。"),
        "average_invoice_amount": ("average_invoice", "平均每张发票金额为AVG(invoice.total)，示例先平均再保留两位得到2024年5.75；平均每位购买客户金额SUM(total)/COUNT(DISTINCT customer_id)是另一个指标。空期间AVG为NULL。已确认的短标签提案“客单价”不应使未指明对象的其他问题自动获得默认口径，runtime_defaults_enabled仍false。"),
        "repeat_customer_count": ("repeat_customers", "期间内复购客户数先将明确期间[2024-01-01,2025-01-01)的invoice按customer_id分组，HAVING COUNT(*)>=2，再计合格客户数，示例27位并有逐客户明细支持；不是发票条数、客户历史跨期次数或付款成功次数。没有合格客户时COUNT返回0，缺少期间不能自动填年。"),
        "popular_tracks": ("popular_tracks", "明确期间内热门曲目按SUM(invoice_line.quantity)的实际购买数量，关联invoice_date过滤；不是目录单价、金额或播放列表成员数。数量降序后track_id升序作并列规则，再LIMIT 5；2024年示例3/9/15/21/30均购买1，补充前10行也并列1，稳定次排序必要。客户“谁买得最多”的金额口径与曲目热门不同，主语省略且无期间的问题仍需澄清。"),
    }
    reviewed = []
    for row in metric_rows:
        ident = row["id"]
        name, reason = meanings[ident]
        line, result = query_index[("metric-example:" + name, "metric_sql_example")]
        old_example = next(item for item in existing_sql["records"] if item["id"] == name)
        assert old_example["sql"] == result["sql"] and old_example["columns"] == result["columns"] and old_example["rows"] == result["rows"]
        supplement_names = {"sales_revenue": ["empty-amount-semantics"], "average_invoice_amount": ["empty-amount-semantics"],
                            "repeat_customer_count": ["repeat-customer-check"], "popular_tracks": ["popular-quantity-ties"]}[ident]
        ev = [evidence("data/rules/metric_definitions.json", section="metrics." + ident + "; general; sql_examples." + name),
              evidence("eval/artifacts/d2/source/metric-human-review.json", section="method; statement; scope; proposal_sha256; reviewed_at_utc", note="原既有人工共同确认记录，仅核实留存、不代填新审批"),
              evidence("eval/artifacts/d2/source/metric-sql-checks.json", section="records.id=" + name, note="既有只读例SQL材料；其早期pending状态早于单独共同确认记录，不视为撤销确认"),
              evidence("eval/artifacts/d2-ai-preaudit/sql-verification.jsonl", line=line, note="本次只读重执行既有SQL示例"),
              evidence("data/catalog/chinook.yaml", section="invoice; invoice_line; track; invoice_date_range"),
              evidence("eval/artifacts/d2-ai-preaudit/database-materials.json", section="schema; invoice_dates; identity; privileges")]
        for key in supplement_names:
            n, _ = query_index[("supplemental:" + key, "audit_select")]
            ev.append(evidence("eval/artifacts/d2-ai-preaudit/sql-verification.jsonl", line=n, note=key))
        if ident == "sales_revenue":
            n, _ = query_index[("metric-example:revenue_reconciliation", "metric_sql_example")]
            ev.append(evidence("eval/artifacts/d2-ai-preaudit/sql-verification.jsonl", line=n, note="发票与明细金额对账"))
        assert row["expected"]["definition"] == next(item for item in definitions["metrics"] if item["id"] == ident)
        assert confirmation["statement"] == "A、B已共同核对同意四项口径"
        assert confirmation["scope"] == "four business definitions and distinct query-object rule only; does not approve evaluation gold or aliases"
        reviewed.append({"review_id": row["review_id"], "id": ident, "group": "metric", "split": None, "title": row["title"],
                         "reference_status": PASS, "actual_status": "不适用（已确认口径依据）", "reason": reason,
                         "actual_reason": "本行是四项已确认业务口径的依据核验，actual原本null；本次仅重执行既有口径示例SELECT，未产生问答系统新预测。",
                         "issues": [], "suggestion": "保留既有四项确认记录；执行该口径时仍明确对象、期间、字段和单位，不把确认范围扩大到题库gold或别名。",
                         "human_confirmation": "既有用户陈述“A、B已共同核对同意四项口径”；本次不新增/冒填人工审批，不要求重复确认四项已授权口径。",
                         "existing_human_confirmation": confirmation, "existing_actual": None,
                         "evidence": ev, "evidence_complete": True, "human_fields_modified": False,
                         "readonly_sql_example_reexecution": {"sql": result["sql"], "columns": result["columns"], "rows": result["rows"], "evidence_line": line}})
    report = {"title": "D2四项已确认口径AI依据核验", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "仅依据核验，不再审批既有口径，不扩大用户确认到题库gold或别名；actual不适用",
              "reference_status_counts": {PASS: 4}, "actual_status_counts": {"不适用（已确认口径依据）": 4},
              "human_fields_preserved": True, "existing_confirmation_scope": confirmation["scope"], "rows": reviewed}
    (REPORT / "metrics-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    parts = ["# D2四项已确认口径AI依据核验", "", report["scope"], "", "既有用户确认：A、B已共同核对同意四项口径。AI核验只保留该原记录，不能代替/扩大人工确认到题库答案或别名。所有金额使用数据库金额单位，没有推断币种。", "",
             "|指标|参考建议|实际|2024年只读示例|", "|---|---|---|---|"]
    for row in reviewed:
        parts.append(f"|{row['title']}|{row['reference_status']}|{row['actual_status']}|{json.dumps(row['readonly_sql_example_reexecution']['rows'], ensure_ascii=False)}|")
    for row in reviewed:
        parts.extend(["", "## " + row["review_id"], "", row["reason"], "", row["actual_reason"], "", row["suggestion"], "", "证据："])
        for item in row["evidence"]:
            location = f"第{item['line']}行" if "line" in item else item.get("section", "")
            parts.append(f"- `{item['path']}`，{location}：{item.get('note', '')}")
    (REPORT / "metrics-review.md").write_text("\n".join(parts) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
