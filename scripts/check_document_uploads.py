"""Real HTTP upload/retrieval smoke test on an isolated copy; no model API calls."""
from __future__ import annotations

import argparse
import base64
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".runtime/upload-check/latest.json")
    args = parser.parse_args()
    from qa_agent.config import get_settings
    original = get_settings()
    run_id = uuid4().hex
    corpus = ROOT / "data/.upload-checks" / run_id
    corpus.mkdir(parents=True)
    manifest = corpus / "manifest.csv"
    index = corpus / "index"
    shutil.copyfile(original.rag_manifest_path, manifest)
    shutil.copytree(original.rag_index_path, index)
    initial_manifest = original.rag_manifest_path.read_bytes()
    os.environ.update(RAG_MANIFEST_PATH=str(manifest), RAG_INDEX_PATH=str(index),
                      RAG_ANSWER_MODE="extractive", LLM_API_KEY="", CHINOOK_DB_URL="", DB_URL="", AW_DB_URL="")
    get_settings.cache_clear()
    from qa_agent.llm import JsonLLM
    calls = []
    def no_remote(*a, **k):
        calls.append(True)
        raise AssertionError("Smoke test must never call the model API")
    JsonLLM.complete_json = no_remote
    from api.main import app
    import uvicorn
    from http.server import ThreadingHTTPServer
    spec = importlib.util.spec_from_file_location("upload_check_proxy", ROOT / "frontend-workbench/run_ui.py")
    proxy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proxy)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    api_port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=api_port, log_level="warning"))
    api_thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    api_thread.start()
    deadline = time.monotonic() + 30
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("Local API startup timed out")
        time.sleep(.05)
    ui = ThreadingHTTPServer(("127.0.0.1", 0), proxy.make_handler(f"http://127.0.0.1:{api_port}"))
    ui_thread = threading.Thread(target=ui.serve_forever, daemon=True)
    ui_thread.start()
    base = f"http://127.0.0.1:{ui.server_port}"
    opener = build_opener(ProxyHandler({}))
    checks = []
    imported = []
    def request(path, payload=None, origin=None):
        req = Request(base + path, data=None if payload is None else json.dumps(payload, ensure_ascii=False).encode(),
                      headers={"Content-Type": "application/json", "Origin": origin or base})
        try:
            with opener.open(req, timeout=30) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.load(exc)
    def upload(route, payload, expected="ready"):
        began = time.perf_counter()
        status, job = request("/api/documents/" + route, payload)
        assert status == 202, (status, job)
        deadline = time.monotonic() + 180
        while job["status"] in {"queued", "indexing"}:
            assert time.monotonic() < deadline, job
            time.sleep(.1)
            status, job = request("/api/documents/imports/" + job["job_id"])
            assert status == 200, job
        assert job["status"] == expected, job
        return job, round(time.perf_counter() - began, 3)
    try:
        import fitz
        from docx import Document
        pdf = fitz.open()
        pdf.new_page().insert_text((72, 72), "Cedar budget is 202630 dollars.")
        pdf_bytes = pdf.tobytes()
        pdf.close()
        docx = Document()
        docx.add_paragraph("Cedar budget is 202630 dollars.")
        buffer = io.BytesIO()
        docx.save(buffer)
        samples = [("text", None, "粘贴文字：Cedar budget is 202630 dollars.".encode()),
                   ("txt", "sample.txt", b"TXT source: Cedar budget is 202630 dollars."),
                   ("md", "sample.md", b"# Markdown source\nCedar budget is 202630 dollars."),
                   ("pdf", "sample.pdf", pdf_bytes), ("docx", "sample.docx", buffer.getvalue())]
        from qa_agent.rag.retriever import retrieve
        for label, filename, raw in samples:
            payload = {"title": "Upload check " + label}
            payload.update({"filename": filename, "content_base64": base64.b64encode(raw).decode()}
                           if filename else {"text": raw.decode()})
            job, seconds = upload("import" if filename else "text", payload)
            doc_id = job["document"]["doc_id"]
            imported.append(doc_id)
            _, listing = request("/api/documents")
            assert any(d["doc_id"] == doc_id and d["ready"] for d in listing["documents"])
            hits, _ = retrieve("Cedar budget", doc_id, settings=get_settings())
            assert hits and "202630" in hits[0]["text"]
            status, answer = request("/api/chat", {"message": "What is the Cedar budget?",
                "scope": {"route": "doc", "doc_ids": [doc_id]}, "session_id": "upload-check-" + run_id + label})
            assert status == 200 and answer["status"] == "SUCCEEDED", answer
            assert "202630" in answer["answer"] and answer["evidences"], answer
            checks.append({"case": label, "status": "passed", "seconds": seconds,
                           "job": job, "retrieval_verified": True, "answer_mode": "extractive",
                           "chat_status": answer["status"], "evidence_count": len(answer["evidences"])})
            print(f"PASS {label}: {seconds}s", flush=True)
        text = "完整会话资料。" * 1000 + "The final budget is 875 dollars."
        session = "upload-context-" + run_id
        status, context = request("/api/context", {"session_id": session, "text": text})
        assert status == 201 and context["characters"] == len(text), context
        from qa_agent.context import ContextStore
        from qa_agent.schemas import ChatRequest
        resolved = ContextStore().resolve(ChatRequest(session_id=session, message="budget?", context_id=context["context_id"]))
        assert resolved.text == text
        checks.append({"case": "session_text", "status": "passed", "characters": len(text), "disk_roundtrip": True})
        duplicate, _ = upload("text", {"title": "Duplicate", "text": samples[0][2].decode()}, "failed")
        assert "已经登记" in duplicate["message"]
        checks.append({"case": "duplicate", "status": "passed"})
        status, _ = request("/api/documents/text", {"title": "blocked", "text": "sample"}, "https://foreign.example")
        assert status == 403
        checks.append({"case": "cross_origin_rejected", "status": "passed"})
        from qa_agent.rag.index import load_index
        chunks, metadata = load_index(settings=get_settings())
        assert set(imported).issubset({c["doc_id"] for c in chunks})
        assert initial_manifest == original.rag_manifest_path.read_bytes()
        assert not calls
        report = {"passed": True, "checks": checks, "model_api_calls": 0,
                  "original_manifest_unchanged": True, "corpus": str(corpus),
                  "index_integrity_verified": True, "incremental": metadata["incremental"],
                  "source_documents": len(metadata["documents"]), "chunk_count": len(chunks)}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"PASS {len(checks)} checks; remote calls: 0; report: {args.output}", flush=True)
    finally:
        ui.shutdown()
        ui.server_close()
        server.should_exit = True
        api_thread.join(20)


if __name__ == "__main__":
    main()
