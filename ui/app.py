"""Shared demonstration UI with actual request traces and source locations."""
from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
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
from qa_agent.sql.result_format import percentage_formats


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


def rewrite_explanation(patch: dict, nlu: dict) -> str:
    """Describe the actual selected match without exposing internal IDs."""
    original = patch.get("original_text", patch.get("original", patch.get("before", "")))
    replacement = patch.get("replacement", patch.get("after", ""))
    method = patch.get("method", "")
    labels = {"exact": "精确匹配", "alias": "已确认别名", "pinyin": "拼音匹配",
              "fuzzy": "拼写相似匹配", "vector": "语义相似匹配", "llm": "候选判断"}
    label = labels.get(method, "名称匹配")
    score = patch.get("score")
    for mention in nlu.get("mentions", []):
        if mention.get("original_text") != original or mention.get("canonical_value") != replacement:
            continue
        if "start" in patch and mention.get("span") != [patch["start"], patch.get("end")]:
            continue
        selected = next((c for c in mention.get("candidates", [])
                         if c.get("candidate_id") == mention.get("selected_candidate_id")), None)
        if selected:
            score = selected.get("stage_scores", {}).get(method, selected.get("score", score))
        break
    # A model choice is not itself a calibrated matching score. Do not attach
    # another retrieval method's similarity to that model-choice label.
    if method != "llm" and isinstance(score, (int, float)) and not isinstance(score, bool) and 0 <= score <= 1:
        label += f" {score:.2f}"
    return safe_text(f"{original} → {replacement}（{label}）")


def clarification_reason(reason: str) -> str:
    """Translate the legacy policy message into the user's query decision."""
    return safe_text(str(reason).replace(
        "候选关系获准不等于允许自动绑定；请明确本次筛选。",
        "这个名称可能指不同对象，请选择本次查询所指的对象。"))


