"""Render verified tool blocks without a second generative rewrite.

No new arithmetic or cross-step inference is performed here. A requested
calculation belongs in an explicit guarded SQL node; this renderer preserves
the actual executed values, result formatting, source text and evidence IDs.
"""
from __future__ import annotations

from hashlib import sha256
import re


def render_executed_blocks(plan, outputs, evidences):
    expected = [item.step_id for item in plan.steps]
    if set(outputs) != set(expected):
        raise ValueError("执行结果与当前计划步骤不一致，不能省略未执行步骤。")
    available = {item.evidence_id: item for item in evidences}
    if len(available) != len(evidences):
        raise ValueError("实际文档证据编号重复，不能合并。")
    blocks, records = [], []
    titles = {"database": "数据库查询结果", "documents": "文档依据", "user_session_context": "本会话正文说明", "not_executed": "未完成步骤"}
    for step_id in expected:
        output = outputs[step_id]
        source = output.get("source")
        if source not in titles:
            raise ValueError("执行结果缺少受支持的实际来源。")
        answer = output.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("实际执行步骤没有可展示的回答。")
        inline = set(re.findall(r"\[(E\d+)\]", answer))
        if source == "documents":
            used = {item["evidence_id"]: item for item in output.get("evidences", [])}
            if not inline <= set(used) <= set(available):
                raise ValueError("文档回答引用不对应当前步骤实际返回的证据。")
            if output.get("status") == "SUCCEEDED" and not inline:
                raise ValueError("文档成功回答没有可核查引用。")
            for key in used:
                if (used[key].get("doc_id") != available[key].doc_id or
                        used[key].get("text") != available[key].text or used[key].get("page") != available[key].page):
                    raise ValueError("文档证据内容或位置在步骤间发生变化。")
        elif inline:
            raise ValueError("非文档步骤不能冒用文档引用编号。")
        if source == "database" and output.get("status") in {"SUCCEEDED", "EMPTY_RESULT"} and not isinstance(output.get("table"), list):
            raise ValueError("数据库步骤缺少实际结果表，不能用模型文字代替。")
        warning = "\n该步骤的证据覆盖仍不足，请查看证据面板。" if output.get("warnings") else ""
        blocks.append("**" + titles[source] + "**\n\n" + answer + warning)
        records.append({"step_id": step_id, "source": source, "status": output.get("status", "SUCCEEDED"),
                        "answer_sha256": sha256(answer.encode("utf-8")).hexdigest(), "citation_ids": sorted(inline),
                        "verbatim_tool_answer": True})
    return "\n\n".join(blocks), {"mode": "verified_tool_blocks", "generative_rewrite_calls": 0,
                                  "blocks": records, "new_numeric_inference": False}
