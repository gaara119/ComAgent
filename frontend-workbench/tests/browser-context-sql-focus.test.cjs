/* Pure local fixtures/structure checks. Never launches Chromium or sends HTTP. */
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm');
const {spawnSync}=require('node:child_process');
const {FOCUS,CONTEXT_QUESTION,SQL_QUESTION,assertFocusBrief,businessLabels,assertContextSQL}=require('./browser-context-sql-focus.cjs');
const fixturePath=path.join(__dirname,'fixtures/actual022-context-sql-label-fields.json');
const fixture=JSON.parse(fs.readFileSync(fixturePath,'utf8'));
const harness=path.join(__dirname,'browser-real-smoke.cjs');
const clone=()=>structuredClone(fixture.record);

test('immutable actual022 field extraction preserves original source identity and full5846 brief',()=>{
 assert.equal(crypto.createHash('sha256').update(fs.readFileSync(fixturePath)).digest('hex'),'450b6d8a7e7ffa0320c50904d618bf2f1a9ff1a4b1c828bd25d58c277b4ea23f');
 assert.equal(fixture.new_prediction,false);assert.equal(fixture.source.sha256,'d87ffa0ffd671528f20becb3a91235c2feda849dc9a5fa22239a16698b1dd8a0');
 assertFocusBrief(fixture.brief);assert.equal(fixture.record.request.message,SQL_QUESTION);
});

test('unchanged actual022 ROUND business label is a hard failure despite successful SQL and amount',()=>{
 const before=JSON.stringify(fixture.record);
 assert.throws(()=>assertContextSQL(fixture.record,fixture.saved,fixture.brief),/SQL function syntax/);
 assert.equal(JSON.stringify(fixture.record),before);
});

test('explicit synthetic corrected-label fixture passes without changing actual raw SQL/values/state',()=>{
 const synthetic=clone();synthetic.fixture_only=true;synthetic.response.metadata.column_labels.invoice_revenue='发票销售额';
 assert.deepEqual(assertContextSQL(synthetic,fixture.saved,fixture.brief),['发票销售额']);
 assert.equal(synthetic.response.sql,fixture.record.response.sql);assert.deepEqual(synthetic.response.table,fixture.record.response.table);
 assert.deepEqual(synthetic.response.metadata.clarify.semantic_contract,fixture.record.response.metadata.clarify.semantic_contract);
});

for(const label of ['ROUND(发票销售额)','CAST(发票销售额 AS NUMERIC)','SUM(发票销售额)','COUNT(客户编号)','发票销售额::numeric','invoice_revenue','金额 public.invoice','金额 FROM invoice'])test('technical business header rejected: '+label,()=>{
 const synthetic=clone();synthetic.response.metadata.column_labels.invoice_revenue=label;
 assert.throws(()=>businessLabels(synthetic.response));
});

for(const label of ['发票销售额','重点市场发票金额','发票销售额（元）','发票销售额 (CNY)'])test('Chinese business header remains accepted: '+label,()=>{
 const synthetic=clone();synthetic.response.metadata.column_labels.invoice_revenue=label;
 assert.deepEqual(businessLabels(synthetic.response),[label]);
});

test('different projected subjects must have different actual display headers',()=>{
 const synthetic=clone();synthetic.response.table=[{a:1,b:2}];synthetic.response.metadata.result_columns=['a','b'];
 synthetic.response.metadata.column_labels={a:'发票金额',b:'发票金额'};
 assert.throws(()=>businessLabels(synthetic.response),/distinguishable/);
});

for(const defect of ['wrong_context','wrong_source_hash','wrong_metric','wrong_period','missing_market','wrong_owner','no_real_sql_exec'])test('context/SQL actual state remains mandatory: '+defect,()=>{
 const synthetic=clone();synthetic.response.metadata.column_labels.invoice_revenue='发票销售额';
 const contract=synthetic.response.metadata.clarify.semantic_contract;
 if(defect==='wrong_context')synthetic.request.context_id='different';
 if(defect==='wrong_source_hash')synthetic.response.metadata.session_context.content_sha256='0'.repeat(64);
 if(defect==='wrong_metric')contract.metric='detail_revenue';
 if(defect==='wrong_period')contract.time_scope.current.end='2027-01-01';
 if(defect==='missing_market')contract.filters[0].value.pop();
 if(defect==='wrong_owner')contract.filters[0].column='customer.country';
 if(defect==='no_real_sql_exec')synthetic.response.steps=[];
 assert.throws(()=>assertContextSQL(synthetic,fixture.saved,fixture.brief));
});

test('default prepared command remains unrun and focus prepares exactly2 without loading browser',()=>{
 for(const focus of ['',FOCUS]){
  const result=spawnSync(process.execPath,[harness],{encoding:'utf8',env:{...process.env,COMAGENT_REAL_UI_SMOKE:'0',COMAGENT_UI_SMOKE_FOCUS:focus}});
  assert.equal(result.status,0,result.stderr);const value=JSON.parse(result.stdout);
  assert.equal(value.status,'prepared_not_run');assert.equal(value.network_requests,0);
  if(focus){assert.equal(value.focus,FOCUS);assert.equal(value.expected_chat_requests,2);}
  else{assert.equal(value.plan.length,9);assert(!Object.hasOwn(value,'focus'));assert(!Object.hasOwn(value,'expected_chat_requests'));}
 }
});

test('unknown focus rejected before browser/network setup',()=>{
 const result=spawnSync(process.execPath,[harness],{encoding:'utf8',env:{...process.env,COMAGENT_REAL_UI_SMOKE:'0',COMAGENT_UI_SMOKE_FOCUS:'unknown'}});
 assert.notEqual(result.status,0);assert.match(result.stderr,/unsupported actual UI smoke focus/);
});

test('focus and default share exact old04/05 flow; focus preserves screenshot04/05 and observer path',()=>{
 const source=fs.readFileSync(harness,'utf8').replace(/\r\n/g,'\n');new vm.Script(source);
 assert.equal((source.match(/async function contextSQLFlow\(/g)||[]).length,1);
 assert.equal((source.match(/await contextSQLFlow\(\)/g)||[]).length,2);
 assert(source.includes("ask('long-brief-context-answer',CONTEXT_QUESTION,focus?4:null)"));
 assert(source.includes("ask('long-brief-sql',SQL_QUESTION,focus?5:null)"));
 assert(source.indexOf("if(focus){\n  await contextSQLFlow()")<source.indexOf("const sql=await ask('sql-invoice-region'"));
 assert(source.includes("checked('context_sql_focus_completed')"));assert(source.includes('collectStartedRequest(stopFile'));
 assert(source.includes("context-sql-final-session-state.json"));
 assert.equal(CONTEXT_QUESTION,'这份会话正文中的重点市场包含哪些国家？请只依据这份正文回答。');
 assert.equal(SQL_QUESTION,'咱们主期间内，重点市场的发票销售额一共是多少？');
});
