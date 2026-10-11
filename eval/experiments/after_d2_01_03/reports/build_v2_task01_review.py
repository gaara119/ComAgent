"""Write independently reasoned task01 V1/V2 review from all30 preserved DEV turns.

This is an evidence/document script outside frozen runtime. No API/model/SQL
calls, label changes, scoring changes, prompt changes or human approvals.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
EXP = "eval/experiments/after_d2_01_03"
RUN = EXP + "/runtime_eval/runs/V2-001"
OUT = ROOT / EXP / "reports"
LABEL = EXP + "/data/cases-v6-reviewed.jsonl"
EXPECTED_SHA = "42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1"
V0_REVIEW = EXP + "/reports/v0-task01-full-review.json"
SCORE = EXP + "/runtime_eval/runs/V2-001-scores.json"
CAPTURE_ROOT = (ROOT / EXP / "runtime_eval/provider-captures/V2-001").resolve()
UUID = re.compile(r"(?:[0-9a-f]{32}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})\.json", re.I)

# Judgments below were written after reading each actual V2 question, reference,
# final SQL/result, NLU binding/patches, gate behavior and provider evidence.
# They do not branch on the automatic result-comparison/score field.
OPINIONS = {
 1: ("AI建议通过", "customers明确客户对象；真实France值按customer.country等值COUNT(*)，客户记录粒度、NULL过滤和无期间条件均正确。V2实际绑定France、SQL和保存结果5一致，无改口径。"),
 2: ("AI建议通过", "已批准Iron Maiden乐队别名被绑定并改写。实际album按artist_id FK内连接artist过滤Iron Maiden，COUNT(DISTINCT album.album_id)与参考COUNT(*)等价：album_id为非NULL主键，artist_id是artist主键且多对一，不会复制专辑记录。实际21；此结构证明独立于结果相等。"),
 3: ("AI建议有条件通过", "实际德国→invoice.billing_country=Germany且SUM(invoice.total)=156.48，按发票账单国家解释保持金额粒度，未联明细。参考与实际均选择账单国家，但已确认规则只区分两国字段，没有全局地区默认。维持V0地区解释争议，人工确认后才可完整通过。"),
 4: ("AI建议有条件通过", "实际SQL确将Frnace变为France，COUNT客户结果5；但metadata.nlu mentions/bindings/patches及intent.filters均为空，response.rewritten_question为NULL。只能说在人工同意该拼写修正后查询正确；有限候选消歧、绑定和显式改写链未完成，不能按结果5认定专项①全通过。"),
 5: ("AI发现错误", "实际NLU无候选/绑定/改写；3次生成及修复仍LOWER(artist.name)=LOWER('Metallcia')，未修成参考Metallica，并被多表守卫拒绝，table为NULL。在人工确认参考拼写意图后仍存在未正确消歧及查询未执行的真实缺陷；不能把被拒SQL当已得到10。"),
 6: ("证据不足", "原参考题有Deguo专辑却canonical/控制器对应无关对象，gold为空，原先已排除评分，仍不能按该标准决定系统正确。V2实际猜成artist.name='Deguo'、无绑定/澄清、跨表守卫FAILED且无结果。独立观察为无依据的对象解释及未完成查询，未把坏参考变成系统通过。"),
 7: ("AI发现错误", "原文明确Protected AAC媒体格式与track数量，参考track.media_type_id→media_type主键FK有效。V2模型3次给出同一正确FK/名称过滤COUNT，调用实际仍单表system，sql_validate均拒绝跨表，NLU绑定空，table=NULL。实际未运行结果237，不能以候选SQL语义正确认定系统回答正确。"),
 8: ("AI建议通过", "意大利在明确客户对象下使用批准customer.country=Italy别名并显式改写；COUNT客户记录1。‘现在’对应现有数据快照，未发明客户创建日期或把invoice_date套到客户。"),
 9: ("AI建议通过", "实际仅给出genre.name的Rock和Rock And Roll两个真实候选，L2、filters为空、SQL/table为空，不强制唯一绑定。满足本条初始候选澄清目标；控制器无补充，因此不是续答成功或SQL执行通过。"),
 10: ("AI发现错误", "Vaporwave在已保存25个流派事实中不存在；模型保留该字面值并给出track→genre FK COUNT，未换成相似流派，候选裁决unmatched可观察。但实际3次SQL均被单表守卫拒绝，table=NULL、未报告没有记录；正确候选SQL和预计COUNT0不能替代实际回答。"),
 11: ("AI建议通过", "明确Canada客户按customer.country=Canada COUNT(*)，真实exact绑定、无额外期间/表/聚合，实际8。别名customer_count不会改语义。"),
 12: ("AI建议有条件通过", "明确2022发票收入，但France未明说客户居住国还是账单国家；V2实际L2问这两种口径，未SQL且controller_unanswered。全局地区默认未获确认，原参考唯一账单国家39.60继续有条件待核；不能仅因原预期L0就把这条追问定为错误。"),
 13: ("AI建议通过", "内容与sp01-02重复，原标签排除状态保留。V2已批准艺术家绑定/改写，album→artist主键FK过滤Iron Maiden，COUNT(album.album_id)与COUNT(*)等价，因为该主键非NULL且FK多对一；结果21正确，但重复题不增加独立覆盖。"),
 14: ("证据不足", "题面只说法兰西的发票，原参考按customer.country却allowed允许两口径且原标签待确认。实际绑定invoice.billing_country=France、COUNT发票35，保存结果与客户所在地参考也35；该巧合不能证明两字段等价。正式系统正确性继续不能确定，先核地区口径。"),
 15: ("AI建议通过", "已批准受保护AAC音频文件别名明确指media_type.name，实际绑定/改写Protected AAC audio file；track→media_type FK主键内连接COUNT曲目237，统计曲目粒度且NULL外键不误并入。"),
 16: ("AI建议通过", "已批准U2乐队别名实际绑定/改写。COUNT(*)在album→artist主键FK内连接与参考COUNT(DISTINCT album_id)等价，album_id非NULL唯一且艺术家连接多对一；结果10只是附加保存数据核验，非唯一语义依据。"),
 17: ("AI建议有条件通过", "V2实际Fracne被SQL生成阶段改成France且COUNT结果5；NLU mentions/bindings/patches为空、intent.filters为空、rewritten_question=NULL。与04一致，仅查询在人工确认拼写意图后可通过；未证明候选裁决或显式绑定/改写，不把自动结果正确当整个专项①链完成。原V0对此给错误的历史意见保留，本次明确拆分查询与链路维度。"),
 18: ("AI发现错误", "V2实际专辑计数对象比V0提取artist_id有所改善，但name仍LOWER('Led Zepelin')而不是人工待确认的Led Zeppelin，无绑定/改写，3次跨表校验拒绝、table=NULL。没有取得参考14，不构成正确消歧。"),
 19: ("AI建议通过", "实际有限候选fuzzy匹配Canda→Canada，绑定customer.country、patch及rewritten_question均保存；COUNT客户8。API答案单句8，但既有UI源码在答案前显示改写/patch，可说明更正；本条未新增浏览器验收，不能冒称实际截图已核。拼写解释仍为参考人审事项。"),
 20: ("AI发现错误", "V2模型把MPEG adiou修成MPEG audio，但NLU绑定/patch为空。最终候选SQL为track.media_type_id=(SELECT媒体ID WHERE name正确 LIMIT1)，完整保存媒体事实显示仅一个MPEG audio ID，当前数据下与参考FK联表计数相符；此唯一性仅是实际快照事实，并无名称唯一约束。实际多表守卫拒绝，无执行3034，不能当通过。"),
 21: ("AI建议通过", "客户对象明确；Deguo由批准德国别名pinyin链绑定customer.country=Germany并改写，COUNT客户4；未把拼音当艺术家或跨到billing_country。"),
 22: ("AI发现错误", "已批准古典→Classical及真实genre事实可支持pinyin目标，但V2实际NLU无mentions/bindings，SQL仍genre.name='Gudian'且跨表守卫FAILED。未得74、未改写正确值，不能因SQL形式COUNT/FK正确就通过。"),
 23: ("AI建议通过", "中英混写仍明确Canada和customers，实际exact customer.country绑定、客户COUNT8，无不相关期间/发票字段。"),
 24: ("AI建议通过", "artist/albums对象明确，actual artist.name=Iron Maiden绑定正确，artist→album主键FK内连接COUNT(album_id)。album_id非NULL，COUNT(album_id)等同COUNT(*)，连接顺序不改变多对一粒度，保存结果21。"),
 25: ("证据不足", "原参考声称意大利发票默认按客户所在地，已确认规则没有这种默认。V2实际按invoice.billing_country=Italy SUM(total)得到37.62，参考customer.country也37.62只为本快照巧合，不是语义证明。保留参考错误与人审，正式系统评分不能确定，不为系统改参考。"),
 26: ("AI建议通过", "加拿大在客户对象下已批准country=Canada别名绑定并改写，客户COUNT8；‘现在’只指数据快照，没有虚构客户时间字段。"),
 27: ("AI建议通过", "摇滚为已批准候选关系；实际L2完整保留Rock/Rock And Roll两genre选项，无自动绑定、无SQL。原冻结binding合同用一个IN列表，而候选观察是两个等值项，可能导致原scorer失败；保留原分，不以修改合同让系统通过。这里只通过初始澄清行为，不声称后续SQL成功。"),
 28: ("AI建议有条件通过", "原题明确流派；参考把Metallica艺术家和Heavy Metal泛近义关系列入，原标签已排除且参考依据错保留。V2实际只给已批准candidate-only的genre Metal，L2不自动绑定、不出现pending Metallica，不猜艺术家。该候选确认行为合理；是否还应有Heavy Metal候选仍需人工，当前仅条件通过。"),
 29: ("AI建议有条件通过", "题面显式customer.country='Atlantis'并要求原字面查询。实际SQL原字面COUNT0，已保存完整countries中无Atlantis，未换成相似国家；COUNT单聚合行0是SUCCEEDED，不是空表或NULL。但answer只‘查询结果：0’，未明确说‘没有记录’，需人工确认说明措辞是否达要求；literal未入已验证绑定不能冒称实体绑定成功。"),
 30: ("证据不足", "原题已明确[2030-01-01,2030-12-31)却参考写<2031-01-01，V0已发现参考边界错误保留；正式按该坏参考不能决定系统评分。V2新增可直接核对的错误行为：把‘之间’识别为invoice.billing_country模糊mention，候选为Argentina/Australia/Austria/Belgium/Brazil并L2询问，用户日期题无国家要求，未SQL。单列无依据追问，不把该行为冒充正确日期保留，也不改原gold/controller。"),
}
REFERENCE_NOTES = {
 1: "客户对象与France明确；参考在customer.country等值COUNT(*)按客户记录数，NULL不满足等值，无附加期间，保存gold5。",
 2: "批准Iron Maiden乐队别名指artist.name；参考album经artist_id真实FK连artist按名称COUNT专辑，主键粒度正确，gold21。",
 3: "参考按invoice.billing_country=Germany求SUM(invoice.total)156.48，金额粒度正确；题面德国发票地理归属仍需确认，已批准规则无全局地区默认。",
 4: "Frnace→France为可能拼写纠正，参考customer.country COUNT5保持客户对象；目标纠正与有限候选依据仍需人工，不能只由结果批准。",
 5: "Metallcia→Metallica拼写目标仍待人工；在该解释下参考album→artist FK计数专辑10，字段与粒度正确。",
 6: "Deguo专辑的canonical_input/控制器/允许解释对应无关艺术家或国家，gold为空，标签已排除；参考无法作为可靠系统标准。",
 7: "原文format明确media_type.name，参考track.media_type_id真实FK过滤Protected AAC名称计数曲目237，不是统计媒体格式行数。",
 8: "意大利批准客户country别名；参考customer.country=Italy COUNT1，‘现在’按数据快照，无虚构创建时间字段。",
 9: "摇滚批准Rock/Rock And Roll候选关系；参考先澄清而不自动绑定唯一genre，无goldSQL符合该初始阶段。",
 10: "显式genre Vaporwave在保存完整25流派中不存在；参考按原字面track→genre FK COUNT0，不能替换相似值；题面还要求没有记录措辞。",
 11: "Canada客户题参考customer.country COUNT8，字段、NULL处理与对象明确，无期间/单位问题。",
 12: "2022半开日期SUM发票总额正确；France归属未指定，参考强选billing_country仍有口径争议，gold39.60不证明唯一解释。",
 13: "题面与02完全重复，原排除状态不变；参考album→artist FK按Iron Maiden COUNT专辑21的内容逻辑正确，但不增加独立覆盖。",
 14: "法兰西发票未明说地区来源；gold选customer.country而allowed允许客户/账单两口径，不能用参考35固定唯一答案，原已待确认。",
 15: "受保护AAC批准别名明确media_type.name；参考track FK内连接媒体格式计数237，曲目粒度正确。",
 16: "U2批准别名；参考COUNT(DISTINCT album_id)在真实artist FK内连接下统计专辑10，非NULL主键避免重复，逻辑正确。",
 17: "Fracne→France为可能拼写纠正，参考客户country COUNT5保持原对象；改写意图/候选依据仍需人工。",
 18: "Led Zepelin→Led Zeppelin目标拼写仍待人工；该解释下参考artist FK COUNT(DISTINCT album_id)14，专辑粒度正确。",
 19: "Canda→Canada为有实际有限fuzzy候选的纠正解释，参考客户country COUNT8；原拼写意图仍需人工确认。",
 20: "MPEG adiou→MPEG audio file拼写目标待人工；该解释下参考track→media_type FK COUNT曲目3034正确。",
 21: "Deguo客户可由已批准德国别名的pinyin对应Germany，参考customer.country COUNT4保持客户对象。",
 22: "Gudian流派可由批准古典pinyin对应Classical，参考track→genre FK COUNT74，对象/字段/单位为曲目条数。",
 23: "中英混写Canada/customers明确，参考country等值客户COUNT8，无额外条件。",
 24: "Iron Maiden artist/albums明确，参考真实album→artist主键FK COUNT专辑21正确。",
 25: "参考business_basis声称意大利发票默认按客户所在地，但已确认规则没有这种默认；gold customer.country37.62不能作为唯一参考，与账单国家当前同值也不等价。",
 26: "加拿大批准country别名且对象客户；参考COUNT8，‘现在’仅数据快照，没有虚构时间字段。",
 27: "摇滚双候选需先澄清正确；原expected_bindings采用IN列表与候选两个等值观察可能造成评分格式争议，冻结标签/分数保留待人工，不强选唯一genre。",
 28: "题面明确流派，原参考却把艺术家Metallica和未经批准的Heavy Metal泛近义候选加入；当前Metallica金属别名pending、Metal为approved_candidate，参考依据错误且原标签已排除。",
 29: "题面显式customer.country='Atlantis'，保存完整国家列表无该值；参考按原字面COUNT0正确，不能把聚合0当空表/NULL。",
 30: "题面明确左闭右开[2030-01-01,2030-12-31)，原参考却上界2031-01-01，边界错误；未来无记录导致0相同不证明期间正确。",
}
V1_DIFFERENT_OPINIONS = {
 2: ("AI建议通过", "V1实际已批准Iron Maiden乐队绑定/改写，album→artist按真实artist_id FK内连接、name等值COUNT(*)与参考相同；21附加核对保存数据，不用相同结果替代对象/连接粒度证明。"),
 5: ("AI发现错误", "V1实际前两次SQL按artist.name='Metallcia'经album FK联表，跨表校验拒绝；第三次技术修复却改成album.title='Metallcia'单表COUNT并执行0。用户未确认把艺术家换为专辑标题，修复改变业务条件来源且仍无拼写纠正/绑定/改写。在人工确认Metallica拼写意图后该结果也不满足参考10；不能用SQL终于能执行宣称修复成功。"),
 7: ("AI发现错误", "V1实际3次模型由正确track→media_type FK JOIN改成媒体ID子查询，仍为同一媒体名称条件；完整已保存媒体事实证实Protected AAC只有ID2。候选SQL可满足当前查询，单表system/多表守卫仍拒绝联表及子查询，table=NULL、绑定空，没有实得237。最后tables_used省略子查询表不等于真实只使用track。"),
 10: ("AI发现错误", "V1实际候选裁决对Vaporwave为unmatched，生成保留原字面genre FK JOIN，最后修成genre_id IN子查询，未猜相似流派。但所有3次SQL均被跨表守卫拒绝，未得到COUNT0也未报告没有记录；不能将未执行SQL或预期0当实际答案。"),
 13: ("AI建议通过", "与02重复的原标签排除状态保持；V1实际批准艺术家绑定/改写，album→artist真实主键FK内连接COUNT(*)按Iron Maiden21正确。重复题不增加独立测试覆盖。"),
 18: ("AI发现错误", "V1实际前两次按artist.name='led zepelin'做FK专辑计数，被跨表守卫拒绝；第三次技术修复改为LOWER(album.title) LIKE '%led zepelin%'，执行得到0。名称筛选从艺术家改成专辑标题且从等值变为子串，用户未确认这种业务改义；无绑定/改写，也未按待确认Led Zeppelin目标得14。"),
 20: ("AI建议有条件通过", "V1实际前两次候选为正确MPEG audio媒体FK JOIN/子查询，但被守卫拦；第三次写track.media_type_id=1并执行3034。已有完整媒体事实确实ID1=MPEG audio，PK/FK使当前数据下该SQL与参考语义对应，这一事实比仅数值相同更强。但真实NLU绑定/patch/rewrite为空，provider user payload未提供完整ID-名称配对证据，仅各列sample_values，修复ID来源未验证。仅在人工确认拼写目标和ID映射依据后查询条件通过，不把3034判为有限候选消歧链全通过。"),
 24: ("AI建议通过", "V1实际artist.name=Iron Maiden绑定正确，album→artist真实主键FK内连接COUNT(*)与原参考相同，连接不复制专辑，保存结果21。"),
 30: ("证据不足", "原题显式[2030-01-01,2030-12-31)，冻结gold错误扩大到2031-01-01，仍保留参考争议，正式系统评分不能依坏参考判定。V1实际NLU对‘之间’unmatched，没有国家追问；随后真实意图提取将end改成2031，SQL也<2031，实际0与错误gold相同只是未来空数据巧合。独立题意观察为日期上界扩大，应人工纠错；不为了系统得0通过而重写题面。"),
}


def path(name: str) -> Path:
    p = (ROOT / name).resolve()
    if not p.is_relative_to(ROOT) or p.name.startswith(".env"):
        raise ValueError("Unsupported evidence path: " + name)
    return p


def read(name: str):
    return json.loads(path(name).read_text(encoding="utf-8-sig"))


def sha(name: str) -> str:
    return sha256(path(name).read_bytes()).hexdigest()


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def sql_proof(sql: str | None) -> dict:
    if not sql:
        return {"actual_sql_present": False, "no_new_sql_execution": True}
    import sqlglot
    from sqlglot import exp
    tree = sqlglot.parse_one(sql, read="postgres")
    return {"actual_sql_present": True, "actual_tables": sorted({t.name for t in tree.find_all(exp.Table)}),
            "actual_predicate_expressions": [p.sql(dialect="postgres") for p in tree.find_all(exp.Predicate)],
            "actual_aggregate_expressions": [a.sql(dialect="postgres") for a in tree.find_all(exp.AggFunc)],
            "has_grouping": tree.args.get("group") is not None,
            "limit": tree.args.get("limit").sql(dialect="postgres") if tree.args.get("limit") else None,
            "no_new_sql_execution": True, "proof_is_not_a_recalculated_score": True}


def inspect_provider(response: dict, turn_dir: Path, require_archive: bool) -> list[dict]:
    records = []
    for step in response.get("steps", []):
        pointer = step.get("output_summary", {}).get("provider_capture") if step.get("name") == "llm" else None
        if not pointer:
            continue
        source = path(pointer)
        if source.parent != CAPTURE_ROOT or not UUID.fullmatch(source.name):
            raise ValueError("Provider pointer failed anchored V2-root/UUID check: " + pointer)
        data = read(pointer)
        if data.get("trace_id") != response.get("trace_id"):
            raise ValueError("Actual provider trace_id does not match saved response")
        archive = turn_dir / "provider" / source.name
        archive_exists = archive.is_file()
        if require_archive and not archive_exists:
            raise ValueError("Wait for root's independent provider supplement: " + rel(archive))
        if archive_exists and sha(rel(archive)) != sha(pointer):
            raise ValueError("Supplement copy is not exact original capture")
        messages = data.get("request", {}).get("messages", [])
        systems = [m["content"] for m in messages if m.get("role") == "system"]
        payloads = []
        for message in messages:
            if message.get("role") != "user":
                continue
            try:
                value = json.loads(message.get("content", ""))
            except (ValueError, TypeError):
                continue
            if isinstance(value, dict):
                # Full source is read/hash preserved; concise observations do not reconstruct prompts.
                payloads.append({"keys": sorted(value), "question": value.get("question"),
                                 "previous_sql": value.get("previous_sql"), "technical_error": value.get("technical_error"),
                                 "intent": value.get("intent"), "input": value.get("input"),
                                 "mention": value.get("mention"), "candidates": value.get("candidates")})
        content = (data.get("response", {}).get("choices") or [{}])[0].get("message", {}).get("content")
        records.append({"file": rel(archive) if archive_exists else pointer,
                        "sha256": sha(pointer), "original_capture_file": pointer,
                        "supplement_archive_exists": archive_exists, "trace_id_verified": True,
                        "observed_system_character_counts": [len(s) for s in systems],
                        "actual_system_role_prefixes": [s[:120] for s in systems],
                        "actual_model": data.get("response", {}).get("model"),
                        "actual_user_payload_observations": payloads,
                        "actual_provider_output": content})
    return records


def main() -> int:
    global RUN, SCORE, CAPTURE_ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=["V1", "V2"], default="V2")
    parser.add_argument("--final", action="store_true", help="Require completed immutable score and exact archived providers")
    args = parser.parse_args()
    version = args.version
    RUN = EXP + f"/runtime_eval/runs/{version}-001"
    SCORE = EXP + f"/runtime_eval/runs/{version}-001-scores.json"
    CAPTURE_ROOT = (ROOT / EXP / f"runtime_eval/provider-captures/{version}-001").resolve()
    if sha(LABEL) != EXPECTED_SHA:
        raise ValueError("Frozen DEV labels changed")
    label_rows = [json.loads(l) for l in path(LABEL).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    source = {x["id"]: x for x in label_rows if x["task"] == "01"}
    if len(source) != 30 or any(x.get("split") != "dev" for x in source.values()):
        raise ValueError("Only exact task01 DEV30 is allowed")
    first = read(V0_REVIEW)
    prior = {x["id"]: x for x in first["cases"]}
    score = read(SCORE) if path(SCORE).is_file() else None
    if args.final and not score:
        raise ValueError("Final V2 original score not ready")
    if score and (score.get("labels_sha256") != EXPECTED_SHA or score.get("version") != version or len(score.get("cases", [])) != 60
                  or any(c.get("outcome") in {None, "not_started", "running"} for c in score["cases"])):
        raise ValueError("Original final score mismatch/incomplete")
    scores = {x["id"]: x for x in score["cases"]} if score else {}
    materials = [LABEL, V0_REVIEW, "data/catalog/chinook.yaml", "data/rules/metric_definitions.json",
                 "data/aliases/aliases-d2-reviewed.csv", EXP + "/materials/readonly_live_facts.json",
                 EXP + f"/runtime_eval/{version}-code-snapshot.json", "qa_agent/pipeline.py", "qa_agent/sql/generator.py", "ui/app.py"]
    material_hashes_before = {name: sha(name) for name in materials}
    # Actually read the corroborating directory/schema, metric rules and alias state,
    # not only file titles. No imports of business code and no live DB connections.
    material_bytes_read = {name: len(path(name).read_bytes()) for name in materials}
    import yaml
    catalog = yaml.safe_load(path("data/catalog/chinook.yaml").read_text(encoding="utf-8-sig"))
    facts = read(EXP + "/materials/readonly_live_facts.json")
    rules = read("data/rules/metric_definitions.json")
    album = next(t for t in catalog["tables"] if t["name"] == "album")
    artist = next(t for t in catalog["tables"] if t["name"] == "artist")
    pk_fk_proof = {"album_primary_key": album["primary_key"], "artist_primary_key": artist["primary_key"],
                   "album_id_nullable": next(c for c in album["columns"] if c["name"] == "album_id")["nullable"],
                   "album_foreign_keys": album["foreign_keys"],
                   "reason": "PK uniqueness/nonNULL and FK many-to-one prove album COUNT(*),COUNT(album_id),COUNT(DISTINCT album_id) equivalence for these unchanged inner FK joins"}
    cases, evidence_hashes, missing = [], dict(material_hashes_before), []
    for number in range(1, 31):
        case_id = f"sp01-{number:02}"
        label, previous = source[case_id], prior[case_id]
        checkpoint_name = RUN + f"/cases/{case_id}/checkpoint.json"
        checkpoint = read(checkpoint_name)
        if checkpoint.get("outcome") in {None, "running", "not_started"}:
            raise ValueError("Unfinished V2 task01 case: " + case_id)
        actual_turns, providers = [], []
        for turn in checkpoint["turns"]:
            turn_dir = path(RUN + f"/cases/{case_id}/turns/{turn['index']:03}")
            raw_name = rel(turn_dir / "response.raw.json")
            request_name = rel(turn_dir / "request.json")
            raw = read(raw_name)
            actual = json.loads(raw["body"]) if isinstance(raw.get("body"), str) else raw["body"]
            if actual != turn["response"]:
                raise ValueError("Raw/checkpoint mismatch: " + raw_name)
            capture = inspect_provider(actual, turn_dir, args.final)
            providers.extend(capture)
            for name in [raw_name, request_name, checkpoint_name]:
                evidence_hashes[name] = sha(name)
            for p in capture:
                evidence_hashes[p["file"]] = p["sha256"]
            actual_turns.append({"index": turn["index"], "phase": turn.get("phase"), "request": read(request_name),
                                 "response": actual, "raw_response_file": raw_name,
                                 "raw_response_sha256": sha(raw_name), "raw_checkpoint_match": True,
                                 "provider_count": len(capture)})
        final = actual_turns[-1]["response"]
        nlu = final.get("metadata", {}).get("nlu", {})
        verdict, reason = V1_DIFFERENT_OPINIONS.get(number, OPINIONS[number]) if version == "V1" else OPINIONS[number]
        if version == "V1":
            reason = reason.replace("V2", "V1")
        ref_reason = REFERENCE_NOTES[number]
        actual_sql = final.get("sql")
        proof = sql_proof(actual_sql)
        if number in {2, 13, 16, 24}:
            proof["PK_FK_count_equivalence"] = pk_fk_proof
        if number == 20:
            proof["saved_complete_media_type_rows"] = facts["media_types"]["result"]["rows"]
            proof["snapshot_unique_name_not_schema_unique_constraint"] = True
        if number in {9, 27, 28}:
            proof["candidate_only_gate"] = {"level": (final.get("clarification") or {}).get("level"),
                                          "options": (final.get("clarification") or {}).get("options"),
                                          "no_auto_filters": not (final.get("intent") or {}).get("filters"),
                                          "no_SQL_executed": actual_sql is None}
        if number == 30:
            proof["direct_user_condition_observation"] = {
                "user_lower_bound": "2030-01-01", "user_exclusive_upper_bound": "2030-12-31",
                "frozen_gold_exclusive_upper_bound": "2031-01-01", "reference_boundary_matches_user": False,
                "actual_country_clarification_has_no_basis_in_question": version == "V2",
                "actual_SQL_exclusive_upper_bound": "2031-01-01" if version == "V1" else None,
                "actual_SQL_matches_user_explicit_exclusive_upper_bound": False if version == "V1" else "未执行SQL",
                "actual_mention": [m.get("original_text") for m in nlu.get("mentions", [])],
                "observed_dimension_verdict": "AI发现错误",
                "formal_system_scoring_under_wrong_reference": "暂不能确定；保留原冻结自动评分"}
        if number in {4, 17}:
            proof["query_vs_binding_chain"] = {"France_SQL_and_saved5": True, "verified_NLU_binding_present": False,
                                               "explicit_rewrite_present": False, "pipeline_full_acceptance_not_proven": True}
        if version == "V1" and number in {5, 18}:
            proof["technical_repair_business_predicate_changed"] = {"before": "artist.name", "after": "album.title",
                                                                    "user_confirmed_field_change": False,
                                                                    "actual_saved_result": 0,
                                                                    "is_successful_execution_not_semantic_success": True}
        if version == "V1" and number == 20:
            proof["foreign_key_id_snapshot_mapping"] = {"actual_id": 1, "stored_source_fact_name": "MPEG audio file",
                                                         "mapped_in_verified_NLU_binding": False,
                                                         "binding_or_rewrite_whole_pipeline_not_proven": True}
        related = {"frozen_label": LABEL, "original_score": SCORE if score else "原评分尚未完成",
                   "checkpoint": checkpoint_name, "actual_raw_response": actual_turns[-1]["raw_response_file"],
                   "catalog": "data/catalog/chinook.yaml", "confirmed_business_rules": "data/rules/metric_definitions.json",
                   "actual_alias_table": "data/aliases/aliases-d2-reviewed.csv", "V0_reference_ai_review": V0_REVIEW,
                   "source_facts": EXP + "/materials/readonly_live_facts.json", "version_code_snapshot": EXP + f"/runtime_eval/{version}-code-snapshot.json"}
        if number in {4, 17, 19}:
            related["UI_renderer"] = "ui/app.py"
        cases.append({
            "id": case_id, "task": "01", "category": label["category"],
            "ai_review_scope": f"independent_all30_{version}_actual_input_SQL_NLU_provider_review_no_new_predictions",
            "original_scorable": label.get("scorable") is True,
            "original_automatic_complete": scores.get(case_id, {}).get("automatic_complete") if score else "原固定评分尚未完成",
            "original_automatic_score": scores.get(case_id) if score else None,
            "question": label["input"], "reference_ai_verdict": previous["reference_ai_verdict"],
            "system_ai_verdict": verdict, "judgment_reason": reason,
            "reference_review": {"verdict": previous["reference_ai_verdict"], "reason": ref_reason,
                                 "reused_frozen_reference_judgment_from": V0_REVIEW,
                                 "prior_original_combined_reason_unchanged": previous["judgment_reason"],
                                 "source_label_re_read": True, "reference_human_review_status": "pending_human_review"},
            "actual_system_review": {"verdict": verdict, "reason": reason, "original_score_not_used_to_infer_verdict": True},
            "reference_human_review_status": "pending_human_review", "human_review_status": "pending_human_review",
            "gold_sql_unchanged": label.get("gold_sql"), "gold_result_from_preparation_unchanged": label.get("gold_result"),
            "actual_final_status": final.get("status"), "actual_final_sql": actual_sql,
            "actual_final_table": final.get("table"), "actual_final_intent": final.get("intent"),
            "actual_answer": final.get("answer"), "actual_rewritten_question": final.get("rewritten_question"),
            "actual_nlu_bindings": nlu.get("bindings"), "actual_nlu_patches": nlu.get("patches"),
            "actual_controller_outcome": checkpoint.get("outcome"),
            "actual_candidate_options": (final.get("clarification") or {}).get("options"),
            "independent_static_and_saved_result_proof": proof,
            "dimension_results": {"SQL_or_initial_candidate_behavior_correct_under_reference": number in {1,2,3,4,8,9,11,13,15,16,17,19,21,23,24,26,27,29} or (version == "V1" and number == 20),
                                  "explicit_binding_chain_correct": ("不适用：初始多候选应保持未绑定" if number in {9,27,28}
                                                                     else bool(nlu.get("bindings"))),
                                  "rewritten_question_available": bool(final.get("rewritten_question")),
                                  "whole_pipeline_not_inferred_from_automatic_result": True,
                                  "this_case_actual_browser_test": "未新增运行；仅读已有API输出及UI源码"},
            "provider_captures": providers, "actual_turns_read": actual_turns, "evidence_files": related,
            "needs_human_confirmation": previous.get("needs_human_confirmation", [])
                + [f"本轮逐条AI意见不代替人审；{version}原自动分数与AI维度意见分别保留。"],
            "formal_score_changed": False,
        })
    if score:
        evidence_hashes[SCORE] = sha(SCORE)
    material_hashes_after = {name: sha(name) for name in materials}
    if material_hashes_before != material_hashes_after:
        raise ValueError("Reference/business evidence changed during the offline review")
    state = f"FINAL_ACTUAL_{version}_REVIEW" if args.final else f"INTERIM_ACTUAL_{version}_TASK01_REVIEW_ARCHIVE_OR_SCORE_PENDING"
    filename = version.lower() + ("-task01-full-review" if args.final else "-task01-interim-evidence-review")
    snapshot = read(EXP + f"/runtime_eval/{version}-code-snapshot.json")
    current_source_matches_snapshot = {
        name: (material_hashes_after[name] == snapshot["files"][name] if name in snapshot.get("files", {})
               else "未被此快照覆盖，不能由本快照判断")
        for name in ["qa_agent/pipeline.py", "qa_agent/sql/generator.py", "ui/app.py"]}
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "purpose": f"逐条{version}实际系统回答AI预审；不重计固定自动分数、不改变原参考、不替人审",
              "version": version, "review_state": state, "reviewed_case_count": 30,
              "review_command": [sys.executable, "-B", *sys.argv], "generator_sha256": sha(rel(Path(__file__).resolve())),
              "new_model_calls": 0, "new_api_requests": 0, "new_database_queries": 0, "holdout_content_read": False,
              "original_task01_summary": score["summary"]["groups"]["task:01"] if score else None,
              "reference_ai_counts": dict(Counter(c["reference_ai_verdict"] for c in cases)),
              "system_ai_counts": dict(Counter(c["system_ai_verdict"] for c in cases)),
              "original_score_sha256": sha(SCORE) if score else None, "unchanged_labels_sha256": EXPECTED_SHA,
              "reference_issue_candidates_beyond_previous11_annotation_pending": ["sp01-03", "sp01-12", "sp01-25", "sp01-30"],
              "original49_scorable11_pending_counts_unchanged": True,
              "original_task01_26_scorable4_pending_counts_unchanged": True,
              "provider_records_read": sum(len(c["provider_captures"]) for c in cases),
              "raw_responses_read": sum(len(c["actual_turns_read"]) for c in cases), "missing_evidence": missing,
              "materials_bytes_actually_read": material_bytes_read, "materials_unchanged": material_hashes_before == material_hashes_after,
              "current_source_at_review_matches_frozen_version": current_source_matches_snapshot,
              "source_version_note": "历史运行行为以该版实际raw/provider和snapshot实际覆盖字段为准。根流程恢复V1使V2 pipeline当前SHA不同；ui/app.py未被此snapshot覆盖，不能据缺键判断UI变化。UI原D3验收另有自身SHA/截图证据。",
              "rules_region_actual": rules["general"]["region"], "PK_FK_count_equivalence_actual_directory": pk_fk_proof,
              "cases": cases, "formal_score_changed": False, "human_review_status": "pending_human_review",
              "evidence_sha256": evidence_hashes,
              "limits": [f"{version}逐项AI预审意见分布不是新通过率；正式自动结果沿用原scores.json。",
                         "原参考争议保留；结果相同不证明地区/时间含义正确。",
                         "candidate_only只验证初始澄清，不伪称续答/SQL成功；未新增逐题浏览器测试。",
                         "04/17统一按查询与绑定链分别判断，原V0不同意见不覆盖。",
                         "30坏参考导致正式判断暂不能确定；V1实际日期上界扩大／V2实际无依据国家追问各自另列观察。"]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / (filename + ".json")).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    def link(name: str) -> str:
        if not path(name).is_file():
            return "未取得：" + name
        return "[" + name + "](<" + Path(os.path.relpath(path(name), OUT)).as_posix() + ">)"
    lines = [f"# {version}专项①全部30条实际回答AI预审", "", "状态：" + state + "；全部人工仍pending。", "",
             "原固定自动结果：" + (score["summary"]["groups"]["task:01"]["correct_over_scorable_tasks"] if score else "尚未完成；不写预期分数"),
             "原固定评分文件：" + (link(SCORE) if score else "尚未取得"),
             "实际读取30原始响应、provider " + str(report["provider_records_read"]) + "份；本次0API/0模型/0SQL。",
             "参考AI分布：" + json.dumps(report["reference_ai_counts"], ensure_ascii=False),
             "系统AI分布：" + json.dumps(report["system_ai_counts"], ensure_ascii=False) + "；AI分布不是重计成绩。", ""]
    for c in cases:
        lines += ["## " + c["id"] + " · " + c["category"], "", "原题：" + c["question"],
                  "参考判断：" + c["reference_ai_verdict"] + "；保留V0冻结参考意见与新争议。",
                  "系统判断：**" + c["system_ai_verdict"] + "**；" + c["judgment_reason"],
                  "```json", json.dumps({k:c[k] for k in ["gold_sql_unchanged", "gold_result_from_preparation_unchanged", "actual_final_status", "actual_final_sql", "actual_final_table", "actual_answer", "actual_nlu_bindings", "actual_nlu_patches", "actual_rewritten_question", "actual_candidate_options", "independent_static_and_saved_result_proof", "original_automatic_score"]},ensure_ascii=False,indent=2), "```",
                  "证据：" + link(c["evidence_files"]["checkpoint"]) + "；" + link(c["evidence_files"]["actual_raw_response"])]
        for p in c["provider_captures"]:
            lines.append("- " + link(p["file"]) + "；SHA=" + p["sha256"] + "；trace核验=true；实际system字符=" + str(p["observed_system_character_counts"]))
        lines += ["", "仍需人工确认：" + "；".join(c["needs_human_confirmation"]), "人工状态：pending_human_review；未填写签名/人工确认日期。", ""]
    lines += ["## 原材料与限制", ""] + ["- " + link(m) + "；SHA=" + h for m,h in material_hashes_after.items()] + ["- " + note for note in report["limits"]]
    (OUT / (filename + ".md")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k:report[k] for k in ["review_state", "reviewed_case_count", "raw_responses_read", "provider_records_read", "reference_ai_counts", "system_ai_counts", "original_score_sha256", "materials_unchanged"]},ensure_ascii=False,indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print("V2 evidence review failed: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
