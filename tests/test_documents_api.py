"""Only registered, hash-matched PDFs may be downloaded or rendered."""
import csv
from dataclasses import replace
from hashlib import sha256
import json

from fastapi.testclient import TestClient
import pytest
from pypdf import PdfWriter

from api.main import app
from qa_agent.config import get_settings
from qa_agent.documents import DocumentError, load_documents


@pytest.fixture
def registered_pdf(tmp_path, monkeypatch):
    folder = tmp_path / "data/docs"
    folder.mkdir(parents=True)
    path = folder / "source.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with path.open("wb") as stream:
        writer.write(stream)
    digest = sha256(path.read_bytes()).hexdigest()
    manifest = folder / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        csv_writer = csv.DictWriter(stream, fieldnames=["doc_id", "title", "format", "path", "content_hash"])
        csv_writer.writeheader()
        csv_writer.writerow({"doc_id": "doc-test", "title": "Registered test PDF", "format": "pdf",
                             "path": "data/docs/source.pdf", "content_hash": digest})
    settings = replace(get_settings(), rag_manifest_path=manifest, rag_index_path=folder / "index")
    monkeypatch.setattr("api.documents.get_settings", lambda: settings)
    def documents():
        return load_documents(manifest, project_root=tmp_path)
    monkeypatch.setattr("api.documents.load_documents", documents)
    monkeypatch.setattr("qa_agent.documents.load_documents", documents)
    return path, manifest, digest, settings


def test_unregistered_document_cannot_be_downloaded(registered_pdf):
    with TestClient(app) as client:
        assert client.get("/api/documents/not-registered/file").status_code == 404


def test_pdf_file_and_physical_page_are_real(registered_pdf):
    with TestClient(app) as client:
        response = client.get("/api/documents/doc-test/file")
        assert response.status_code == 200
        assert response.content.startswith(b"%PDF-")
        assert response.headers["content-disposition"].startswith("inline")
        page = client.get("/api/documents/doc-test/pages/1")
        assert page.status_code == 200
        assert page.content.startswith(b"\x89PNG\r\n\x1a\n")
        assert client.get("/api/documents/doc-test/pages/0").status_code == 404
        assert client.get("/api/documents/doc-test/pages/2").status_code == 404


def test_modified_pdf_is_not_served(registered_pdf):
    path, _, _, _ = registered_pdf
    path.write_bytes(path.read_bytes() + b"\nchanged")
    with TestClient(app) as client:
        assert client.get("/api/documents/doc-test/file").status_code == 409
        assert client.get("/api/documents/doc-test/pages/1").status_code == 409


def test_documents_ready_requires_matching_index(registered_pdf):
    _, _, digest, settings = registered_pdf
    with TestClient(app) as client:
        assert client.get("/api/documents").json()["documents"][0]["ready"] is False
        settings.rag_index_path.mkdir()
        (settings.rag_index_path / "index_meta.json").write_text(json.dumps({
            "documents": [{"doc_id": "doc-test", "content_hash": digest}]}), encoding="utf-8")
        doc = client.get("/api/documents").json()["documents"][0]
        assert doc["ready"] is True
        assert doc["page_count"] == 1
        assert "path" not in doc


def test_manifest_cannot_expose_outside_data_files(registered_pdf, tmp_path):
    _, manifest, _, _ = registered_pdf
    text = manifest.read_text(encoding="utf-8").replace("data/docs/source.pdf", "../outside.pdf")
    manifest.write_text(text, encoding="utf-8")
    with pytest.raises(DocumentError, match="data"):
        load_documents(manifest, project_root=tmp_path)
