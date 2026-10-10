"""Export human review material; record IDs explicitly accepted by a human."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eval.dataset import DEFAULT_DATASET, ROOT, load_dataset, reviewed, review_hash


def export_review(items: list[dict], directory: Path, dataset: Path = DEFAULT_DATASET) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    fields = ["id", "split", "category", "family_id", "question", "gold_sql", "gold_result", "review_status", "human_notes"]
    with (directory / "gold_review.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in items:
            writer.writerow({**{key: item[key] for key in fields[:6]}, "gold_result": json.dumps(item["gold_result"], ensure_ascii=False),
                             "gold_sql": item["gold_sql"], "review_status": "accepted" if reviewed(item) else "needs_human_review", "human_notes": ""})
    lines = ["# 30 道 Chinook gold 人工复核表", "", "请先对照问题、SQL 和实际结果，确认筛选值、单位、日期边界、排序及并列处理。",
             "标注结果来自真实数据库；这些题尚未获得人工认可时，只能报告草稿状态。",
             "本文包含保留题 gold，用于一次性审核。保留题不能用于调提示词或日常系统试跑。", "",
             "接受题目后执行，例如：", "", "```powershell",
             f'.\\.venv\\Scripts\\python.exe scripts/review_gold.py --dataset "{dataset.as_posix()}" '
             f'--output "{directory.as_posix()}" --accept sql-01,sql-02 --reviewer A',
             "```", "", "该命令记录人工接受，不替代核对；结果或问题修改后，接受记录自动失效。", ""]
    for item in items:
        status = "已人工接受" if reviewed(item) else "等待人工审核"
        lines += [f"## {item['id']} · {item['split']} · {item['category']} · {status}", "", item["question"], "",
                  "```sql", item["gold_sql"], "```", "", "实际标准结果：", "", "```json",
                  json.dumps(item["gold_result"], ensure_ascii=False, indent=2), "```", "",
                  f"结果列：{', '.join(item['gold_columns'])}；有序比较：{item['ordered']}；金额列：{item['monetary_columns']}。", "",
                  "人工检查：问题与 SQL 一致 □　来源/单位/日期/排序正确 □　结果已核对 □", ""]
    (directory / "gold_review.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=ROOT / "eval/datasets/review")
    parser.add_argument("--accept", help="由人工已经复核的 ID，以逗号分隔；不自动接受整套标注")
    parser.add_argument("--reviewer", help="实际审核人的姓名或团队标识")
    args = parser.parse_args()
    items = load_dataset(args.dataset)
    if args.accept:
        if not args.reviewer or not args.reviewer.strip():
            parser.error("--accept 必须填写实际人工审核者 --reviewer")
        accepted = {value.strip() for value in args.accept.split(",") if value.strip()}
        unknown = accepted - {item["id"] for item in items}
        if unknown:
            parser.error("未知题目 ID：" + ", ".join(sorted(unknown)))
        for item in items:
            if item["id"] in accepted:
                item["gold_review"] = {"status": "accepted", "reviewer": args.reviewer.strip(),
                                       "accepted_at_utc": datetime.now(timezone.utc).isoformat(),
                                       "content_sha256": review_hash(item)}
        args.dataset.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items), encoding="utf-8")
    export_review(items, args.output, args.dataset)
    print(f"审核表：{args.output / 'gold_review.md'}；已人工接受 {sum(reviewed(item) for item in items)}/{len(items)}。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
