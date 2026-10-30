"""Bounded, same-origin local file/text ingestion; no chat/model invocation."""
import ipaddress
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.concurrency import run_in_threadpool

from qa_agent.rag.uploads import (ImportError, MAX_JSON_BYTES, MAX_TEXT_CHARS,
                                  get_job, prepare_file, submit_import)


def local_only(request: Request):
    def loopback(value):
        try:
            return ipaddress.ip_address(value).is_loopback
        except ValueError:
            return value == "localhost"
    if not loopback(request.url.hostname or "") or not loopback(request.client.host if request.client else ""):
        raise HTTPException(403, "资料导入仅允许通过本机工作台访问。")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "资料导入仅接受工作台同源请求。")
    if origin := request.headers.get("origin"):
        parsed = urlsplit(origin)
        if (parsed.scheme, parsed.netloc.lower()) != (request.url.scheme, request.url.netloc.lower()):
            raise HTTPException(403, "资料导入仅接受工作台同源请求。")


router = APIRouter(prefix="/api/documents", tags=["document-import"], dependencies=[Depends(local_only)])


class FileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    filename: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1, max_length=MAX_JSON_BYTES)


class TextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)


async def parse_request(request, model):
    if not request.headers.get("content-type", "").startswith("application/json"):
        raise HTTPException(415, "请使用 JSON 提交资料。")
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_JSON_BYTES:
            raise HTTPException(413, "资料超过上传大小限制。")
    try:
        return model.model_validate_json(body)
    except (ValidationError, ValueError):
        raise HTTPException(422, "资料字段无效，请检查标题、正文或文件大小。") from None


@router.post("/import", status_code=202)
async def file_import(request: Request):
    payload = await parse_request(request, FileRequest)
    try:
        raw, fmt = await run_in_threadpool(prepare_file, payload.filename, payload.content_base64)
        return submit_import(payload.title, raw, fmt)
    except ImportError as exc:
        raise HTTPException(exc.status_code, str(exc)) from None


@router.post("/text", status_code=202)
async def text_import(request: Request):
    payload = await parse_request(request, TextRequest)
    if not payload.text.strip() or "\x00" in payload.text:
        raise HTTPException(422, "请填写有效的资料正文。")
    try:
        return submit_import(payload.title, payload.text.encode("utf-8"), "md")
    except ImportError as exc:
        raise HTTPException(exc.status_code, str(exc)) from None


@router.get("/imports/{job_id}")
def import_status(job_id: str):
    try:
        return get_job(job_id)
    except ImportError as exc:
        raise HTTPException(exc.status_code, str(exc)) from None