def result_display_table(result: AnswerEnvelope) -> list[dict] | None:
    """Format a display copy; database values remain in result.table unchanged."""
    if not result.table:
        return result.table
    formats = result.metadata.get("result_format", {})
    if not isinstance(formats, dict):
        formats = {}
    inferred = {}
    # For old responses, use the SQL projection to determine fractional versus
    # already-scaled percentages. Without SQL or a supported projection, keep
    # the raw value rather than making up a scale from the column name.
    if result.intent and result.sql:
        names = {"ratio", "share", "percentage", "growth", "growth_rate", "yoy", "yoy_rate",
                 "同比", "增长率", "占比", "比例"}
        projected = percentage_formats(result.sql, list(result.table[0]), result.intent.task_type)
        inferred = {column: formatting for column, formatting in projected.items()
                    if str(column).casefold() in names and column not in formats}
    formats = {**inferred, **formats}
    displayed = []
    for row in result.table:
        output = dict(row)
        for column, formatting in formats.items():
            if (column not in output or not isinstance(formatting, dict)
                    or formatting.get("kind") != "percentage" or formatting.get("scale") not in (1, 100)):
                continue
            value = output[column]
            if value is None or isinstance(value, bool):
                continue
            try:
                numeric = Decimal(str(value))
                if numeric.is_finite():
                    output[column] = f"{numeric * Decimal(formatting['scale']):.2f}%"
            except (InvalidOperation, ValueError, TypeError):
                continue
        displayed.append(output)
    return displayed


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
            st.dataframe(result_display_table(result), width="stretch", hide_index=True)
        elif result and result.table == []:
            st.caption("结果表为空。")
        if result and result.metadata.get("truncated"):
            st.info("结果超过显示上限，仅展示本次返回的部分记录。")
        if result:
            bundle = result.metadata.get("schema_linker", {})
            if isinstance(bundle, dict) and bundle.get("selected_tables"):
                st.markdown("**所选表及理由**")
                reasons = bundle.get("reasons", {})
                rows = [{"表": name, "理由": "；".join(str(x) for x in reasons.get(name, []))}
                        for name in bundle["selected_tables"]]
                st.dataframe(rows, width="stretch", hide_index=True)
                components = bundle.get("disconnected_components", [])
                if len(components) > 1:
                    st.warning("所选对象分属不同关联分量，不能凭相似名称构造关联。")
                elif bundle.get("join_paths"):
                    st.caption(f"使用目录中的真实外键补齐关联，保留 {len(bundle['join_paths'])} 条关联路径。")
                omitted = bundle.get("excluded_tables", {})
                if omitted:
                    st.caption("未选表及理由")
                    st.dataframe([{"表": key, "理由": str(value)} for key, value in omitted.items()],
                                 width="stretch", hide_index=True)
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
            st.caption(clarification_reason(card["reason"]))
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
    region_labels={"customer.country":"客户所在地", "invoice.billing_country":"发票账单国家"}
    region=metadata.get("region_scope")
    if region in region_labels:
        st.caption(f"当前国家口径：{region_labels[region]}（{region}）")
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
    scope: SourceScope | None = None,
) -> None:
    labels = {
        "SUCCEEDED": "回答完成", "EMPTY_RESULT": "查询完成，未找到符合条件的记录",
        "NEEDS_CLARIFICATION": "需要补充信息", "UNSUPPORTED": "当前来源不支持此问题", "FAILED": "本次请求未完成",
    }
    fusion = result.metadata.get("fusion", {})
    if (result.status == "EMPTY_RESULT" and result.table and isinstance(fusion, dict)
            and fusion.get("document_status") in {"insufficient", "EMPTY_RESULT"}):
        labels["EMPTY_RESULT"] = "数据库查询完成，文档证据不足"
    label = labels[result.status]
    if result.status == "SUCCEEDED" and result.metadata.get("faithfulness_uncertain"):
        st.warning("回答已生成，含未核实内容。请根据引用原文核对数字和单位后使用。")
    elif result.status == "SUCCEEDED":
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
                st.text(rewrite_explanation(patch, nlu))
    if scope is None and isinstance(fusion, dict) and fusion.get("original_scope"):
        scope = SourceScope.model_validate(fusion["original_scope"])
    scope = scope or (SourceScope(route="sql", db_id=db_id, doc_ids=[]) if db_id else SourceScope(route="doc", db_id=None))
    if db_id:
        render_clarification_controls(result, base_url, scope)
    st.markdown(linked_answer(result.answer, result, base_url))
    if isinstance(fusion, dict) and fusion.get("plan_stages"):
        st.markdown("**跨源执行**")
        completed = fusion.get("completed_stages", 0)
        for number, label in enumerate(fusion["plan_stages"], 1):
            st.caption(f"{number}. {safe_text(label)} · {'完成' if number <= completed else '待完成'}")
        entity = fusion.get("transferred_entity")
        if entity:
            st.caption(f"数据库结果传给文档检索：{safe_text(entity['artist_name'])}（artist_id={entity['artist_id']}）")
        context = fusion.get("definition_context")
        if context and fusion.get("definition_used_in_generation"):
            st.caption("实际检索定义已用于SQL生成，并在执行前校验聚合表达式。")
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
    source = st.radio("数据来源", ["数据库", "指定文档", "数据库与文档"], horizontal=True, key="source_choice")
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
    elif source == "指定文档":
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
    else:
        allowed = {d["doc_id"]: d for d in ready_documents if str(d.get("entity_ref", "")).startswith("chinook:")}
        doc_ids = st.multiselect("允许检索的文档（留空使用全部对应文档）", list(allowed),
            format_func=lambda key: allowed[key].get("title", key), key="hybrid_documents")
        scope = SourceScope(route="hybrid", db_id="chinook", doc_ids=doc_ids)
        context = "hybrid:chinook:" + ",".join(sorted(doc_ids))
        placeholder = "例如：销售额最高的艺术家是谁？介绍一下他的音乐风格。或：按口径手册定义，计算2024年美国客户的客单价。"
        st.caption("一次请求依次使用数据库和对应文档，SQL、结果和文档引用都保留在下方。")
        if health.get("database_ready") is False:
            st.warning("数据库暂不可用，请稍后重试。")
            blocked = True
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
        render_result(AnswerEnvelope.model_validate(st.session_state.last_answer), base_url, documents,
                      db_id=scope.db_id, scope=scope)
    else:
        render_panels(None, base_url, documents, db_id=scope.db_id)


if __name__ == "__main__":
    main()
