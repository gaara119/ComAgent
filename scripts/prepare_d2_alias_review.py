"""Prepare a concrete proposed alias selection; leave every row pending."""
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    path = ROOT / "data/aliases/aliases.csv"
    snapshot = ROOT / "eval/artifacts/d2/aliases-74-model-draft.csv"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot.exists():
        snapshot.write_bytes(path.read_bytes())
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
        fields = list(rows[0])
    with (ROOT / "data/aliases/aliases-italy-draft.csv").open(encoding="utf-8-sig",newline="") as stream:
        supplement = list(csv.DictReader(stream))
    supplement.append({"standard_value":"Rock And Roll", "column":"genre.name", "alias":"摇滚",
                       "source":"方案.md:§3.6.3 ambiguous value example", "review_status":"pending", "reviewer":"",
                       "alias_id":"a-d2-plan-rock-and-roll"})
    existing = {r["alias_id"] for r in rows}
    rows += [r for r in supplement if r["alias_id"] not in existing]
    with path.open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    excluded = {("Metallica","金属"), ("Rock And Roll","节奏摇滚"), ("Iron Maiden","铁处女")}
    approved = [r["alias_id"] for r in rows if (r["standard_value"],r["alias"]) not in excluded]
    rejected = [r["alias_id"] for r in rows if (r["standard_value"],r["alias"]) in excluded]
    proposal={"created_at_utc":datetime.now(timezone.utc).isoformat(),"expected_sha256":sha256(path.read_bytes()).hexdigest(),
              "status":"pending_human_review","approve_ids":approved,"reject_ids":rejected,
              "approved_rows_proposal":[r for r in rows if r["alias_id"] in approved],
              "rejected_rows_proposal":[r for r in rows if r["alias_id"] in rejected]}
    (ROOT / "eval/artifacts/d2/aliases-review-selection.json").write_text(json.dumps(proposal,ensure_ascii=False,indent=2),encoding="utf8")
    grouped={}
    for r in rows:
        grouped.setdefault((r["column"],r["standard_value"]),[]).append(r)
    lines=["# D2 别名表人工审核提案","","状态：全部 pending，尚未进入运行值索引。", "",
           f"建议通过 {len(approved)} 项，建议拒绝 {len(rejected)} 项；审核必须对应当前 CSV SHA256：`{proposal['expected_sha256']}`。",
           "", "精确匹配限定真实表字段；同一词对应多个值时保留候选并澄清。尤其“摇滚/摇滚乐”同时映射 Rock 与 Rock And Roll，不替用户选一个。", "",
           "| 字段 | 真实标准值 | 建议通过的别名 | 建议拒绝 |", "|---|---|---|---|"]
    for (column,value), rs in grouped.items():
        good="、".join(r["alias"] for r in rs if r["alias_id"] in approved)
        bad="、".join(r["alias"] for r in rs if r["alias_id"] in rejected)
        lines.append(f"| {column} | {value} | {good} | {bad} |")
    lines += ["", "拒绝理由：泛称“金属”不能唯一代表 Metallica 乐队；“节奏摇滚”不足以唯一说明 Rock And Roll；“铁处女”不采用为本项目的默认中文乐队名。", "",
              "别名来自已实跑 DeepSeek 初稿（Italy 为单独模型补充）；“摇滚”多候选对应关系来自总计划的明确例子。上述建议不代表人工已批准。", "",
              "- [aliases.csv](../data/aliases/aliases.csv)", "- [具体行 ID 与审核哈希](../eval/artifacts/d2/aliases-review-selection.json)", ""]
    (ROOT / "notes/d2-alias-review.md").write_text("\n".join(lines),encoding="utf8")
    print(json.dumps({"pending":len(rows),"proposed_approve":len(approved),"proposed_reject":len(rejected)},ensure_ascii=False))


if __name__=="__main__": main()
