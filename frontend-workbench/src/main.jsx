import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Alert, Button, Card, Collapse, ConfigProvider, Empty, Input, Select, Space, Spin, Table, Tag, Typography, message } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'antd/dist/reset.css';
import './styles.css';
import './workbench-white.css';
import { Overview, Analysis } from './Analytics.jsx';
import DatabaseManager from './DatabaseManager.jsx';
import DocumentManager from './DocumentManager.jsx';
import { displayValue, makeScope, sourceReady, databaseReady, publicDatabase, apiErrorMessage, safeDiagnostics, safeExport, safeText, makeContextRequest, bindContextResponse, attachContext, columnTitle } from './contract.mjs';

const { TextArea } = Input;
const statuses = { SUCCEEDED: ['已完成','success'], EMPTY_RESULT: ['无匹配记录','default'], NEEDS_CLARIFICATION: ['需要补充信息','warning'], UNSUPPORTED: ['当前范围不支持','warning'], FAILED: ['请求未完成','error'] };
const readable = value => displayValue(safeDiagnostics(value));
const uuid = () => globalThis.crypto?.randomUUID?.() || `ui-${Date.now()}-${Math.random().toString(36).slice(2)}`;
const docPath = id => `/api/documents/${encodeURIComponent(id)}`;
async function requestJSON(url, options = {}) {
  const response = await fetch(url, options);
  const body = await response.text();
  let data; try { data = JSON.parse(body); } catch { throw new Error('服务没有返回有效JSON，请检查API是否正常启动。'); }
  if (!response.ok) throw new Error(apiErrorMessage(data,response.status));
  return data;
}
function downloadJSON(value, name) {
  const url=URL.createObjectURL(new Blob([JSON.stringify(safeExport(value),null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function Results({ response, chooseEvidence }) {
  if (!response) return <Empty description="选择来源后，输入你的第一个问题。" />;
  const [baseLabel,color]=statuses[response.status] || ['未知响应状态','error'];
  const label=response.status==='EMPTY_RESULT' && response.table?.length && ['insufficient','EMPTY_RESULT'].includes(response.metadata?.fusion?.document_status) ? '查询完成，文档证据不足' : baseLabel;
  const parts=String(response.answer||'').split(/(\[E\d+\])/g);
  const columns=response.metadata?.result_columns?.length ? response.metadata.result_columns : Object.keys(response.table?.[0] || {});
  return <>
    <div className="answer-heading"><span className="agent-name">ComAgent</span><Tag color={color}>{label}</Tag></div>
    {response.metadata?.faithfulness_uncertain && <Alert type="warning" title="回答含未核实内容，请核对引用中的数字和单位。" showIcon />}
    <div className="answer-text">{parts.map((part,index)=> /^\[E\d+\]$/.test(part) ? <Button type="link" size="small" key={index} onClick={()=>chooseEvidence(part)}>{part}</Button> : <React.Fragment key={index}>{part}</React.Fragment>)}</div>
    {response.error && <Alert type="error" title={response.error.message || response.error.code} showIcon />}
    {Array.isArray(response.table) && <div className="results"><Table size="small" pagination={response.table.length>20 ? {pageSize:20,showSizeChanger:false} : false} scroll={columns.length>4 ? {x:'max-content'} : undefined} dataSource={response.table.map((row,index)=>({record:row,rowKey:index}))} rowKey="rowKey" columns={columns.map(key=>({title:columnTitle(key,response.metadata?.column_labels),key,render:(_,entry)=>displayValue(entry.record[key], response.metadata?.result_format?.[key])}))} locale={{emptyText:'结果表为空；不等同于COUNT为0或SUM为NULL。'}} /></div>}
    {response.metadata?.truncated && <Alert type="warning" title="结果已截断，当前显示的行并非完整结果。" showIcon />}
    {response.metadata?.nlu?.patches?.length>0 && <details className='rewrite-details'><summary>名称识别与修改依据</summary><pre>{JSON.stringify(safeDiagnostics({patches:response.metadata.nlu.patches,mentions:response.metadata.nlu.mentions}),null,2)}</pre></details>}
    {response.rewritten_question && <Collapse size="small" items={[{key:'rewrite',label:'查看问题改写',children:<div className="plain-text">{response.rewritten_question}</div>}]} />}
  </>;
}
function Clarification({ card, submit, busy, switchMode=false }) {
  const [extra,setExtra]=useState('');
  if (!card) return null;
  const canResume=Boolean(card.clarification_id && Number.isInteger(card.intent_version) && (switchMode || card.resume_supported));
  return <section className="clarification-box">
    <h3>{switchMode?'切换统计口径':'请补充查询条件'}</h3><p>{card.question || card.reason || '请选择或补充具体条件。'}</p>
    <Space wrap>{(card.options||[]).map((option,index)=>typeof option==='object' && option.id ? <Button aria-label={option.label} key={option.id} disabled={busy||!canResume} onClick={()=>submit(option.label,{card,choice:option.id})}>{option.label}</Button> : <Tag key={index}>{readable(option)}</Tag>)}</Space>
    {!switchMode && canResume && <div className="resume-form"><Input aria-label="补充查询条件" value={extra} maxLength={4000} onChange={event=>setExtra(event.target.value)} onPressEnter={()=>{if(extra.trim()){submit(extra.trim(),{card});setExtra('');}}} placeholder="也可以输入补充说明" disabled={busy}/><Button disabled={busy||!extra.trim()} onClick={()=>{submit(extra.trim(),{card});setExtra('');}}>提交补充</Button></div>}
    {!canResume && <p className="subtle">此卡片不支持版本化续问，请根据提示重新输入完整问题。</p>}
  </section>;
}
function ProofPane({ record, selected, setSelected, documents }) {
  const result=record?.response;
  const evidence=result?.evidences?.[selected];
  const document=documents.find(item=>item.doc_id===evidence?.doc_id);
  const intent=result?.intent;
  const region=result?.metadata?.clarify?.region_scope;
  const regionName={'customer.country':'客户所在地','invoice.billing_country':'发票账单国家'}[region] || region;
  const steps=(result?.steps || []).slice(0,20).map(step=>safeDiagnostics(step));
  const fusion=safeDiagnostics(result?.metadata?.fusion);
  const schema=safeDiagnostics(result?.metadata?.schema_linker);
  return <Card className="proof-card" title="来源与统计口径">
    {!result ? <p className="subtle">查询后显示实际SQL、引用原文、统计口径和执行记录。</p> : <>
      {fusion?.plan_stages?.length>0 && <section className='fusion-section'><h3>跨源执行</h3>{fusion.plan_stages.map((stage,index)=><div key={index} className='trace-row'><Tag color={index<(fusion.completed_stages||0)?'success':'default'}>{index<(fusion.completed_stages||0)?'完成':'待完成'}</Tag><span>{index+1}. {readable(stage)}</span></div>)}{fusion.transferred_entity && <p className='assumption'>数据库结果传给文档检索：{readable(fusion.transferred_entity.artist_name)}（artist_id={readable(fusion.transferred_entity.artist_id)}）</p>}{fusion.definition_context && <><p className='subtle'>{fusion.definition_used_in_generation?'检索定义已用于SQL生成，并在执行前校验。':'服务未确认定义已用于SQL生成。'}</p><details><summary>查看传递的指标定义</summary><pre>{JSON.stringify(fusion.definition_context,null,2)}</pre></details></>}</section>}
      {result.sql && <section><h3>实际查询SQL</h3><pre>{result.sql}</pre><Typography.Paragraph copyable={{text:result.sql}}>复制SQL</Typography.Paragraph></section>}
      {schema && <section className='schema-section'><h3>表定位与关联依据</h3>{schema.selected_tables?.map(name=><div key={name}><Tag color='blue'>{name}</Tag><p className='subtle'>{readable(schema.reasons?.[name]||[])}</p></div>)}{schema.disconnected_components?.length>1 && <Alert title='所选对象分属不同关联分量，不能凭名称构造关联。' type='warning' showIcon/>}{schema.join_paths?.length>0 && <details><summary>真实外键路径（{schema.join_paths.length}条）</summary><pre>{JSON.stringify(schema.join_paths,null,2)}</pre></details>}{schema.excluded_tables && Object.keys(schema.excluded_tables).length>0 && <details><summary>未选表及理由</summary><pre>{JSON.stringify(schema.excluded_tables,null,2)}</pre></details>}</section>}
      {result.evidences?.length>0 && <section><h3>引用原文</h3><Space wrap>{result.evidences.map((item,index)=><Button key={item.evidence_id||index} size="small" type={index===selected?'primary':'default'} onClick={()=>setSelected(index)}>{item.evidence_id || `E${index+1}`}</Button>)}</Space>
        {evidence && <><p className="evidence-title">{evidence.doc_title || evidence.doc_id}</p><p className="subtle">{evidence.page ? `物理页 ${evidence.page}` : (evidence.section_path||[]).join(' / ') || '非分页文档'}{evidence.bbox ? ' · 已提供区域坐标' : ''}</p><blockquote>{evidence.text}</blockquote>
          {evidence.page && <img className="page-preview" src={`${docPath(evidence.doc_id)}/pages/${evidence.page}`} alt={`引用原文物理页 ${evidence.page}`} onError={event=>{event.currentTarget.hidden=true;}} />}
          {!evidence.page && document?.format==='png' && <img className="page-preview" src={`${docPath(evidence.doc_id)}/file`} alt={evidence.doc_title||'来源图片'} />}
          <a href={`${docPath(evidence.doc_id)}/file${evidence.page?`#page=${evidence.page}`:''}`} target="_blank" rel="noreferrer">打开/下载登记原文件</a>
          {evidence.bbox && <details><summary>查看区域坐标</summary><code>{readable(evidence.bbox)}</code></details>}
        </>}
      </section>}
      {intent && <section className="proof-section"><h3>本次查询口径</h3><dl><dt>指标</dt><dd>{intent.metric||intent.task_type||'未提供'}</dd>{regionName && <><dt>地域</dt><dd>{regionName}</dd></>}<dt>期间</dt><dd>{intent.time_scope ? readable(intent.time_scope) : '未单独提供期间对象'}</dd><dt>过滤</dt><dd>{intent.filters?.length ? readable(intent.filters) : '未提供过滤条件对象'}</dd></dl>{(intent.assumptions||[]).map((item,index)=><p className="assumption" key={index}>默认/假设：{readable(item)}</p>)}</section>}
      <Collapse size="small" items={[{key:'trace',label:'实际执行记录',children:<>{steps.length ? steps.map((step,index)=><div className="trace-row" key={index}><Tag color={step.status==='error'?'error':step.status==='warn'?'warning':'default'}>{step.status}</Tag><span>{safeText(step.name)}</span><span className="subtle">{step.latency_ms ?? 0} ms</span>{(step.input_summary||step.output_summary) && <details><summary>输入与输出</summary><pre>{JSON.stringify(safeDiagnostics({input:step.input_summary,output:step.output_summary}),null,2)}</pre></details>}</div>) : <p>服务没有提供步骤记录。</p>}{result.metadata?.latency_ms!=null && <p className='subtle'>服务端总耗时：{result.metadata.latency_ms} ms</p>}<p className="subtle break-all">Trace：{result.trace_id||'未提供'}</p></>}]} />
    </>}
  </Card>;
}
function DataHome({ health, databases, documents, docsError, useDocument, manageDatabases }){
  return <><div className="page-heading"><div><h2>数据与文档</h2><p className="subtle">查看可查询的数据库与已处理文档。</p></div><Button onClick={manageDatabases}>添加与管理数据库</Button></div><div className="database-list">{databases.map(item=><Card key={item.db_id} title={item.label}><Tag color={databaseReady(item.db_id,health,databases)?'success':'warning'}>{databaseReady(item.db_id,health,databases)?'只读数据库已就绪':'尚未就绪'}</Tag><p className="subtle">{item.builtin?'项目内置数据库':'本地登记连接'}{item.catalog_summary?.table_count!=null?` · ${item.catalog_summary.table_count} 张表`:''}</p></Card>)}</div>{docsError && <Alert title={docsError} type="warning" showIcon style={{marginBottom:16}} />}<Card title="登记文档"><Table size="small" rowKey="doc_id" dataSource={documents} pagination={{pageSize:10,showSizeChanger:false}} scroll={{x:500}} columns={[{title:'文档',dataIndex:'title',render:(title,item)=><><div>{title||item.doc_id}</div><span className="subtle">{item.doc_id}</span></>},{title:'格式',dataIndex:'format'},{title:'页数',dataIndex:'page_count',render:v=>v??'非分页'},{title:'索引',dataIndex:'ready',render:v=><Tag color={v?'success':'warning'}>{v?'已就绪':'未就绪'}</Tag>},{title:'操作',render:(_,item)=><Button disabled={!item.ready} onClick={()=>useDocument(item)}>用此文档提问</Button>}]} /></Card></>;
}
function App(){
  const [page,setPage]=useState('workspace'),[health,setHealth]=useState(null),[healthError,setHealthError]=useState(''),[documents,setDocuments]=useState([]),[docsError,setDocsError]=useState(''),[refreshing,setRefreshing]=useState(false);
  const [databases,setDatabases]=useState([]),[databasesError,setDatabasesError]=useState(''),[databaseManagerOpen,setDatabaseManagerOpen]=useState(false);
  const [documentManagerOpen,setDocumentManagerOpen]=useState(false),[documentManagerMode,setDocumentManagerMode]=useState('file');
  const [documentTextTarget,setDocumentTextTarget]=useState('knowledge');
  const [historyRecord,setHistoryRecord]=useState(null);
  const [route,setRoute]=useState('sql'),[db,setDb]=useState('chinook'),[doc,setDoc]=useState(''),[question,setQuestion]=useState(''),[history,setHistory]=useState([]),[busy,setBusy]=useState(false),[error,setError]=useState(''),[selectedEvidence,setSelectedEvidence]=useState(0);
  const session=useRef(uuid()),requestNumber=useRef(0);
  const [savedContextText,setSavedContextText]=useState(''),[contextBinding,setContextBinding]=useState(null),[savingContext,setSavingContext]=useState(false);
  const latest=history.at(-1),result=latest?.response;
  const scope=makeScope(route,db,doc);
  const currentDoc=documents.find(item=>item.doc_id===doc);
  const builtins=[{db_id:'chinook',name:'Chinook',label:'Chinook',builtin:true,configured:health?.database_ready===true,catalog_exists:health?.database_ready===true},{db_id:'adventureworks',name:'AdventureWorks',label:'AdventureWorks',builtin:true,configured:health?.aw_database_ready===true,catalog_exists:health?.aw_database_ready===true}];
  const databaseList=[...builtins.map(item=>databases.find(entry=>entry.db_id===item.db_id)||item),...databases.filter(item=>!builtins.some(entry=>entry.db_id===item.db_id))];
  const ready=sourceReady(route,db,doc,health,documents,databaseList);
  function openDocuments(mode,target='knowledge'){if(busy)return;setDocumentManagerMode(mode);setDocumentTextTarget(target);setDocumentManagerOpen(true);}
  async function refreshDatabases(){
    try{const data=await requestJSON('/api/databases');const list=(data.databases||[]).map(publicDatabase).filter(Boolean);setDatabases(list);setDatabasesError('');return list;}
    catch(exc){setDatabasesError(exc.message);return null;}
  }
  async function refresh(){
    setRefreshing(true);
    const values=await Promise.allSettled([requestJSON('/health'),requestJSON('/api/documents'),refreshDatabases()]);
    if(values[0].status==='fulfilled'){setHealth(values[0].value);setHealthError('');}else{setHealth(null);setHealthError(values[0].reason.message);}
    if(values[1].status==='fulfilled'){const list=values[1].value.documents||[];setDocuments(list);setDocsError('');}else{setDocuments([]);setDocsError(values[1].reason.message);}
    setRefreshing(false);
  }
  useEffect(()=>{refresh();},[]);
  function reset(){requestNumber.current++;session.current=uuid();setHistory([]);setHistoryRecord(null);setError('');setQuestion('');setSelectedEvidence(0);setSavedContextText('');setContextBinding(null);}
  function changeSource(nextRoute,nextDb=db,nextDoc=doc){if(busy)return;if(nextRoute==='doc'&&!nextDoc)nextDoc=documents.find(item=>item.ready)?.doc_id||'';reset();setRoute(nextRoute);setDb(nextDb);setDoc(nextDoc);}
  async function saveSessionContext(text){
    const payload=makeContextRequest(session.current,text);
    const ticket=++requestNumber.current;setSavingContext(true);setError('');
    try{
      const saved=await requestJSON('/api/context',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const binding=bindContextResponse(saved,payload.session_id,scope);
      if(ticket===requestNumber.current){setContextBinding(binding);setSavedContextText(payload.text);setHistory([]);setHistoryRecord(null);setSelectedEvidence(0);}
    }finally{if(ticket===requestNumber.current)setSavingContext(false);}
  }
  async function submit(text,resume={}){
    if(busy||!ready||!String(text||'').trim())return;
    if(String(text).trim().length>4000){setError('问题不能超过4000个字符。');return;}
    const card=resume.card;
    if(card && (!card.clarification_id || !Number.isInteger(card.intent_version))){setError('澄清卡缺少有效ID或版本，请重新提问。');return;}
    let payload={session_id:session.current,message:String(text).trim(),scope:card?latest.scope:scope};
    try{payload=attachContext(payload,contextBinding);}catch(exc){setError(exc.message);return;}
    if(card){payload.clarification_id=card.clarification_id;payload.intent_version=card.intent_version;if(resume.choice)payload.choice_id=resume.choice;}
    const ticket=++requestNumber.current;setBusy(true);setError('');
    const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),240000);
    try{
      const response=await requestJSON('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:controller.signal});
      if(!statuses[response.status] || typeof response.answer!=='string')throw new Error('响应不符合AnswerEnvelope协议，请检查API版本。');
      if(ticket===requestNumber.current){setHistory(items=>[...items,{id:uuid(),question:payload.message,scope:payload.scope,response}]);setQuestion('');setSelectedEvidence(0);}
    }catch(exc){if(ticket===requestNumber.current)setError(exc.name==='AbortError'?'请求超时，尚未获得结果。请确认后端状态。':exc.message);}
    finally{clearTimeout(timer);if(ticket===requestNumber.current)setBusy(false);}
  }
  function chooseEvidence(id){const index=(result?.evidences||[]).findIndex(item=>String(item.evidence_id).replace(/[\[\]]/g,'')===id.replace(/[\[\]]/g,''));if(index>=0)setSelectedEvidence(index);else message.info('该标记未对应返回的证据，请核对实际引用。');}
  const activeCard=result?.status==='NEEDS_CLARIFICATION'&&result.clarification?.resume_supported?result.clarification:null;
  return <ConfigProvider locale={zhCN} theme={{token:{colorPrimary:'#557f8b',borderRadius:14,fontFamily:'Microsoft YaHei, system-ui, sans-serif',fontSize:14,colorBgLayout:'#f4f7fa'}}}><div className={`app page-${page}`}>
    <header className="topbar"><a className="brand" href="#overview" onClick={event=>{event.preventDefault();setPage('overview');}}>ComAgent <span className="brand-subtitle">分析中心</span></a><nav className="topnav" aria-label="主导航">{[{key:'overview',label:'数据概览'},{key:'analysis',label:'数据分析'},{key:'workspace',label:'问答工作台'},{key:'data',label:'数据与文档'},{key:'history',label:'运行记录'}].map(item=><button key={item.key} type="button" aria-current={page===item.key?'page':undefined} className={page===item.key?'selected':''} onClick={()=>setPage(item.key)}>{item.label}</button>)}</nav><Space className="header-status"><Tag color={health?.status==='ok'?'success':'warning'}>{health?.ui_test_fixture?'接口模拟验证':health?.status==='ok'?'API已连接':'API未连接'}</Tag><Button onClick={refresh} loading={refreshing} disabled={busy}>刷新状态</Button></Space></header>
    <div className="shell"><main className="main">
      {page==='overview' && <Overview latestResponse={result} onNavigate={setPage}/>}
      {page==='analysis' && <Analysis latestResponse={result} onNavigate={setPage} onUseQuestion={text=>{if(busy){message.info('请等待当前请求完成后再使用分析摘要。');return;}setQuestion(text);setPage('workspace');}}/>}
      {page==='workspace' && <>
        <div className="page-heading"><div><h2>问答工作台</h2><p className="subtle">选择数据范围，输入问题，核对结果与来源。</p></div><Button disabled={busy} onClick={reset}>新会话</Button></div>
        {healthError && <Alert type="warning" title="无法连接项目API" description={`${healthError} 请先启动原项目FastAPI服务。`} showIcon style={{marginBottom:16}} />}
        {health?.llm_configured===false && <Alert type="warning" title="后端尚未配置模型，请在原项目配置后重启API。" showIcon style={{marginBottom:16}} />}
        <div className="workspace workspace-query"><Card className="conversation">
          <div className="source-bar">
            <div className="source-field"><label>数据来源</label><Select aria-label="数据来源" value={route} onChange={value=>changeSource(value)} disabled={busy} options={[{value:'auto',label:'自动综合问答'},{value:'sql',label:'数据库问数'},{value:'doc',label:'指定文档问答'}]} /></div>
            {['sql','auto'].includes(route)&&<div className="source-field"><label>数据库</label><Select aria-label="数据库" value={db} disabled={busy} onChange={value=>changeSource(route,value)} options={databaseList.map(item=>({value:item.db_id,label:item.label,disabled:!databaseReady(item.db_id,health,databaseList)}))} /></div>}
            {route!=='sql'&&<div className="source-field source-document"><label>文档范围</label><Select aria-label="查询文档" className="doc-select" value={route==='auto'?doc:doc||undefined} disabled={busy} placeholder="选择已处理文档" onChange={value=>changeSource(route,db,value)} options={[...(route==='auto'?[{value:'',label:'全部登记文档'}]:[]),...documents.map(item=>({value:item.doc_id,label:item.title||item.doc_id,disabled:!item.ready}))]} /></div>}
            <Button className="source-add-button" disabled={busy} onClick={()=>setDatabaseManagerOpen(true)}>＋ 添加数据库</Button>
            <Button className="source-add-button" disabled={busy} onClick={()=>openDocuments('file')}>＋ 上传文档</Button>
            <Button className="source-add-button" disabled={busy} onClick={()=>openDocuments('text')}>＋ 添加文字</Button>
            <Tag className="source-hint">{route==='sql'?'只读查询':route==='auto'?'按问题选择来源':'限定当前文档'}</Tag>
          </div>
          {contextBinding&&<div className="session-text-summary"><Tag color="success">本次会话文字 · {contextBinding.characters} 字 · v{contextBinding.version}</Tag><Button type="link" disabled={busy} onClick={()=>openDocuments('text','session')}>编辑文字</Button></div>}
          {route==='auto' && <Alert type='info' title='支持艺术家销售排名→介绍文档，以及指标手册定义→SQL计算。跨源数据库为Chinook。' description={db==='chinook'?'可在问题中直接提出数据库与文档联动需求，系统按问题安排处理步骤。':'上述两类跨源流程需选择Chinook；当前所选数据库仍用于其目录范围内问数。'} showIcon style={{marginBottom:16}}/>}
          {route!=='sql' && doc && !currentDoc?.ready && <Alert type='warning' title='当前选择的文档已移除或尚未就绪，请重新选择来源后再提问。' showIcon style={{marginBottom:16}}/>}
          {route!=='sql'&&docsError && <Alert title={docsError} type="warning" showIcon />}
          <div className="composer"><label className="question-label" htmlFor="workspace-question">你的问题</label><TextArea id="workspace-question" aria-label="你的问题" value={question} onChange={event=>setQuestion(event.target.value)} placeholder={activeCard?'输入需要补充的条件':route==='sql'?'例如：来自巴西的客户有多少位？':route==='auto'?'例如：销售额最高的艺术家是谁？介绍他的音乐风格。':'输入与当前文档有关的问题'} maxLength={4000} showCount autoSize={{minRows:4,maxRows:8}} disabled={busy} /><div className="composer-actions"><span className="subtle">{ready?'续问保留当前会话；切换来源会新建会话。':'当前来源或模型尚未就绪。'}</span><Space>{latest && <Button disabled={busy} onClick={()=>downloadJSON({schema_version:'comagent-answer-export-v1',exported_at_utc:new Date().toISOString(),session_id:session.current,...latest},'ComAgent-本次问答结果.json')}>导出本次结果</Button>}<Button aria-label={activeCard?'提交补充':'发送问题'} type="primary" loading={busy} disabled={!ready||!question.trim()} onClick={()=>submit(question,activeCard?{card:activeCard}:{})}>{activeCard?'提交补充':'发送问题'} <span aria-hidden="true">↗</span></Button></Space></div></div>
          {error && <Alert type="error" title={error} showIcon style={{marginTop:16}} />}
          {(latest||busy)&&<Spin spinning={busy} tip={savingContext?'正在保存会话文字……':'正在等待实际查询结果……'}><section className="query-result" aria-label="查询结果">
            {latest&&<div className="question-bubble"><span className="subtle">本次问题</span><p>{latest.question}</p></div>}
            <div className="answer-region">{result&&<Results response={result} chooseEvidence={chooseEvidence} />}{result?.clarification && <Clarification key={result.clarification.clarification_id||latest.id} card={result.clarification} submit={submit} busy={busy}/>} {result?.metadata?.clarify?.switch && <Clarification key={result.metadata.clarify.switch.clarification_id} card={result.metadata.clarify.switch} submit={submit} busy={busy} switchMode/>}</div>
          </section></Spin>}
          {history.length>1 && <Collapse className="history" size="small" items={[{key:'history',label:`较早的会话记录（${history.length-1}条）`,children:history.slice(0,-1).map(item=><div className="history-entry" key={item.id}><strong>{item.question}</strong><div className="plain-text">{item.response.answer}</div><Tag>{statuses[item.response.status]?.[0]||item.response.status}</Tag></div>)}]} />}
        </Card>{latest&&<ProofPane record={latest} selected={selectedEvidence} setSelected={setSelectedEvidence} documents={documents}/>}</div>
      </>}
      {page==='data' && <><Space wrap style={{marginBottom:16}}><Button className="source-add-button" disabled={busy} onClick={()=>openDocuments('file')}>＋ 上传文档</Button><Button className="source-add-button" disabled={busy} onClick={()=>openDocuments('text')}>＋ 添加文字</Button></Space><DataHome health={health} databases={databaseList} documents={documents} docsError={docsError} manageDatabases={()=>{if(!busy)setDatabaseManagerOpen(true);}} useDocument={item=>{if(busy){message.info('请等待当前请求完成后切换来源。');return;}changeSource('doc',db,item.doc_id);setPage('workspace');}}/></>}
      {page==='history' && <><div className="page-heading"><div><div className="section-eyebrow">QUERY HISTORY</div><h2>运行记录</h2><p className="subtle">本次会话的真实请求与返回结果；新会话或切换来源会清空，可在工作台导出保存。</p></div><Button onClick={()=>setPage('workspace')}>返回工作台</Button></div>{history.length?<div className="workspace"><div className="run-list">{history.slice().reverse().map(item=><Card key={item.id} className={`run-card ${historyRecord?.id===item.id?'selected':''}`}><div className="run-heading"><h3>{item.question}</h3><Tag color={statuses[item.response.status]?.[1]}>{statuses[item.response.status]?.[0]||item.response.status}</Tag></div><p className="plain-text run-answer">{item.response.answer}</p><Space wrap><Button onClick={()=>{setHistoryRecord(item);setSelectedEvidence(0);}}>查看查询依据</Button><Button onClick={()=>downloadJSON({schema_version:'comagent-answer-export-v1',session_id:session.current,...item},'ComAgent-问答记录.json')}>导出记录</Button></Space></Card>)}</div><ProofPane record={historyRecord||latest} selected={selectedEvidence} setSelected={setSelectedEvidence} documents={documents}/></div>:<Card className="empty-history"><Empty description="还没有运行记录。"/><Button type="primary" onClick={()=>setPage('workspace')}>开始查询</Button></Card>}</>}
    </main></div>
    <DocumentManager open={documentManagerOpen} mode={documentManagerMode} textTarget={documentTextTarget} sessionText={savedContextText} onSaveSession={saveSessionContext} onClose={()=>setDocumentManagerOpen(false)} request={requestJSON} onBusyChange={setBusy}
      onAdded={async item=>{const data=await requestJSON('/api/documents');setDocuments(data.documents||[]);setDocsError('');reset();setRoute('doc');setDoc(item.doc_id);setPage('workspace');}}/>
    <DatabaseManager open={databaseManagerOpen} onClose={()=>setDatabaseManagerOpen(false)} request={requestJSON} databases={databaseList} listError={databasesError} disabled={busy}
      onRefreshList={refreshDatabases}
      onAdded={async item=>{setDatabases(items=>[...items.filter(entry=>entry.db_id!==item.db_id),item]);await refreshDatabases();reset();setRoute('sql');setDb(item.db_id);setDoc('');setPage('workspace');}}
      onRemoved={async id=>{setDatabases(items=>items.filter(item=>item.db_id!==id));await refreshDatabases();if(db===id){reset();setRoute('sql');setDb('chinook');setDoc('');}}}/>

  </div></ConfigProvider>;
}
class ErrorBoundary extends React.Component{constructor(props){super(props);this.state={failed:false};}static getDerivedStateFromError(){return {failed:true};}render(){return this.state.failed?<div style={{padding:24}}>页面渲染失败，请刷新页面并核对后端响应协议。可以刷新页面后重试。</div>:this.props.children;}}
createRoot(document.getElementById('root')).render(<ErrorBoundary><App/></ErrorBoundary>);
