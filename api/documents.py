"""Read-only access to registered files and honest physical-page previews."""
from __future__ import annotations

from functools import lru_cache
import io
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pypdf import PdfReader

from qa_agent.config import get_settings
from qa_agent.documents import DocumentError, get_document, load_documents, verify_document_hash

router = APIRouter(prefix="/api/documents", tags=["documents"])


@lru_cache(maxsize=32)
def _page_count(path: str, mtime_ns: int, size: int) -> int:
    return len(PdfReader(path).pages)


def _registered(doc_id: str) -> dict:
    try:
        return get_document(doc_id)
    except KeyError:
        raise HTTPException(404, "指定文档未在清单中登记。") from None
    except DocumentError as exc:
        raise HTTPException(409, str(exc)) from None


@router.get("")
def document_list() -> dict:
    settings = get_settings()
    if not settings.rag_manifest_path.is_file():
        return {"documents": [], "status": "NOT_READY"}
    try:
        documents = load_documents()
        index_path = settings.rag_index_path / "index_meta.json"
        metadata = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {}
        indexed = metadata.get("documents", {})
        if isinstance(indexed, list):
            indexed = {doc["doc_id"]: doc for doc in indexed}
        result = []
        for document in documents:
            verify_document_hash(document)
            path = document["resolved_path"]
            stat = path.stat()
            index_document = indexed.get(document["doc_id"], {})
            index_hash = index_document if isinstance(index_document, str) else index_document.get("content_hash")
            result.append({
                **{key: document.get(key, "") for key in
                   ("doc_id", "title", "format", "domain", "language", "source_url", "content_hash")},
                "page_count": _page_count(str(path), stat.st_mtime_ns, stat.st_size) if document["format"] == "pdf" else None,
                "location_type": "physical_page" if document["format"] == "pdf" else
                                 "image_coordinates" if document["format"] == "png" else "section",
                "ready": index_hash == document["content_hash"],
            })
        return {"documents": result, "status": "READY" if result and all(d["ready"] for d in result) else "NOT_READY"}
    except (DocumentError, ValueError, OSError):
        raise HTTPException(409, "文档清单或索引未就绪，请检查资料并运行导入脚本。") from None


@router.get("/{doc_id}/file")
def document_file(doc_id: str) -> FileResponse:
    document = _registered(doc_id)
    formats = {"pdf": ("application/pdf", ".pdf"), "png": ("image/png", ".png"),
               "html": ("text/html; charset=utf-8", ".html"), "md": ("text/markdown; charset=utf-8", ".md"),
               "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx")}
    mime, suffix = formats[document["format"]]
    # HTML is an untrusted source: download it rather than execute its scripts
    # inside the API origin. Only PDF/PNG have an inline preview.
    return FileResponse(document["resolved_path"], media_type=mime,
                        filename=f"{doc_id}{suffix}",
                        content_disposition_type="inline" if document["format"] in {"pdf", "png"} else "attachment")


@lru_cache(maxsize=16)
def _render_page(path: str, content_hash: str, page: int) -> bytes:
    import pypdfium2 as pdfium
    with pdfium.PdfDocument(path) as pdf:
        pdf_page = pdf[page - 1]
        try:
            bitmap = pdf_page.render(scale=1.25)
            try:
                output = io.BytesIO()
                bitmap.to_pil().save(output, format="PNG")
                return output.getvalue()
            finally:
                bitmap.close()
        finally:
            pdf_page.close()


@router.get("/{doc_id}/pages/{page}")
def document_page(doc_id: str, page: int) -> Response:
    document = _registered(doc_id)
    if document["format"] != "pdf":
        raise HTTPException(404, "此格式没有稳定 PDF 物理页码，请使用章节或图像位置。")
    path = document["resolved_path"]
    stat = path.stat()
    if page < 1 or page > _page_count(str(path), stat.st_mtime_ns, stat.st_size):
        raise HTTPException(404, "物理页码超出文档范围。")
    return Response(_render_page(str(path), document["content_hash"], page), media_type="image/png")
