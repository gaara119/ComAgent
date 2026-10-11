"""Build a new D3 30-case family split; never edits older datasets or predictions."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.clarify.rules import explicit_period


def main():
    destination = ROOT / "eval/datasets/d3/clarify"
    if destination.exists():
        raise SystemExit("Destination already exists; use a new dataset version.")
    # Labels are a project-authored D3 development proposal, not OHR or official gold.
    specs = [
        ("L0", "巴西有多少客户？", {"metric":"customer_count"}, "客户计数不需要期间；国家来自客户所在地。"),
        ("L0", "genre.name 明确为 Rock 的曲目有多少首？", {"metric":"track_count"}, "显式标准对象不再问摇滚候选。"),
        ("L0", "2024年账单国家为Canada的发票销售额是多少？", {"metric":"invoice_revenue","time_scope":explicit_period("2024年"),"region_scope":"invoice.billing_country"}, "发票总额和账单国家已明确。"),
        ("L0", "2024年全部发票的平均每张发票金额是多少？", {"metric":"average_invoice_amount","time_scope":explicit_period("2024年")}, "已确认客单价定义，无地区歧义。"),
        ("L0", "数据库一共有多少个音乐流派？", {"metric":"record_count"}, "单表全部记录范围明确。"),
        ("L0", "国家明确为Antarctica的客户有多少位？", {"metric":"customer_count"}, "不存在值应保留零结果，不替成其它国家。"),
        ("L0", "2024年账单国家为Brazil的发票金额占同年所有发票金额的比例是多少？", {"task_type":"ratio","metric":"invoice_revenue","numerator":"2024年账单国家Brazil的发票金额","denominator":"2024年全部发票金额","time_scope":explicit_period("2024年"),"region_scope":"invoice.billing_country"}, "分子分母同年且范围明确，不因比较任务一概追问。"),
        ("L0", "2024年账单国家为USA的发票销售额同比增长率是多少？", {"task_type":"growth","metric":"invoice_revenue","time_scope":explicit_period("2024年"),"comparison":{"type":"yoy"},"region_scope":"invoice.billing_country"}, "当前年度和同比明确，2023年基期可程序推导。"),
        ("L0", "2024年5月全部发票销售额环比增长率是多少？", {"task_type":"growth","metric":"invoice_revenue","time_scope":explicit_period("2024年5月"),"comparison":{"type":"mom"}}, "当前月份与环比明确，4月基期可推导。"),
        ("L0", "2024年全部发票按总额从高到低列出前5张，相同金额按invoice_id升序。", {"task_type":"ranking","metric":"invoice_revenue","rank_object":"invoice","top_n":5,"time_scope":explicit_period("2024年")}, "排名对象、计量、时期、数量及并列次序明确。"),
        ("L1", "2024年最受欢迎的5首曲目是哪些？", {"task_type":"ranking","rank_object":"track","top_n":5,"time_scope":explicit_period("2024年")}, "购买数量为已确认曲目默认，应声明并支持切换。"),
        ("L1", "2023年最热门的3首歌曲是哪几首？", {"task_type":"ranking","rank_object":"track","top_n":3,"time_scope":explicit_period("2023年")}, "曲目对象及期间明确，默认只作用于计量。"),
        ("L1", "2022年卖得最好的2首歌有哪些？", {"task_type":"ranking","rank_object":"track","top_n":2,"time_scope":explicit_period("2022年")}, "已登记热门曲目购买数量口径，不能改成全局销量默认。"),
        ("L1", "2024年客户中谁买得最多？请列前3名。", {"task_type":"ranking","rank_object":"customer","top_n":3,"time_scope":explicit_period("2024年")}, "客户买得最多保留金额专属定义，不能套曲目数量。"),
        ("L1", "2024年曲目按购买数量排名。", {"task_type":"ranking","metric":"purchased_quantity","rank_object":"track","time_scope":explicit_period("2024年")}, "未指定条数时按总计划前10，明确声明。"),
        ("L2", "账单国家为USA的发票销售额同比增长多少？", {"task_type":"growth","metric":"invoice_revenue","comparison":{"type":"yoy"},"region_scope":"invoice.billing_country"}, "缺当前年份，真实年份只提供候选不代填。"),
        ("L2", "2024年同比增长多少？", {"task_type":"growth","time_scope":explicit_period("2024年"),"comparison":{"type":"yoy"}}, "缺基础指标，不能猜发票额。"),
        ("L2", "2024年全部发票销售额增长多少？", {"task_type":"growth","metric":"invoice_revenue","time_scope":explicit_period("2024年")}, "同比/环比或显式基期缺失。"),
        ("L2", "2024年Brazil账单发票销售额占比是多少？", {"task_type":"ratio","metric":"invoice_revenue","numerator":"2024年Brazil账单发票销售额","time_scope":explicit_period("2024年"),"region_scope":"invoice.billing_country"}, "分母范围未给，不默认全库或同年全部。"),
        ("L2", "2024年哪些记录的金额占全部发票金额的比例？我还没确定分子范围。", {"task_type":"ratio","metric":"invoice_revenue","denominator":"2024年全部发票金额","time_scope":explicit_period("2024年")}, "用户明确分子未定，不自行补条件。"),
        ("L2", "最受欢迎的5首曲目是哪些？", {"task_type":"ranking","rank_object":"track","top_n":5}, "已确认曲目指标需要指定期间，不猜最近一年。"),
        ("L2", "2024年谁买得最多？", {"task_type":"ranking","time_scope":explicit_period("2024年")}, "没有查询对象，金额/数量不可安装全局默认。"),
        ("L2", "摇滚歌曲有多少首？", {"metric":"track_count","_ambiguity":"摇滚"}, "真实Rock与Rock And Roll都存在，必须用户选择。"),
        ("L2", "2024年美国的发票销售额是多少？", {"metric":"invoice_revenue","time_scope":explicit_period("2024年"),"region_ambiguous":True}, "客户所在国与账单国家含义不同。"),
        ("L2", "这批曲目的平均时长是多少？", {"scope_missing":True}, "没有这批记录的范围，不能复用全库gold。"),
        ("L2", "有多少复购客户？", {"metric":"repeat_customer_count"}, "期间内至少2张发票定义必须说明期间。"),
        ("L2", "2024年全部发票销售额环比增长率是多少？", {"task_type":"growth","metric":"invoice_revenue","time_scope":explicit_period("2024年"),"comparison":{"type":"mom"}}, "年度范围不能唯一推导月环比基期。"),
        ("L2", "统计2024年的发票销售额，但日期必须从2023年1月1日到2023年12月31日。", {"metric":"invoice_revenue","conflicts":["2024年与2023年日期范围冲突"]}, "同一任务日期条件冲突，应由用户确定。"),
        ("L2", "最近完整年度的发票销售额是多少？", {"metric":"invoice_revenue","time_ambiguous":True}, "日期存在不证明年度完整，无完整性依据则澄清。"),
        ("L2", "摇滚乐曲目的平均时长是多少？", {"_ambiguity":"摇滚乐"}, "即便聚合平均值，也不能自动合并不同音乐流派。"),
    ]
    # Family splitting occurs before any prediction; all variants of one intent
    # would share its family. These cases have distinct final tasks.
    hold_positions = {3,6,9,12,15,18,21,24,29}
    destination.mkdir(parents=True)
    (destination / "protected_holdout").mkdir()
    dev, held = [], []
    for number, (level, question, semantic, rationale) in enumerate(specs,1):
        record={"id":f"clarify-{number:02d}","family_id":f"d3-clarify-family-{number:02d}",
                "split":"holdout" if number in hold_positions else "dev",
                "question":question,"scope":{"route":"sql","db_id":"chinook","doc_ids":[]},
                "expected_level":level,"expected_behavior":"clarify" if level=="L2" else "execute_with_assumption" if level=="L1" else "execute",
                "reference_semantics":semantic,"basis":rationale,
                "source_type":"project_authored","source":"方案.md §3.6.4; approved metric_definitions.json",
                "auto_review_status":"pending","ai_review_status":"pending","human_review_status":"pending_human_review"}
        (held if record["split"]=="holdout" else dev).append(record)
    for path, records in [(destination/"dev.jsonl",dev),(destination/"protected_holdout"/"cases.jsonl",held)]:
        path.write_text("".join(json.dumps(row,ensure_ascii=False)+"\n" for row in records),encoding="utf-8")
    manifest={"created_at_utc":datetime.now(timezone.utc).isoformat(),"total":len(specs),"dev":len(dev),"holdout":len(held),
              "labels":dict(Counter(level for level,_,_,_ in specs)),"family_leakage":False,
              "dev_sha256":sha256((destination/'dev.jsonl').read_bytes()).hexdigest(),
              "holdout_sha256":sha256((destination/'protected_holdout/cases.jsonl').read_bytes()).hexdigest(),
              "holdout_predictions":0,"holdout_policy":"D5 after freeze only; excluded from developer review and live runner",
              "human_review_status":"pending_human_review"}
    (destination/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({key:manifest[key] for key in ("total","dev","holdout","labels","holdout_predictions")},ensure_ascii=False))


if __name__=="__main__":main()
