"""Same-origin localhost endpoints for local, read-only database connections."""
from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from qa_agent.database_registry import (
    DatabaseRegistryError, RegistrationRequest, list_databases,
    refresh_database, register_database, remove_database,
)


def _local_same_origin(request: Request) -> None:
    host = request.url.hostname or ""
    try:
        local_host = ipaddress.ip_address(host).is_loopback
    except ValueError:
        local_host = host.lower() == "localhost"
    client = request.client.host if request.client else ""
    try:
        local_client = ipaddress.ip_address(client).is_loopback
    except ValueError:
        local_client = False
    if not local_host or not local_client:
        raise HTTPException(403, "数据库连接管理仅允许通过本机工作台访问。")
    origin = request.headers.get("origin")
    if origin:
        parsed = urlsplit(origin)
        if (parsed.scheme, parsed.netloc.lower()) != (request.url.scheme, request.url.netloc.lower()):
            raise HTTPException(403, "数据库连接管理仅接受工作台同源请求。")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "数据库连接管理仅接受工作台同源请求。")


router = APIRouter(prefix="/api/databases", tags=["databases"], dependencies=[Depends(_local_same_origin)])


def _safe_error(exc: DatabaseRegistryError) -> HTTPException:
    return HTTPException(exc.status_code, detail={"code": exc.code, "message": str(exc)})


@router.get("")
def database_list() -> dict:
    try:
        return {"databases": list_databases()}
    except DatabaseRegistryError as exc:
        raise _safe_error(exc) from None


@router.post("", status_code=201)
async def database_add(request: Request) -> dict:
    # Parse explicitly so validation errors cannot echo request.input, including
    # a password or a DSN accidentally pasted into another field.
    if not request.headers.get("content-type", "").lower().startswith("application/json"):
        raise HTTPException(415, "请使用 JSON 提交数据库连接信息。")
    body = await request.body()
    if len(body) > 16384:
        raise HTTPException(413, "连接信息超过长度限制。")
    try:
        payload = RegistrationRequest.model_validate_json(body)
    except (ValidationError, ValueError):
        raise HTTPException(422, "连接信息格式无效；请检查名称、主机、端口、库名、账户和业务 Schema。") from None
    try:
        return await run_in_threadpool(register_database, payload)
    except DatabaseRegistryError as exc:
        raise _safe_error(exc) from None


@router.post("/{db_id}/refresh")
def database_refresh(db_id: str) -> dict:
    try:
        return refresh_database(db_id)
    except DatabaseRegistryError as exc:
        raise _safe_error(exc) from None


@router.delete("/{db_id}")
def database_remove(db_id: str) -> dict:
    try:
        remove_database(db_id)
        return {"db_id": db_id, "removed": True}
    except DatabaseRegistryError as exc:
        raise _safe_error(exc) from None
