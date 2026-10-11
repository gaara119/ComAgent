"""Prepare a reviewable D3 shared patch without changing the live D2 source."""
from __future__ import annotations

import difflib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'notes/d3/staging'


def replace_once(source,old,new):
    if source.count(old)!=1:raise ValueError(f'Expected one stable source anchor: {old[:100]}')
    return source.replace(old,new,1)


SCHEMA_FIELDS='''
    clarification_id: str | None = Field(default=None, min_length=1, max_length=128)
    intent_version: int | None = Field(default=None, ge=1)
    choice_id: str | None = Field(default=None, min_length=1, max_length=512)

    @model_validator(mode="after")
    def valid_clarification_resume(self):
        if (self.clarification_id is None) != (self.intent_version is None):
            raise ValueError("clarification_id 与 intent_version 必须同时提供")
        if self.choice_id is not None and self.clarification_id is None:
            raise ValueError("choice_id 必须属于带版本的澄清卡片")
        return self
'''

UI_CONTROLS='''

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
'''


def main():
    originals={path:(ROOT/path).read_text(encoding='utf-8') for path in
               ['qa_agent/schemas.py','qa_agent/pipeline.py','ui/app.py','api/main.py']}
    if '    clarification_id:' in originals['qa_agent/schemas.py']:
        raise SystemExit('D3 shared protocol is already integrated; the historical staging snapshot is preserved.')
    changed=dict(originals)
    schema=changed['qa_agent/schemas.py']
    schema=replace_once(schema,'BaseModel, ConfigDict, Field, field_validator','BaseModel, ConfigDict, Field, field_validator, model_validator')
    schema=replace_once(schema,'    scope: SourceScope = Field(default_factory=SourceScope)\n','    scope: SourceScope = Field(default_factory=SourceScope)\n'+SCHEMA_FIELDS)
    changed['qa_agent/schemas.py']=schema
    pipeline=changed['qa_agent/pipeline.py']
    sql_start=pipeline.index('def _sql(')
    chat_start=pipeline.index('\ndef chat(',sql_start)
    candidate=(STAGE/'sql_pipeline_candidate.txt').read_text(encoding='utf-8')
    pipeline=pipeline[:sql_start]+candidate+'\n'+pipeline[chat_start:]
    pipeline=replace_once(pipeline,'    settings = settings or get_settings()\n    trace = TraceRecorder(settings=settings)\n',
        '    settings = settings or get_settings()\n    if request.scope.db_id == "aw":\n        request = request.model_copy(update={"scope": request.scope.model_copy(update={"db_id": "adventureworks"})})\n    trace = TraceRecorder(settings=settings)\n')
    pipeline=replace_once(pipeline,'    if request.scope.db_id != "chinook":\n        return _unsupported(trace, "D1 SQL 通道仅支持 Chinook 数据库。")\n',
        '    if request.scope.db_id not in {"chinook", "adventureworks"}:\n        return _unsupported(trace, "SQL 来源请选择 Chinook 或 AdventureWorks 数据库。")\n')
    pipeline=replace_once(pipeline,'    return _sql(request, trace, settings, llm or JsonLLM(settings))\n',
        '    from qa_agent.clarify.state import DEFAULT_STORE\n    with DEFAULT_STORE.locked(request.session_id):\n        return _sql(request, trace, settings, llm or JsonLLM(settings))\n')
    changed['qa_agent/pipeline.py']=pipeline
    ui=changed['ui/app.py']
    ui=replace_once(ui,'def render_result(\n',UI_CONTROLS+'\n\ndef render_result(\n')
    ui=replace_once(ui,'    if result.clarification:\n        for item in result.clarification.get("options", []):\n            st.caption(safe_text(str(item)))\n',
        '    scope = SourceScope(route="sql", db_id=db_id, doc_ids=[]) if db_id else SourceScope(route="doc", db_id=None)\n    if db_id:\n        render_clarification_controls(result, base_url, scope)\n')
    ui=replace_once(ui,'        st.selectbox("数据库", ["Chinook"], disabled=True)\n        scope = SourceScope(route="sql", db_id="chinook", doc_ids=[])\n        context = "sql:chinook"\n',
        '        names = ["Chinook", "AdventureWorks"] if health.get("aw_database_ready") else ["Chinook"]\n        selected = st.selectbox("数据库", names, disabled=len(names) == 1)\n        db_id = "adventureworks" if selected == "AdventureWorks" else "chinook"\n        scope = SourceScope(route="sql", db_id=db_id, doc_ids=[])\n        context = f"sql:{db_id}"\n')
    ui=replace_once(ui,'        if health.get("database_ready") is False:\n',
        '        if health.get("aw_database_ready" if db_id == "adventureworks" else "database_ready") is False:\n')
    changed['ui/app.py']=ui
    # API health is staged only; real D2 process stays untouched.
    api=changed['api/main.py']
    api=api.replace('version="0.2.0"','version="0.3.0"').replace('"stage": "D2"','"stage": "D3"')
    api=replace_once(api,'共享显式来源入口；D2 增加值链接、可核验改写与多格式文档检索。',
        '共享显式来源入口；D3 增加 AdventureWorks Schema Linking 与分级澄清、版本化条件补丁。')
    api=replace_once(api,'    return {"status": "ok", "stage": "D3", "database_ready": database_ready,\n',
        '''    aw_ready = False
    try:
        if settings.aw_db_url:
            with psycopg.connect(settings.aw_db_url, connect_timeout=2) as connection:
                connection.read_only = True
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    aw_ready = cursor.fetchone() == (1,)
    except psycopg.Error:
        pass
    return {"status": "ok", "stage": "D3", "database_ready": database_ready,
            "aw_database_ready": aw_ready,
''')
    changed['api/main.py']=api
    STAGE.mkdir(parents=True,exist_ok=True)
    diffs=[]
    for path,source in changed.items():
        compile(source,str(ROOT/path),'exec')
        target=STAGE/path;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(source,encoding='utf-8')
        if source!=originals[path]:diffs.extend(difflib.unified_diff(originals[path].splitlines(keepends=True),source.splitlines(keepends=True),fromfile='a/'+path,tofile='b/'+path))
    (STAGE/'shared.patch').write_text(''.join(diffs),encoding='utf-8')
    print('Prepared a four-file preview patch only; live source unchanged. Runtime and UI tests await D2 freeze.')


if __name__=='__main__':main()
