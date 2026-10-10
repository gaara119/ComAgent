"""Reproduce D1 engineering acceptance; default mode makes no LLM requests.

Run after the API, UI and v2 dense index are ready. The optional --live flag
sends four explicitly labelled additional smoke questions to /api/chat.
Existing reports are preserved; select another --output for a repeated run.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx
import numpy as np
from PIL import Image

from qa_agent.config import get_settings, sanitize_error
from qa_agent.rag.embeddings import get_embedder
from qa_agent.rag.index import INDEX_VERSION, load_index
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import SQLTimeoutError, execute_sql
from qa_agent.sql.validator import SQLValidationError, validate_sql


class Acceptance:
    def __init__(self, args):
        self.args = args
        self.settings = get_settings()
        self.started = datetime.now(timezone.utc)
        self.stamp = self.started.strftime("%Y%m%dT%H%M%S%fZ")
        self.checks = []
        self.documents = []
        self.git_commit = self.git("rev-parse", "HEAD")
        self.initial_dirty = bool(self.git("status", "--porcelain"))
        self.live_prediction_count = 0
        self.live_llm_steps = 0
        self.report_path = args.output.resolve()
        self.report_path.parent.mkdir(parents=True, exist_ok=True)

    def safe_text(self, value) -> str:
        # Unlike user-facing sanitize_error, command logs must retain their full
        # length, including pytest's final summary. Redact before writing them.
        text = str(value)
        secrets = (self.settings.llm_api_key, self.settings.db_url, self.settings.aw_db_url,
                   os.getenv("POSTGRES_PASSWORD", ""), os.getenv("DB_READER_PASSWORD", ""))
        for secret in sorted(filter(None, secrets), key=len, reverse=True):
            text = text.replace(secret, "[redacted]")
        text = re.sub(r"postgres(?:ql)?://[^\s]+", "postgresql://[redacted]", text)
        text = re.sub(r"(?i)(bearer\s+)[^\s\"']+", r"\1[redacted]", text)
        return re.sub(r"\bsk-[A-Za-z0-9_-]+", "[redacted]", text)

    def safe(self, value):
        if isinstance(value, str):
            return self.safe_text(value)
        if isinstance(value, dict):
            return {str(key): self.safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.safe(item) for item in value]
        return value

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=30)
        return result.stdout.strip() if result.returncode == 0 else None

    def check(self, name, function):
        start = perf_counter()
        try:
            details = function()
            status = "PASS"
        except Exception as exc:
            details = {"error_type": type(exc).__name__, "error": sanitize_error(exc, self.settings)}
            status = "FAIL"
        record = {"id": name, "status": status, "latency_ms": round((perf_counter() - start) * 1000),
                  "details": self.safe(details)}
        self.checks.append(record)
        print(f"[{status}] {name}", flush=True)
        return record

    def command(self, name, command, *, timeout=600):
        environment = dict(os.environ)
        # Existing integration fixtures read the legacy DB_URL. Use the actual
        # already-authorized SELECT-only DSN without displaying it in arguments.
        if self.settings.db_url:
            environment["DB_URL"] = self.settings.db_url
        environment["PYTHONIOENCODING"] = "utf-8"
        environment["PYTHONUNBUFFERED"] = "1"
        log_path = self.report_path.parent / f"engineering-{self.stamp}-{name}.txt"
        try:
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", env=environment, timeout=timeout)
            output = self.safe_text(result.stdout + result.stderr)
        except subprocess.TimeoutExpired as exc:
            def decoded(value):
                return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else (value or "")
            captured = decoded(exc.stdout) + decoded(exc.stderr)
            log_path.write_text(self.safe_text(captured) + "\nCommand timeout.\n", encoding="utf-8")
            raise RuntimeError(f"命令超过 {timeout} 秒；脱敏日志：{log_path.name}") from None
        log_path.write_text(output, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"命令返回 {result.returncode}；脱敏日志：{log_path.name}；末段：{output[-800:]}")
        details = {"command": command, "returncode": result.returncode, "log": str(log_path),
                   "output_tail": output[-1200:]}
        if name == "pytest":
            passed = re.search(r"(\d+) passed", output)
            skipped = re.search(r"(\d+) skipped", output)
            details.update(passed=int(passed.group(1)) if passed else 0,
                           skipped=int(skipped.group(1)) if skipped else 0)
            if details["skipped"]:
                raise RuntimeError(f"pytest 存在 {details['skipped']} 项跳过，需检查真实集成覆盖；日志：{log_path.name}")
        return details

    def get(self, path, *, ui=False):
        base = self.args.ui_url if ui else self.args.api_url
        with httpx.Client(timeout=30, trust_env=False) as client:
            return client.get(base.rstrip("/") + path)

    def post(self, payload):
        with httpx.Client(timeout=self.args.live_timeout if self.args.live else 30, trust_env=False) as client:
            return client.post(self.args.api_url.rstrip("/") + "/api/chat", json=payload)

    def api_health(self):
        response = self.get("/health")
        assert response.status_code == 200, f"HTTP {response.status_code}"
        body = response.json()
        assert body.get("status") == "ok" and body.get("stage") == "D1", "API 状态或阶段异常"
        assert body.get("database_ready") is True, "真实数据库未就绪"
        assert body.get("catalog_exists") is True, "目录不存在"
        return {"http_status": response.status_code, "body": body}

    def ui_health(self):
        response = self.get("/_stcore/health", ui=True)
        assert response.status_code == 200 and response.text.strip().lower() == "ok", "Streamlit 健康检查失败"
        return {"http_status": response.status_code, "body": response.text.strip()}

    def document_list(self):
        response = self.get("/api/documents")
        assert response.status_code == 200, f"HTTP {response.status_code}"
        body = response.json()
        self.documents = body.get("documents", [])
        assert body.get("status") == "READY", "文档清单未就绪"
        assert len(self.documents) == 6, f"应为 6 文档，实际 {len(self.documents)}"
        assert len({doc["doc_id"] for doc in self.documents}) == 6, "文档 ID 重复"
        assert len({doc["domain"] for doc in self.documents}) == 6, "领域不是六类"
        assert all(doc.get("ready") is True and doc.get("page_count", 0) > 0 for doc in self.documents), "部分文档未就绪"
        return {"http_status": response.status_code, "body": body}

    def source_pdf(self, document):
        response = self.get(f"/api/documents/{document['doc_id']}/file")
        assert response.status_code == 200, f"PDF HTTP {response.status_code}"
        assert response.headers.get("content-type", "").startswith("application/pdf"), "PDF Content-Type 异常"
        assert response.content.startswith(b"%PDF-"), "PDF 文件 magic 不符"
        digest = sha256(response.content).hexdigest()
        assert digest == document["content_hash"], "HTTP 返回的源 PDF 与清单 SHA256 不一致"
        return {"doc_id": document["doc_id"], "http_status": response.status_code,
                "byte_count": len(response.content), "sha256": digest, "magic": "%PDF-"}

    def physical_page(self, document, page):
        response = self.get(f"/api/documents/{document['doc_id']}/pages/{page}")
        assert response.status_code == 200, f"页预览 HTTP {response.status_code}"
        assert response.headers.get("content-type", "").startswith("image/png"), "PNG Content-Type 异常"
        assert response.content.startswith(b"\x89PNG\r\n\x1a\n"), "PNG magic 不符"
        with Image.open(io.BytesIO(response.content)) as picture:
            picture.load()
            size = list(picture.size)
            assert picture.format == "PNG" and all(dimension > 0 for dimension in size), "PNG 图像不可解码"
        return {"doc_id": document["doc_id"], "physical_page": page, "http_status": response.status_code,
                "image_size": size, "byte_count": len(response.content), "sha256": sha256(response.content).hexdigest()}

    def invalid_page(self, document, page):
        response = self.get(f"/api/documents/{document['doc_id']}/pages/{page}")
        assert response.status_code == 404, f"越界物理页应拒绝，实际 HTTP {response.status_code}"
        return {"doc_id": document["doc_id"], "requested_page": page, "http_status": response.status_code,
                "body": response.json()}

    def invalid_message(self, message):
        response = self.post({"session_id": f"accept-invalid-{self.stamp}", "message": message,
                              "scope": {"route": "sql", "db_id": "chinook", "doc_ids": []}})
        assert response.status_code == 422, f"非法消息应拒绝，实际 HTTP {response.status_code}"
        errors = response.json().get("detail", [])
        return {"message_type": type(message).__name__, "message_length": len(message) if isinstance(message, str) else None,
                "http_status": response.status_code,
                "validation_errors": [{key: error.get(key) for key in ("type", "loc", "msg")} for error in errors]}

    def unknown_file(self):
        response = self.get("/api/documents/not-registered/file")
        assert response.status_code == 404, f"未登记文档应为 404，实际 {response.status_code}"
        return {"http_status": response.status_code, "body": response.json()}

    @staticmethod
    def llm_usage(body):
        steps = [step for step in body.get("steps", []) if "llm" in step.get("name", "").lower()]
        def tokens(value):
            if isinstance(value, dict):
                return sum(item for key, item in value.items()
                           if key in {"prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens"}
                           and isinstance(item, (int, float))) + sum(tokens(item) for item in value.values())
            if isinstance(value, list):
                return sum(tokens(item) for item in value)
            return 0
        return {"llm_step_count": len(steps), "recorded_token_counter_sum": tokens(body)}

    def unsupported_scope(self, scope):
        payload = {"session_id": f"accept-scope-{self.stamp}", "message": "检查今天允许的来源范围。", "scope": scope}
        response = self.post(payload)
        assert response.status_code == 200, f"HTTP {response.status_code}"
        body = response.json()
        usage = self.llm_usage(body)
        assert body.get("status") == "UNSUPPORTED", f"实际状态 {body.get('status')}"
        assert usage["llm_step_count"] == 0 and usage["recorded_token_counter_sum"] == 0, "拒绝来源却出现模型步骤/用量"
        return {"request": payload, "http_status": response.status_code, "response": body, "usage_check": usage}

    def dense_index(self):
        chunks, metadata = load_index(settings=self.settings, verify_sources=True)
        assert metadata.get("index_version") == INDEX_VERSION == 2, "必须使用 v2 索引"
        assert len(metadata.get("documents", [])) == 6, "索引文档数量异常"
        assert metadata.get("retrieval_method") == "bm25+bge-m3_dense_rrf", "没有启用真实混合检索"
        dense = metadata.get("dense_embedding", {})
        assert dense.get("enabled") is True and dense.get("dimension") == 1024, "dense 元数据未就绪"
        path = self.settings.rag_index_path / "embeddings.npy"
        actual_hash = sha256(path.read_bytes()).hexdigest()
        assert actual_hash == dense.get("vectors_sha256"), "向量文件 SHA256 不符"
        vectors = np.load(path, allow_pickle=False, mmap_mode="r")
        assert vectors.shape == (len(chunks), 1024), f"实际向量形状 {vectors.shape}"
        assert np.isfinite(vectors).all(), "向量含非有限值"
        norms = np.linalg.norm(vectors, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5), "向量没有归一化"
        page_counts = {document["doc_id"]: document["page_count"] for document in metadata["documents"]}
        assert all(chunk["doc_id"] in page_counts and 1 <= chunk["page"] <= page_counts[chunk["doc_id"]] for chunk in chunks), "chunk 文档或物理页越界"
        assert all(chunk["text"] and len(chunk["text"]) <= 600 for chunk in chunks), "chunk 内容为空或超限"
        return {"index_version": metadata["index_version"], "retrieval_method": metadata["retrieval_method"],
                "chunk_count": len(chunks), "shape": list(vectors.shape), "all_finite": True,
                "norm_min": float(norms.min()), "norm_max": float(norms.max()), "vectors_sha256": actual_hash,
                "all_source_hashes_verified": True, "manifest_hash_verified": True,
                "document_page_counts": page_counts, "chunking": metadata.get("chunking"),
                "parsing": metadata.get("parsing")}

    def embedding_smoke(self):
        embedder = get_embedder(self.settings)
        assert embedder is not None, "真实 BGE-M3 未安装"
        texts = ["客户发票和账单金额。", "Customer invoices and billing amounts.",
                 "A spacecraft explores the surface of Mars."]
        vectors = embedder.encode(texts)
        assert vectors.shape == (3, 1024) and np.isfinite(vectors).all(), "三句编码的维度或数值异常"
        norms = np.linalg.norm(vectors, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5), "三句编码未归一化"
        related = float(vectors[0] @ vectors[1])
        unrelated = float(vectors[0] @ vectors[2])
        assert related > unrelated, f"中英同义相似度未高于无关句：{related} / {unrelated}"
        metadata = embedder.metadata()
        assert metadata.get("providers") == ["CPUExecutionProvider"] and metadata.get("mode") == "bge-m3_onnx_int8", "实际运行方式与配置不符"
        return {"texts": texts, "shape": list(vectors.shape), "norms": norms.tolist(),
                "related_cosine": related, "unrelated_cosine": unrelated,
                "model_id": metadata.get("model_id"), "model_revision": metadata.get("model_revision"),
                "model_sha256": metadata.get("model_sha256"), "mode": metadata.get("mode"), "providers": metadata.get("providers")}

    def sql_rejections(self):
        catalog = load_catalog(self.settings.catalog_path)
        cases = ["UPDATE customer SET country='test' WHERE false;", "DELETE FROM customer WHERE false;",
                 "SELECT customer_id FROM customer; SELECT country FROM customer;",
                 "SELECT not_a_real_column FROM customer;"]
        results = []
        for query in cases:
            try:
                validate_sql(query, catalog, max_rows=self.settings.max_rows)
            except SQLValidationError as exc:
                results.append({"sql": query, "rejected": True, "reason": sanitize_error(exc, self.settings)})
            else:
                raise AssertionError("SQL 校验器放行应拒绝的查询：" + query)
        return {"catalog_table_count": len(catalog.tables), "cases": results, "database_writes_executed": 0}

    def sql_values(self):
        query_empty = "SELECT invoice_id FROM public.invoice WHERE false"
        query_aggregate = "SELECT COUNT(*) AS n,SUM(total) AS amount FROM public.invoice WHERE false"
        empty = execute_sql(query_empty, self.settings.db_url)
        aggregate = execute_sql(query_aggregate, self.settings.db_url)
        assert empty.rows == [] and empty.row_count == 0, "空表语义异常"
        assert aggregate.rows == [[0, None]] and aggregate.row_count == 1, "0 和 NULL 聚合语义异常"
        return {"empty": {"sql": query_empty, "columns": empty.columns, "rows": empty.rows},
                "aggregate": {"sql": query_aggregate, "columns": aggregate.columns, "rows": aggregate.rows}}

    def sql_read_only(self):
        query = "SELECT current_setting('transaction_read_only') AS setting"
        result = execute_sql(query, self.settings.db_url)
        assert result.rows == [["on"]], "executor 事务没有启用只读"
        return {"sql": query, "columns": result.columns, "rows": result.rows}

    def sql_timeout(self):
        query = "SELECT pg_sleep(0.2)"
        try:
            execute_sql(query, self.settings.db_url, statement_timeout_ms=10)
        except SQLTimeoutError as exc:
            assert exc.sqlstate == "57014", f"超时 SQLSTATE {exc.sqlstate}"
            return {"sql": query, "timeout_ms": 10, "cancelled": True, "sqlstate": exc.sqlstate,
                    "scope": "直接 executor 安全只读诊断；该 pg_sleep 不会通过业务 SQL 校验器"}
        raise AssertionError("10 ms statement_timeout 没有取消 200 ms pg_sleep")

    def live_case(self, name, message, scope, expected):
        request = {"session_id": f"accept-live-{self.stamp}-{name}", "message": message, "scope": scope}
        self.live_prediction_count += 1
        response = self.post(request)
        body = response.json()
        self.live_llm_steps += self.llm_usage(body)["llm_step_count"]
        result = {"request": request, "http_status": response.status_code, "response": body,
                  "usage": self.llm_usage(body), "expected": expected}
        # Store observed results even if the expected behavior fails.
        correct = response.status_code == 200 and body.get("status") == expected["status"]
        if "rows" in expected:
            table = body.get("table")
            actual_rows = [list(row.values()) for row in table] if isinstance(table, list) else None
            correct = correct and actual_rows == expected["rows"]
            result["actual_rows"] = actual_rows
        if expected.get("no_evidences"):
            correct = correct and not body.get("evidences")
        result["expected_behavior_matched"] = correct
        return result, correct

    def run(self):
        self.check("pytest_full", lambda: self.command("pytest", [sys.executable, "-m", "pytest", "-q", "--tb=short"]))
        self.check("pip_check", lambda: self.command("pip-check", [sys.executable, "-m", "pip", "check"], timeout=120))
        self.check("credentials_current", lambda: self.command("secrets-current", [sys.executable, "scripts/check_secrets.py"], timeout=120))
        self.check("credentials_git_history", lambda: self.command("secrets-history", [sys.executable, "scripts/check_secrets.py", "--history"], timeout=180))
        self.check("api_health", self.api_health)
        self.check("streamlit_health", self.ui_health)
        self.check("document_manifest_ready", self.document_list)
        for document in self.documents:
            doc_id = document["doc_id"]
            self.check("source_pdf_" + doc_id, lambda doc=document: self.source_pdf(doc))
            for label, page in (("first", 1), ("last", document.get("page_count", 0))):
                self.check(f"page_{label}_{doc_id}", lambda doc=document, number=page: self.physical_page(doc, number))
            for label, page in (("zero", 0), ("overflow", document.get("page_count", 0) + 1)):
                self.check(f"page_reject_{label}_{doc_id}", lambda doc=document, number=page: self.invalid_page(doc, number))
        self.check("unknown_document_file", self.unknown_file)
        for name, message in (("empty", ""), ("whitespace", "   "), ("too_long", "问" * 4001), ("null", None)):
            self.check("message_reject_" + name, lambda value=message: self.invalid_message(value))
        doc_ids = [document["doc_id"] for document in self.documents]
        if len(doc_ids) < 2:
            doc_ids = ["not-registered-one", "not-registered-two"]
        scopes = {
            "auto": {"route": "auto", "db_id": "chinook", "doc_ids": []},
            "hybrid": {"route": "hybrid", "db_id": "chinook", "doc_ids": [doc_ids[0]]},
            "adventureworks": {"route": "sql", "db_id": "adventureworks", "doc_ids": []},
            "sql_with_document": {"route": "sql", "db_id": "chinook", "doc_ids": [doc_ids[0]]},
            "multiple_documents": {"route": "doc", "db_id": None, "doc_ids": doc_ids[:2]},
        }
        for name, scope in scopes.items():
            self.check("unsupported_" + name, lambda value=scope: self.unsupported_scope(value))
        self.check("dense_index_v2_all_sources", self.dense_index)
        self.check("bge_m3_three_sentence_smoke", self.embedding_smoke)
        self.check("sql_validator_rejections", self.sql_rejections)
        self.check("sql_empty_zero_null", self.sql_values)
        self.check("sql_executor_read_only", self.sql_read_only)
        self.check("sql_executor_timeout", self.sql_timeout)
        if self.args.live:
            sql_scope = {"route": "sql", "db_id": "chinook", "doc_ids": []}
            live = [
                ("invoice_pre1990_empty", "列出 1990 年之前的发票编号，按发票编号升序。", sql_scope, {"status": "EMPTY_RESULT", "rows": []}),
                ("invoice_pre1990_count_zero", "1990 年之前一共有多少张发票？", sql_scope, {"status": "SUCCEEDED", "rows": [[0]]}),
                ("invoice_pre1990_sum_null", "1990 年之前发票总金额是多少？没有匹配时按 SQL SUM 的语义保留 NULL。", sql_scope, {"status": "SUCCEEDED", "rows": [[None]]}),
                ("manual_unanswerable_2035", "该文档所列 2035 年营业利润金额是多少美元？",
                 {"route": "doc", "db_id": None, "doc_ids": ["ohr-manual-macbook-air"]}, {"status": "EMPTY_RESULT", "no_evidences": True}),
            ]
            for name, message, scope, expected in live:
                start = perf_counter()
                try:
                    details, passed = self.live_case(name, message, scope, expected)
                    record = {"id": "live_" + name, "status": "PASS" if passed else "FAIL", "details": self.safe(details),
                              "latency_ms": round((perf_counter() - start) * 1000)}
                    self.checks.append(record)
                    print(f"[{record['status']}] live_{name}", flush=True)
                except Exception as exc:
                    self.checks.append({"id": "live_" + name, "status": "FAIL", "latency_ms": round((perf_counter() - start) * 1000),
                                        "details": {"error": sanitize_error(exc, self.settings), "expected": expected}})
                    print(f"[FAIL] live_{name}", flush=True)
        failed = [check["id"] for check in self.checks if check["status"] == "FAIL"]
        report = {
            "title": "D1 工程逐项验收", "reviewer_type": "automated_engineering", "human_signature": None,
            "started_at_utc": self.started.isoformat(), "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit_at_start": self.git_commit, "git_commit_at_finish": self.git("rev-parse", "HEAD"),
            "working_tree_dirty_at_start": self.initial_dirty,
            "api_url": self.args.api_url, "ui_url": self.args.ui_url,
            "scope": "工程、组件、文件完整性和接口边界；不替代业务标准答案人工接受，不改变原 gold/原评测报告。",
            "live_enabled": self.args.live, "model_prediction_count": self.live_prediction_count,
            "observed_live_llm_steps": self.live_llm_steps, "holdout_prediction_count": 0,
            "status": "PASS" if not failed else "FAIL", "check_count": len(self.checks),
            "passed_count": len(self.checks) - len(failed), "failed_count": len(failed), "failed_checks": failed,
            "checks": self.checks,
        }
        self.report_path.write_text(json.dumps(self.safe(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Engineering acceptance {report['status']}: {report['passed_count']}/{report['check_count']}; report={self.report_path}", flush=True)
        return 0 if not failed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--ui-url", default="http://127.0.0.1:8501")
    parser.add_argument("--output", type=Path, default=ROOT / "eval/reports/d1-acceptance/engineering.json")
    parser.add_argument("--live", action="store_true", help="明确发送额外 3 道 SQL 和 1 道无法回答的文档问题；默认关闭")
    parser.add_argument("--live-timeout", type=int, default=180)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("输出报告已存在；使用 --output 新路径保留旧验收证据。")
    try:
        return Acceptance(args).run()
    except Exception as exc:
        print("Engineering acceptance failed: " + sanitize_error(exc, get_settings()), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
