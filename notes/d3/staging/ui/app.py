"""Shared demonstration UI with actual request traces and source locations."""
from __future__ import annotations

import os
from pathlib import Path
import re
import sys
from urllib.parse import quote, urlsplit
from uuid import uuid4

import httpx
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qa_agent.schemas import AnswerEnvelope, ChatRequest, SourceScope


def api_base_url() -> str:
    value = os.getenv("QA_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("QA_API_BASE_URL must be an HTTP URL without credentials")
    return value


def safe_text(value: str) -> str:
    """Keep diagnostic text useful without showing common credential formats."""
    value = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[已隐藏凭据]", str(value))
    value = re.sub(r"(?i)Bearer\s+\S+", "Bearer [已隐藏凭据]", value)
    value = re.sub(r"(?i)postgres(?:ql)?://[^\s]+", "[已隐藏数据库连接]", value)
    return value


def safe_diagnostics(value):
    """Show bounded tool summaries; never display full prompts or credentials."""
    hidden = {"api_key", "llm_api_key", "password", "secret", "authorization", "db_url",
              "dsn", "system_prompt", "user_prompt", "prompt", "full_prompt", "catalog"}
    if isinstance(value, dict):
        return {key: "[已隐藏]" if key.lower() in hidden else safe_diagnostics(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [safe_diagnostics(item) for item in value[:20]]
    return safe_text(value)[:2000] if isinstance(value, str) else value


@st.cache_data(ttl=300, show_spinner=False)
def source_bytes(base_url: str, doc_id: str, content_hash: str) -> bytes:
    response = httpx.get(document_url(base_url, doc_id), timeout=30)
    response.raise_for_status()
    if len(response.content) > 50 * 1024 * 1024:
        raise ValueError("The original document exceeds the preview limit")
    return response.content


@st.cache_data(ttl=15, show_spinner=False)
def service_health(base_url: str) -> dict:
    response = httpx.get(f"{base_url}/health", timeout=5)
    response.raise_for_status()
    result = response.json()
    return result if isinstance(result, dict) else {}


@st.cache_data(ttl=30, show_spinner=False)
def document_list(base_url: str) -> list[dict]:
    response = httpx.get(f"{base_url}/api/documents", timeout=15)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("documents", []), list):
        raise ValueError("Invalid document list")
    documents = payload.get("documents", [])
    return [item for item in documents if isinstance(item, dict) and item.get("doc_id")]


def document_url(base_url: str, doc_id: str, page: int | None = None) -> str:
    url = f"{base_url}/api/documents/{quote(doc_id, safe='')}/file"
    return f"{url}#page={page}" if page is not None and page >= 1 else url


@st.cache_data(ttl=300, show_spinner=False)
def pdf_bytes(base_url: str, doc_id: str, content_hash: str) -> bytes:
    # The content hash forms part of the cache key when a source document changes.
    response = httpx.get(document_url(base_url, doc_id), timeout=30)
    response.raise_for_status()
    value = response.content
    if not value.startswith(b"%PDF-") or len(value) > 50 * 1024 * 1024:
        raise ValueError("The source is not a supported PDF")
    return value


@st.cache_data(ttl=300, show_spinner=False)
def page_image(base_url: str, doc_id: str, page: int, content_hash: str) -> bytes:
    response = httpx.get(f"{base_url}/api/documents/{quote(doc_id, safe='')}/pages/{page}", timeout=30)
    response.raise_for_status()
    if not response.content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("The page preview is unavailable")
    return response.content


def linked_answer(answer: str, result: AnswerEnvelope, base_url: str) -> str:
    references = {e.evidence_id: e for e in result.evidences}

    def replace(match: re.Match) -> str:
        evidence = references.get(match.group(1))
        if not evidence:
            return match.group(0)
        target = document_url(base_url, evidence.doc_id, evidence.page)
        return f"[{match.group(0)}]({target})"

    return re.sub(r"\[(E\d+)\]", replace, safe_text(answer))


def render_evidence(result: AnswerEnvelope, base_url: str, documents: list[dict]) -> None:
    if not result.evidences:
        return
    st.subheader("引用依据")
    selected_key = f"selected_evidence_{result.trace_id}"
    valid_ids = {e.evidence_id for e in result.evidences}
    if st.session_state.get(selected_key) not in valid_ids:
        st.session_state[selected_key] = result.evidences[0].evidence_id
    for evidence in result.evidences:
        page_label = (f"第 {evidence.page} 页" if evidence.page is not None
                      else "章节：" + " / ".join(evidence.section_path) if evidence.section_path else "原文段落")
        if st.button(
            f"[{evidence.evidence_id}] {evidence.doc_title} · {page_label}",
            key=f"reference_{result.trace_id}_{evidence.evidence_id}",
            width="stretch",
        ):
            st.session_state[selected_key] = evidence.evidence_id
    selected = next(e for e in result.evidences if e.evidence_id == st.session_state[selected_key])
    metadata = next((d for d in documents if d["doc_id"] == selected.doc_id), {})
    document_format = str(metadata.get("format", "pdf")).lower()
    left, right = st.columns([1, 1])
    with left:
        st.markdown(f"**[{selected.evidence_id}] 原文**")
        if selected.section_path:
            st.caption(" / ".join(selected.section_path))
        st.text(safe_text(selected.text))
        st.link_button("打开原 PDF 对应页" if document_format == "pdf" else "打开原始文件",
                       document_url(base_url, selected.doc_id, selected.page))
    with right:
        if document_format != "pdf":
            try:
                value = source_bytes(base_url, selected.doc_id, metadata.get("content_hash", ""))
            except (httpx.HTTPError, ValueError):
                st.info("原文引用已显示，原始文件暂不可用。")
            else:
                mime = {"docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "html": "text/html", "md": "text/markdown", "png": "image/png"}.get(document_format, "application/octet-stream")
                st.download_button("下载原始文件", value, file_name=f"{selected.doc_id}.{document_format}", mime=mime)
                if document_format in {"png", "jpg", "jpeg"}:
                    st.image(value, caption="原始图像；引用文字来自实际 OCR。", width="stretch")
            return
        try:
            value = pdf_bytes(base_url, selected.doc_id, metadata.get("content_hash", ""))
        except (httpx.HTTPError, ValueError):
            st.info("原文引用已显示。PDF 预览暂不可用，可尝试打开原 PDF。")
        else:
            st.download_button("下载原 PDF", value, file_name=f"{selected.doc_id}.pdf", mime="application/pdf")
        if selected.page is not None and selected.page >= 1:
            try:
                preview = page_image(base_url, selected.doc_id, selected.page, metadata.get("content_hash", ""))
            except (httpx.HTTPError, ValueError):
                st.caption("对应页预览暂不可用，可打开原 PDF 查看。")
            else:
                st.image(preview, caption=f"原 PDF 第 {selected.page} 页", width="stretch")


def render_panels(
    result: AnswerEnvelope | None,
    base_url: str,
    documents: list[dict],
    *,
    db_id: str | None = None,
) -> None:
    """Keep the plan's three evidence panels visible in either source scope."""
    with st.expander("SQL 与结果", expanded=bool(result and result.sql)):
        if db_id:
            st.caption(f"数据库：{safe_text(db_id)}")
        if result and result.sql:
            st.caption("执行的 SQL")
            st.code(result.sql, language="sql")
        elif result is None:
            st.caption("提交问题后在这里查看 SQL 和查询结果。" if db_id else "当前来源为文档，尚未提交问题。")
        else:
            st.caption("本次响应未提供 SQL。" if db_id else "本次文档查询未执行数据库 SQL。")
        if result and result.table:
            st.dataframe(result.table, width="stretch", hide_index=True)
        elif result and result.table == []:
            st.caption("结果表为空。")
        if result and result.metadata.get("truncated"):
            st.info("结果超过显示上限，仅展示本次返回的部分记录。")
    with st.expander("引用来源", expanded=bool(result and result.evidences)):
        if result and result.evidences:
            render_evidence(result, base_url, documents)
        elif result is None:
            st.caption("提交文档问题后在这里查看原文、页码和原 PDF。")
        else:
            st.caption("本次查询没有文档引用。")
    with st.expander("处理步骤与耗时"):
        if result is None:
            st.caption("提交问题后在这里查看实际处理步骤和耗时。")
            return
        st.caption(f"请求编号：{result.trace_id}")
        if "latency_ms" in result.metadata:
            st.caption(f"服务端总耗时：{result.metadata['latency_ms']} 毫秒")
        if not result.steps:
            st.caption("本次响应未提供处理步骤。")
        for index, step in enumerate(result.steps, start=1):
            labels = {"ok": "完成", "warn": "有告警", "error": "失败", "skipped": "未执行"}
            st.markdown(f"**{index}. {step.name}** · {labels[step.status]} · {step.latency_ms} 毫秒")
            show = st.toggle(f"展开第 {index} 步详情", key=f"step_{result.trace_id}_{index}")
            if show and (step.input_summary or step.output_summary):
                # Render summaries as text rather than allowing arbitrary HTML.
                import json
                st.code(json.dumps(safe_diagnostics({"输入": step.input_summary, "输出": step.output_summary}),
                                   ensure_ascii=False, indent=2), language="json")




def submit_resume(base_url: str, scope: SourceScope, *, message: str,
                  card: dict, choice_id: str | None = None) -> None:
    request = ChatRequest(session_id=st.session_state.qa_session_id, message=message, scope=scope,
                          clarification_id=card["clarification_id"], intent_version=card["intent_version"],
                          choice_id=choice_id)
    with st.spinner("正在更新条件并查询……"):
        try:
            response = httpx.post(f"{base_url}/api/chat", json=request.model_dump(), timeout=240)
            response.raise_for_status()
            result = AnswerEnvelope.model_validate(response.json())
        except (httpx.HTTPError, ValueError):
            st.error("未能获取有效的补充结果，请稍后重试。")
            return
        st.session_state.last_answer = result.model_dump()
    st.rerun()


def render_clarification_controls(result: AnswerEnvelope, base_url: str, scope: SourceScope) -> None:
    card = result.clarification
    if card and card.get("resume_supported"):
        st.markdown("**请补充查询条件**")
        st.write(safe_text(card.get("question", "")))
        if card.get("reason"):
            st.caption(safe_text(card["reason"]))
        for item in card.get("options", []):
            if st.button(safe_text(item["label"]), key=f"clarify_{card['clarification_id']}_{item['id']}"):
                submit_resume(base_url, scope, message=item["label"], card=card, choice_id=item["id"])
        with st.form(f"clarify_free_{card['clarification_id']}"):
            value = st.text_input("补充说明", max_chars=4000)
            submitted = st.form_submit_button("提交补充")
        if submitted:
            if value.strip():
                submit_resume(base_url, scope, message=value.strip(), card=card)
            else:
                st.warning("请写出需要补充的具体信息。")
    elif card:
        for item in card.get("options", []):
            st.caption(safe_text(str(item)))
    metadata = result.metadata.get("clarify", {})
    switch = metadata.get("switch")
    if switch:
        st.caption("切换统计口径")
        for item in switch.get("options", []):
            if st.button("切换：" + safe_text(item["label"]), key=f"switch_{switch['clarification_id']}_{item['id']}"):
                submit_resume(base_url, scope, message=item["label"], card=switch, choice_id=item["id"])


def render_result(
    result: AnswerEnvelope,
    base_url: str,
    documents: list[dict],
    *,
    db_id: str | None = None,
) -> None:
    labels = {
        "SUCCEEDED": "回答完成", "EMPTY_RESULT": "查询完成，未找到符合条件的记录",
        "NEEDS_CLARIFICATION": "需要补充信息", "UNSUPPORTED": "当前来源不支持此问题", "FAILED": "本次请求未完成",
    }
    label = labels[result.status]
    if result.status == "SUCCEEDED":
        st.success(label)
    elif result.status in {"EMPTY_RESULT", "NEEDS_CLARIFICATION", "UNSUPPORTED"}:
        st.info(label)
    else:
        st.error(label)
    nlu = result.metadata.get("nlu", {})
    if result.rewritten_question:
        left, right = st.columns(2)
        with left:
            st.caption("原问题")
            st.text(safe_text(nlu.get("original_question", "")))
        with right:
            st.caption("改写后")
            st.text(safe_text(result.rewritten_question))
        patches = nlu.get("patches", [])
        if patches:
            st.caption("修改依据")
            for patch in patches:
                st.text(safe_text(f"{patch.get('original_text', patch.get('original', patch.get('before','')))} → "
                                  f"{patch.get('replacement', patch.get('after',''))}；"
                                  f"{patch.get('method','')} {patch.get('evidence_ref','')}"))
    scope = SourceScope(route="sql", db_id=db_id, doc_ids=[]) if db_id else SourceScope(route="doc", db_id=None)
    if db_id:
        render_clarification_controls(result, base_url, scope)
    st.markdown(linked_answer(result.answer, result, base_url))
    if result.error:
        st.caption(safe_text(result.error.message))
    render_panels(result, base_url, documents, db_id=db_id)


def main() -> None:
    st.set_page_config(page_title="精准问数问答", page_icon="🔎", layout="wide")
    st.title("精准问数问答")
    st.caption("选择数据来源，输入问题，查看答案和对应依据。")
    try:
        base_url = api_base_url()
    except ValueError:
        st.error("服务地址配置无效，请联系维护人员。")
        st.stop()
    try:
        health = service_health(base_url)
    except (httpx.HTTPError, ValueError):
        st.error("问答服务暂不可用，请启动后端服务后刷新页面。")
        st.stop()
    if health.get("status") != "ok":
        st.warning("问答服务正在准备，请稍后重试。")
    try:
        documents = document_list(base_url)
    except (httpx.HTTPError, ValueError):
        documents = []
    source = st.radio("数据来源", ["数据库", "指定文档"], horizontal=True, key="source_choice")
    ready_documents = [d for d in documents if d.get("ready")]
    blocked = False
    if source == "数据库":
        names = ["Chinook", "AdventureWorks"] if health.get("aw_database_ready") else ["Chinook"]
        selected = st.selectbox("数据库", names, disabled=len(names) == 1)
        db_id = "adventureworks" if selected == "AdventureWorks" else "chinook"
        scope = SourceScope(route="sql", db_id=db_id, doc_ids=[])
        context = f"sql:{db_id}"
        placeholder = "例如：来自巴西的客户有多少位？"
        if health.get("aw_database_ready" if db_id == "adventureworks" else "database_ready") is False:
            st.warning("数据库暂不可用，请稍后重试。")
            blocked = True
    else:
        if not ready_documents:
            st.info("暂无可查询的已处理文档，请完成文档导入后刷新页面。")
            st.stop()
        by_id = {d["doc_id"]: d for d in ready_documents}
        doc_id = st.selectbox("查询文档", list(by_id), format_func=lambda value: by_id[value].get("title", value), key="document_choice")
        document = by_id[doc_id]
        info = [str(document.get("format", "PDF")).upper()]
        if document.get("page_count"):
            info.append(f"{document['page_count']} 页")
        if document.get("language"):
            info.append(document["language"])
        st.caption(" · ".join(info))
        scope = SourceScope(route="doc", db_id=None, doc_ids=[doc_id])
        context = f"doc:{doc_id}"
        placeholder = "输入与当前文档有关的问题，例如：文档列出了哪些风险？"
    if not health.get("llm_configured", True):
        st.warning("模型尚未配置，问答请求可能无法完成。")
    if "qa_session_id" not in st.session_state:
        st.session_state.qa_session_id = str(uuid4())
    with st.form("question_form", clear_on_submit=False):
        question = st.text_area("你的问题", placeholder=placeholder, max_chars=4000, key="question_input")
        submitted = st.form_submit_button("提交问题", type="primary", disabled=blocked)
    if submitted:
        if not question.strip():
            st.warning("请先输入问题。")
        else:
            request = ChatRequest(session_id=st.session_state.qa_session_id, message=question, scope=scope)
            with st.spinner("正在查询，请稍候……"):
                try:
                    response = httpx.post(f"{base_url}/api/chat", json=request.model_dump(), timeout=240)
                    response.raise_for_status()
                    result = AnswerEnvelope.model_validate(response.json())
                except httpx.TimeoutException:
                    st.error("服务响应超时，请稍后重试。")
                    st.session_state.pop("last_answer", None)
                except (httpx.HTTPError, ValueError):
                    st.error("未能获取有效的问答结果，请稍后重试或联系维护人员。")
                    st.session_state.pop("last_answer", None)
                else:
                    st.session_state.last_answer = result.model_dump()
                    st.session_state.last_answer_context = context
    if st.session_state.get("last_answer_context") == context and st.session_state.get("last_answer"):
        render_result(AnswerEnvelope.model_validate(st.session_state.last_answer), base_url, documents, db_id=scope.db_id)
    else:
        render_panels(None, base_url, documents, db_id=scope.db_id)


if __name__ == "__main__":
    main()
