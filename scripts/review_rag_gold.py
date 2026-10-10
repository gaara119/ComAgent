"""Export RAG gold and record the user's completed human review."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.rag_dataset import DEFAULT_DATASET, load_dataset, review_hash, reviewed, write_review_table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--accept", help="Comma-separated IDs already reviewed by a human")
    parser.add_argument("--reviewer", help="Name or team role of the human reviewer")
    args = parser.parse_args()
    items = load_dataset(args.dataset)
    if args.accept:
        if not args.reviewer or not args.reviewer.strip():
            parser.error("--accept requires the actual human --reviewer")
        ids = {value.strip() for value in args.accept.split(",") if value.strip()}
        known = {item["id"] for item in items}
        if ids - known:
            parser.error("Unknown RAG IDs: " + ", ".join(sorted(ids - known)))
        stamp = datetime.now(timezone.utc).isoformat()
        for item in items:
            if item["id"] in ids:
                item["gold_review"] = {"status": "accepted", "reviewer": args.reviewer.strip(),
                                       "reviewed_at_utc": stamp, "content_sha256": review_hash(item)}
        args.dataset.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items), encoding="utf8")
    path = write_review_table(items)
    print(json.dumps({"review_table": str(path), "accepted": sum(reviewed(x) for x in items),
                      "pending": sum(not reviewed(x) for x in items)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
