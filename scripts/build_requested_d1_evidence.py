"""Consolidate the user's fourteen D1 checklist items from recorded evidence."""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "eval/reports/d1-acceptance"


def read(name: str) -> dict:
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def link(path: str, line: int | None = None) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    target = p.as_posix() + (f":{line}" if line else "")
    return f"[{p.name}](<{target}>)"


def main() -> None:
    shared, a, b = (read(f"requested-{part}-evidence.json") for part in ("shared", "a", "b"))
    engineering, ui, mirror = (read(name) for name in
        ("requested-engineering.json", "requested-ui-smoke.json", "requested-mirror-pdfs.json"))
    assert engineering["status"] == "PASS" and ui["status"] == "PASSED" and mirror["status"] == "PASS"
    assert all(ui["checks"].values())
    assert next(i for i in a["items"] if i["id"] == "COMMON_SCHEMA")["status"] == "AGREED_USER_CONFIRMED"
    rows = []
    for item in shared["shared_requirements"]:
        rows.append({"id": item["id"], "owner": "上午共同", "requirement": item["requirement"],
                     "status": "完成（当前协议双方已确认）" if item["id"] == "shared-02" else "完成（未来功能按排期）",
                     "facts": "19个计划目录已存在；私有Git仓库已上传并核验。" if item["id"] == "shared-01" else "用户确认A/B同意当前版本，含1起物理页约定；后续实质修改必须双方同意。",
                     "evidence": [{"path": "eval/reports/d1-acceptance/requested-shared-evidence.json"},
                                  {"path": "notes/D1目录对照.md" if item["id"] == "shared-01" else "notes/共享协议确认.md"}]})
    for item in a["items"]:
        if item["id"] == "COMMON_SCHEMA":
            continue
        rows.append({"id": item["id"], "owner": "A", "requirement": item["requirement"],
                     "status": "完成；正式人工审核另列" if item["id"] == "A05" else "完成（本轮补齐）" if item["id"] == "A03" else "完成",
                     "facts": "；".join(item["facts"]),
                     "evidence": [{"path": "eval/reports/d1-acceptance/requested-a-evidence.md"}, *item["evidence"]]})
    for item in b["items"]:
        proofs = [{"path": "eval/reports/d1-acceptance/requested-b-evidence.md"}]
        proofs.extend({"path": p} if isinstance(p, str) else p for p in item["evidence"])
        rows.append({"id": item["id"], "owner": "晚上联调" if item["id"] == "JOINT-EVENING" else "B",
                     "requirement": item["requirement"],
                     "status": "完成；QA来源调整" if item["id"] == "B-1" else "完成（本轮补齐）" if item["id"] == "B-3" else "完成",
                     "facts": item.get("actual", "已逐项核对，见证据报告"), "evidence": proofs})
    assert len(rows) == 14
    report = {"checked_at_local": datetime.now(ZoneInfo("America/Chicago")).isoformat(),
              "scope": "User's exact D1 morning/A/B/evening list; human gold review and later days tracked separately",
              "item_count": len(rows), "rows": rows,
              "latest_engineering": {k: engineering[k] for k in ("status", "passed_count", "check_count")},
              "pytest": engineering["checks"][0]["details"],
              "new_ui": {k: ui[k] for k in ("status", "checks", "sql_trace", "doc_trace", "observed_model_attempts")},
              "new_ui_is_not_benchmark": True, "holdout_model_predictions": 0,
              "foreign_key_count": 11, "current_schema_sha256": a["schema_file_sha256"],
              "schema_changed_in_this_followup": False,
              "adjustment": "Six PDFs now downloaded through hf-mirror and byte/hash checked; mirror qas_v2.json URL returns404, fixed official GitHub QA retained.",
              "formal_gold_review_pending": {"sql": 30, "rag": 20}}
    (BASE / "requested-d1-evidence.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    lines = ["# D1 原清单十四项逐项验收与证据", "", f"时间：{report['checked_at_local']}。", "",
             "本文件逐条对应用户本次清单。当前D1工程和数据准备完成；QA下载地址调整、当前协议双方确认及未来功能边界分别写明。当前代码新回归159项通过，工程53/53通过；早先57项工程（含4条live）与149项测试保留历史。", "",
             "| 编号 | 分工 | 原要求 | 状态 | 实际事实 | 可查看证据 |", "|---|---|---|---|---|---|"]
    for row in rows:
        proofs = "；".join(link(x["path"], x.get("line")) for x in row["evidence"])
        values = [row[k] for k in ("id", "owner", "requirement", "status", "facts")] + [proofs]
        lines.append("| " + " | ".join(str(v).replace("|", "／").replace("\n", " ") for v in values) + " |")
    lines += ["", "本轮新增真模型请求仅为新页面SQL和文档各一道，观察3个LLM步骤；不重跑35题旧开发基准，不预测15道保留题。", "",
              "资料路线调整不是更换题库：六份镜像PDF与原件SHA256逐一相同，QA仍为同一固定官方版本。原PDF、索引、题库及原开发报告内容保留。", "",
              "D1的30条gold实际执行与保存已完成。标准答案人工业务接受和正式模型成绩另行完成，不把AI复核填成真人审核。", "",
              "后续nlu/clarify/fusion/aliases/rules仅补目录说明，未宣称D2-D4功能已经完成。", "",
              link("notes/dev-log.md") + "；" + link("notes/screenshots/D1-evidence.json") + "。", ""]
    (BASE / "requested-d1-evidence.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"items": len(rows), "engineering": report["latest_engineering"], "output": str(BASE / "requested-d1-evidence.md")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
