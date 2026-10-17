/* Actual API smoke: opt-in only, no fixture routing and no service restarts. */
const fs=require('fs'),path=require('path'),assert=require('assert');
const {assertRegionChoice,assertRegionFollowup,assertContextOnly,chooseVisibleVirtualOption,assertLocalOperandPatch,assertLocalOperandLedger,assertProviderAtomicOutputs,assertRankOnlyOutputPreservation,assertSavedSemanticContract}=require('./browser-real-smoke-checks.cjs');
const {assertBeforeRequest,collectStartedRequest}=require('./real-request-control.cjs');
const {FOCUS,CONTEXT_QUESTION,SQL_QUESTION,assertFocusBrief,assertContextSQL}=require('./browser-context-sql-focus.cjs');
const focus=process.env.COMAGENT_UI_SMOKE_FOCUS||null;assert(focus===null||focus===FOCUS,'unsupported actual UI smoke focus');
const plan=focus?['原完整B正文保存','原04正文独占问题','原05主期间重点市场SQL及业务表头']:['SQL真实结果','L1地域切换及版本失效','同会话改年份续问','完整长正文绑定及正文回答','长正文条件进入SQL','单文档RAG真实引用','文档定义→SQL混合链路','可选：客户金额默认→发票张数明确并列规则切换','可选：AW两个独立非空计数可辨识表头、百分比一位与撤销后原值'];
if(process.env.COMAGENT_REAL_UI_SMOKE!=='1'){
 console.log(JSON.stringify({status:'prepared_not_run',network_requests:0,requires:'COMAGENT_REAL_UI_SMOKE=1 after root approves final freeze',plan,...(focus?{focus,expected_chat_requests:2}: {})},null,2));
 process.exit(0);
}
const root=path.resolve(__dirname,'../..');
const stopFile=process.env.COMAGENT_QA_STOP_FILE?path.resolve(process.env.COMAGENT_QA_STOP_FILE):null;
if(stopFile)assert(!path.relative(root,stopFile).startsWith('..')&&!path.isAbsolute(path.relative(root,stopFile)),'stop file must be inside the project');
assertBeforeRequest(stopFile);
const base=process.env.COMAGENT_QA_UI_URL||'http://127.0.0.1:8501';
const target=new URL(base);assert(['127.0.0.1','localhost','[::1]'].includes(target.hostname),'only a loopback project UI is allowed');
const output=path.resolve(process.env.COMAGENT_QA_OUTPUT_DIR||path.join(root,'eval/artifacts/ui-white-integration',`actual-${Date.now()}-${process.pid}`));
const modules=process.env.COMAGENT_QA_NODE_MODULES;
const {chromium}=modules?require(path.join(modules,'playwright')):require('playwright');
const briefFile=process.env.COMAGENT_SMOKE_BRIEF_FILE||path.join(root,'eval/artifacts/agent-improvement-20261016/evaluation/full-candidate-003/input/B-cases.json');
const loaded=JSON.parse(fs.readFileSync(briefFile,'utf8'));
assert(Array.isArray(loaded)&&loaded[0]?.split==='dev','the full brief must come from the existing approved DEV input');
const brief=loaded[0].source_context?.text;assert(typeof brief==='string'&&brief.length>4000&&brief.length<=120000);
let browser,page,chatCount=0;
const records=[],checks=[],errors=[];
fs.mkdirSync(output,{recursive:true});assert.equal(fs.readdirSync(output).length,0,'browser evidence directory must be fresh and empty');
function save(){fs.writeFileSync(path.join(output,'actual-ui-smoke.json'),JSON.stringify({kind:'actual_browser_against_existing_API',fixture_only:false,plan,chat_requests:chatCount,checks,records,page_errors:errors,...(focus?{focus,expected_chat_requests:2}: {})},null,2));}
function checked(name){checks.push(name);save();}
function succeeded(record){assert.equal(record.response.status,'SUCCEEDED',`${record.name}: ${record.response.answer}`);assert(record.response.trace_id);}
async function interaction(name,action,screenshotNumber=null){
 assert(chatCount<(focus?2:12),'this smoke reached its explicit chat request limit');
 const record=await collectStartedRequest(stopFile,async()=>{
  const pending=page.waitForResponse(response=>new URL(response.url()).pathname==='/api/chat'&&response.request().method()==='POST',{timeout:245000});
  await action();const response=await pending;chatCount++;
  return {name,http_status:response.status(),request:response.request().postDataJSON(),response:await response.json()};
 },record=>{records.push(record);save();});
 assert.equal(record.http_status,200);
 await page.waitForFunction(()=>{
  const input=document.querySelector('textarea[aria-label="你的问题"]');
  if(!input||input.disabled||document.querySelector('.ant-spin-blur'))return false;
  let node=document.querySelector('.answer-region');
  while(node){if(Number(getComputedStyle(node).opacity)<0.99)return false;node=node.parentElement;}
  return true;
 },null,{timeout:245000});
 await page.screenshot({path:path.join(output,`${String(screenshotNumber??records.length).padStart(2,'0')}-${name}.png`),fullPage:true});
 return record;
}
async function ask(name,question,screenshotNumber=null){
 await page.getByRole('textbox',{name:'你的问题',exact:true}).fill(question);
 return interaction(name,()=>page.getByRole('button',{name:'发送问题',exact:true}).click(),screenshotNumber);
}
async function source(label){
 assertBeforeRequest(stopFile);
 await page.getByRole('combobox',{name:'数据来源',exact:true}).click();
 await page.getByText(label,{exact:true}).last().click();
}
async function chooseDocument(docId){
 assertBeforeRequest(stopFile);
 const response=await page.request.get(new URL('/api/documents',base).href);assert(response.ok());
 const entry=(await response.json()).documents?.find(item=>item.doc_id===docId&&item.ready);assert(entry,`document not ready: ${docId}`);
 const picker=page.getByRole('combobox',{name:'查询文档',exact:true});await picker.click();
 await chooseVisibleVirtualOption(page,entry.title||entry.doc_id,picker);
}
async function contextSQLFlow(){
 if(focus)assertFocusBrief(brief);
 await source('自动综合问答');
 await page.getByText('本会话正文（可选）',{exact:true}).click();
 await page.getByRole('textbox',{name:'本会话正文',exact:true}).fill(brief);
 assertBeforeRequest(stopFile);
 const savedPromise=page.waitForResponse(response=>new URL(response.url()).pathname==='/api/context'&&response.request().method()==='POST');
 await page.getByRole('button',{name:'保存会话正文',exact:true}).click();const savedResponse=await savedPromise;assert(savedResponse.ok());
 const saved=await savedResponse.json(),savedRequest=savedResponse.request().postDataJSON();assert.equal(savedRequest.text,brief);assert.equal(saved.characters,brief.length);
 fs.writeFileSync(path.join(output,'actual-context-save.json'),JSON.stringify({request:savedRequest,response:saved},null,2));
 await page.getByText('完整正文已绑定当前会话',{exact:true}).waitFor();
 const context=await ask('long-brief-context-answer',CONTEXT_QUESTION,focus?4:null);succeeded(context);
 assert.equal(context.request.context_id,saved.context_id);assert.equal(context.request.scope.route,'auto');
 assertContextOnly(context,saved,brief);
 checked('context_only_has_exact_source_hash_quotes_and_zero_database_execution');
 const contextSQL=await ask('long-brief-sql',SQL_QUESTION,focus?5:null);succeeded(contextSQL);
 assert.equal(contextSQL.request.context_id,saved.context_id);assert(contextSQL.response.sql&&contextSQL.response.table?.length);
 assert.equal(contextSQL.response.intent.time_scope.current.start,'2025-01-01');
 assert.equal(contextSQL.response.metadata.session_context.context_id,saved.context_id);
 checked('full_DEV_brief_bound_exactly_and_consumed_by_context_and_SQL');
 if(focus){
  for(const label of assertContextSQL(contextSQL,saved,brief))await page.getByRole('columnheader',{name:label,exact:true}).waitFor();
  const stateName=require('node:crypto').createHash('sha256').update(contextSQL.request.session_id).digest('hex')+'.json';
  const stateBytes=fs.readFileSync(path.join(root,'.runtime/sessions',stateName));
  assertSavedSemanticContract(JSON.parse(stateBytes.toString('utf8')),contextSQL);
  fs.writeFileSync(path.join(output,'context-sql-final-session-state.json'),stateBytes,{flag:'wx'});
  checked('context_SQL_business_headers_and_saved_state_match_actual_response');
 }
}
(async()=>{
 browser=await chromium.launch({headless:true,...(process.env.COMAGENT_QA_CHROME?{executablePath:process.env.COMAGENT_QA_CHROME}:{})});
 page=await browser.newPage({viewport:{width:1520,height:1120}});page.on('pageerror',error=>errors.push(error.message));
 await page.goto(base);await page.getByRole('navigation',{name:'主导航'}).getByRole('button',{name:'问答工作台',exact:true}).click();await page.getByRole('combobox',{name:'数据来源',exact:true}).waitFor();
 if(focus){
  await contextSQLFlow();checked('context_sql_focus_completed');
  assert.deepEqual(errors,[]);checked('no_browser_runtime_errors');save();await browser.close();
  console.log(JSON.stringify({status:'completed',focus,chat_requests:chatCount,checks,output},null,2));return;
 }
 await source('数据库问数');
 const sql=await ask('sql-invoice-region','2025年法国的发票销售额是多少？');succeeded(sql);assert(sql.response.sql&&sql.response.table?.length);
 const switchCard=sql.response.metadata?.clarify?.switch;assert(switchCard?.clarification_id&&Number.isInteger(switchCard.intent_version));
 const regionOption=switchCard.options.find(item=>item.id==='customer_country');assert(regionOption);
 assert(switchCard.options.every(item=>!('patch' in item)&&!('patches' in item)));
 const switched=await interaction('l1-real-region-switch',()=>page.getByRole('button',{name:regionOption.label,exact:true}).click());succeeded(switched);
 assert.equal(switched.request.choice_id,'customer_country');assert.equal(switched.request.clarification_id,switchCard.clarification_id);
 assert.equal(switched.response.metadata.clarify.semantic_contract.region_scope,'customer.country');
 assert(switched.response.intent.intent_version>sql.response.intent.intent_version);
 assert.deepEqual(switched.response.intent.time_scope,sql.response.intent.time_scope);
 assertRegionChoice(switched,sql);
 checked('real_L1_region_choice_changes_version_and_preserves_period_and_current_owner_provenance');
 const follow=await ask('same-session-year-followup','换成2024年呢？');succeeded(follow);
 assert.equal(follow.request.session_id,switched.request.session_id);
 assert.equal(follow.response.intent.time_scope.current.start,'2024-01-01');
 assert.equal(follow.response.metadata.clarify.semantic_contract.region_scope,'customer.country');
 assert(follow.response.intent.filters.some(item=>item.value==='France'));
 assertRegionFollowup(follow,switched);
 checked('real_followup_keeps_country_and_region_changes_only_period');
 await contextSQLFlow();
 await source('指定文档问答');await chooseDocument('project-metric-manual');
 const rag=await ask('single-doc-rag','这份指标手册中的客单价按什么计算？请给出原文依据。');succeeded(rag);
 assert(!rag.request.context_id);assert.deepEqual(rag.request.scope.doc_ids,['project-metric-manual']);
 assert(rag.response.evidences?.length&&rag.response.evidences.every(item=>item.doc_id==='project-metric-manual'));
 checked('single_document_RAG_returns_actual_citations_and_source_switch_clears_context');
 await source('数据库与文档');await chooseDocument('project-metric-manual');
 const hybrid=await ask('document-to-sql-hybrid','按口径手册里的客单价定义，计算2025年美国客户的客单价。');succeeded(hybrid);
 assert(hybrid.response.sql&&hybrid.response.table?.length&&hybrid.response.evidences?.length);
 assert(hybrid.response.metadata?.fusion?.definition_used_in_generation===true,'definition must actually participate in SQL generation');
 checked('real_hybrid_definition_used_in_SQL_with_query_and_document_evidence');
 if(process.env.COMAGENT_UI_SMOKE_INNER==='1'){
  await source('数据库问数');
  const winner=await ask('inner-ranking-initial','2025年买得最多的那位客户，其发票金额占全年发票总额的百分之多少？');succeeded(winner);
  assertProviderAtomicOutputs(winner,root);
  const card=winner.response.metadata?.clarify?.switch,choice=card?.options?.find(item=>item.id==='customer_inner_by_invoice_count');assert(choice);
  assert(choice.label.includes('并列按客户编号升序取第一'));assert(!card.options.some(item=>item.id==='customer_inner_by_quantity'));
  const count=await interaction('inner-ranking-count-switch',()=>page.getByRole('button',{name:choice.label,exact:true}).click());succeeded(count);
  const contract=count.response.metadata.clarify.semantic_contract;assert.equal(contract.metric,'invoice_revenue');assert.equal(contract.query_scope.rank_metric,'invoice_count');
  assert.deepEqual(contract.query_scope.rank_tie_breaker,{field:'customer.customer_id',direction:'asc',source:'explicit_user_choice'});
  assert.deepEqual(contract.time_scope,winner.response.metadata.clarify.semantic_contract.time_scope);
  assert.equal(contract.denominator,winner.response.metadata.clarify.semantic_contract.denominator);
  assertLocalOperandPatch(count,winner);
  assertProviderAtomicOutputs(count,root);assertRankOnlyOutputPreservation(count,winner,root);
  const stateName=require('node:crypto').createHash('sha256').update(count.request.session_id).digest('hex')+'.json';
  const statePath=path.join(root,'.runtime/sessions',stateName);const stateBytes=fs.readFileSync(statePath);
  const actualSavedState=JSON.parse(stateBytes.toString('utf8'));
  assertLocalOperandLedger(actualSavedState,count);assertSavedSemanticContract(actualSavedState,count);
  fs.writeFileSync(path.join(output,'inner-count-final-session-state.json'),stateBytes,{flag:'wx'});
  checked('actual_inner_count_choice_preserves_amount_denominator_and_period');
 }
 if(process.env.COMAGENT_UI_SMOKE_DISPLAY==='1'){
  await source('数据库问数');
  let dbPicker=page.getByRole('combobox',{name:'数据库',exact:true});await dbPicker.click();
  await chooseVisibleVirtualOption(page,'AdventureWorks',dbPicker);
  const counts=await ask('AW-independent-nullable-count-headers','客户档案中 personid 非空的有多少条，storeid 非空的有多少条？两个条件分别计数，不要求互斥。');succeeded(counts);
  assert.equal(counts.request.scope.db_id,'adventureworks');assert.equal(counts.response.table?.length,1);
  const countKeys=Object.keys(counts.response.table[0]),labels=counts.response.metadata?.column_labels||{};
  assert.equal(countKeys.length,2);assert.deepEqual(Object.values(counts.response.table[0]).map(Number).sort((a,b)=>a-b),[1336,19119]);
  const shown=countKeys.map(key=>labels[key]);assert(shown.every(label=>typeof label==='string'&&label.trim()));
  assert.equal(new Set(shown).size,2,'distinct count subjects collapsed into one display label');
  assert(shown.every(label=>!['数量','计数','count'].includes(label)),'requested count subjects must remain identifiable');
  for(const label of shown){assert(counts.response.answer.includes(label));await page.getByRole('columnheader',{name:label,exact:true}).waitFor();}
  checked('AW_two_independent_count_subjects_remain_distinct_in_actual_answer_and_UI');
  dbPicker=page.getByRole('combobox',{name:'数据库',exact:true});await dbPicker.click();
  await chooseVisibleVirtualOption(page,'Chinook',dbPicker);
  const one=await ask('explicit-percentage-one-decimal','2025年账单国家为 USA 的发票金额占该年全部发票金额的百分之多少？百分比保留一位小数。');succeeded(one);
  const percentageEntry=Object.entries(one.response.metadata?.result_format||{}).filter(([,rule])=>rule.kind==='percentage');
  assert.equal(percentageEntry.length,1);const [percentColumn,percentRule]=percentageEntry[0];
  assert.equal(percentRule.digits,1);assert([1,100].includes(percentRule.scale));
  const expectedOne=`${(Number(one.response.table[0][percentColumn])*percentRule.scale).toFixed(1)}%`;
  assert(one.response.answer.includes(expectedOne));await page.getByRole('cell',{name:expectedOne,exact:true}).waitFor();
  checked('actual_authorized_one_decimal_percentage_matches_answer_and_UI');
  const raw=await ask('percentage-precision-retired-raw','取消百分比小数位约定，按原值显示；其他条件不变。');succeeded(raw);
  assert.equal(raw.request.session_id,one.request.session_id);
  assert(raw.response.intent.intent_version>one.response.intent.intent_version);
  const rawEntry=Object.entries(raw.response.metadata?.result_format||{}).filter(([,rule])=>rule.kind==='percentage');
  assert.equal(rawEntry.length,1);const [rawColumn,rawRule]=rawEntry[0];assert.equal(rawRule.digits,null);
  const actualValue=Number(raw.response.table[0][rawColumn])*rawRule.scale;
  const rawToken=(raw.response.answer.match(/[+-]?\d+(?:\.\d+)?%/g)||[]).find(token=>Math.abs(Number(token.slice(0,-1))-actualValue)<1e-9);
  assert(rawToken&&rawToken.includes('.')&&rawToken.split('.')[1].length>3,'raw display was silently rounded again');
  await page.getByRole('cell',{name:rawToken,exact:true}).waitFor();
  const rawStateName=require('node:crypto').createHash('sha256').update(raw.request.session_id).digest('hex')+'.json';
  const rawStateBytes=fs.readFileSync(path.join(root,'.runtime/sessions',rawStateName));
  assertSavedSemanticContract(JSON.parse(rawStateBytes.toString('utf8')),raw);
  fs.writeFileSync(path.join(output,'percentage-raw-final-session-state.json'),rawStateBytes,{flag:'wx'});
  checked('actual_percentage_precision_retirement_matches_raw_answer_UI_and_saved_state');
 }
 assert.deepEqual(errors,[]);checked('no_browser_runtime_errors');save();await browser.close();console.log(JSON.stringify({status:'completed',chat_requests:chatCount,checks,output},null,2));
})().catch(async error=>{records.push({kind:error.code==='EVALUATION_STOPPED'?'smoke_stopped':'smoke_failure',code:error.code||null,error:String(error.stack||error)});save();if(page)await page.screenshot({path:path.join(output,'failure.png'),fullPage:true}).catch(()=>{});if(browser)await browser.close();console.error(error);process.exitCode=1;});
