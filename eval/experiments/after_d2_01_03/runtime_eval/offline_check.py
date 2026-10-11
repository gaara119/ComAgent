"""No network/DB/model: validate every frozen gold AST and simulator safety tests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from common import HERE, digest, load_cases, utcnow, write_new
from runner import check
from scorer import load_post_results, sql_contract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--post-results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = load_cases(args.cases)
    errors = []
    count = 0
    for case in cases:
        queries = [("main", case.get("gold_sql"))]
        queries.extend((f"post_completion_{index+1}", item.get("gold_sql")) for index, item in enumerate((case.get("controller") or {}).get("post_completion_turns") or []))
        for name, sql in queries:
            if sql:
                count += 1
                try:
                    sql_contract(sql)
                except Exception as exc:
                    errors.append({"id": case["id"], "query": name, "error": str(exc)})
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_runtime_eval.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    posts = load_post_results(args.post_results)
    output = {"checked_at": utcnow(), "labels_sha256": digest(args.cases), "contract": check(cases),
              "unit_checks_run": result.testsRun, "unit_checks_passed": result.wasSuccessful(),
              "gold_asts_parsed": count-len(errors), "gold_ast_total": count, "gold_ast_errors": errors,
              "saved_post_results_loaded": sum(len(value) for value in posts.values()),
              "api_prediction_calls": 0, "provider_calls": 0, "database_queries": 0,
              "meaning": "Evaluator/controller preparation checks only; fabricated unit fixtures are not system results"}
    write_new(args.output, output)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if errors or not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
