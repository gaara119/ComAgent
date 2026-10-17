const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {assertRegionChoice,assertRegionFollowup,assertContextOnly,chooseVisibleVirtualOption,assertLocalOperandPatch,assertLocalOperandLedger}=require('./browser-real-smoke-checks.cjs');
const actual=JSON.parse(fs.readFileSync(path.join(__dirname,'../../eval/artifacts/agent-improvement-20261016/evaluation/ui-candidate013-001/actual-ui-smoke.json'),'utf8'));
const byName=name=>actual.records.find(r=>r.name===name);
test('actual013 DB-backed body-only violation is now a hard smoke failure',()=>{
 const saved=JSON.parse(fs.readFileSync(path.join(__dirname,'../../eval/artifacts/agent-improvement-20261016/evaluation/ui-candidate013-001/actual-context-save.json'),'utf8'));
 assert.throws(()=>assertContextOnly(byName('long-brief-context-answer'),saved.response,saved.request.text),/SQL/);
});
test('actual013 retired field proof is now a hard smoke failure',()=>{
 assert.throws(()=>assertRegionChoice(byName('l1-real-region-switch'),byName('sql-invoice-region')),/old field/);
});
test('a real context quote requires exact Unicode codepoint offset/hash/source',()=>{
 const brief='😀前缀。真实正文定义。';
 const saved={context_id:'fixture',content_sha256:'a'.repeat(64)};
 const record={response:{sql:null,table:null,evidences:[],answer:'定义来自正文。',steps:[{name:'context_only_tool'}],
  metadata:{source_scope:'context',fusion:{actual_outputs:{s1:{source:'user_session_context',context_id:'fixture',sha256:saved.content_sha256,quotes:[{text:'真实正文定义。',char_start:4}]}}}}}};
 assertContextOnly(record,saved,brief);
 const bad=structuredClone(record);bad.response.metadata.fusion.actual_outputs.s1.quotes[0].char_start=5;
 assert.throws(()=>assertContextOnly(bad,saved,brief));
});
test('current explicit owner and year-only preservation assertions are meaningful',()=>{
 const previous={response:{intent:{filters:[{column:'invoice.billing_country',value:'France',evidence_ref:'old'}]}}};
 const binding={column:'customer.country',value:'France',source:'explicit_user_choice',value_index_revalidated:false,evidence_ref:'new',
  field_owner_proof:{column:'customer.country',source:'program:trusted_region_choice',choice_id:'country',clarification_id:'card'},
  value_origin:{evidence_ref:'old',role:'value_only_not_current_field_authorization'}};
 const next={request:{choice_id:'country',clarification_id:'card'},response:{intent:{filters:[binding]},metadata:{clarify:{semantic_contract:{region_scope:'customer.country',filters:[binding]}}}}};
 assertRegionChoice(next,previous);assertRegionFollowup(structuredClone(next),next);
 const bad=structuredClone(next);bad.response.intent.filters[0].field_owner_proof.column='invoice.billing_country';
 assert.throws(()=>assertRegionFollowup(bad,next));
});
for(const holderClass of ['rc-virtual-list-holder','ant-select-dropdown-list-holder'])test('real DOM scrolling reaches an option beyond first eight: '+holderClass,async()=>{
 const modules=process.env.COMAGENT_QA_NODE_MODULES;
 const {chromium}=modules?require(path.join(modules,'playwright')):require('playwright');
 const browser=await chromium.launch({headless:true,...(process.env.COMAGENT_QA_CHROME?{executablePath:process.env.COMAGENT_QA_CHROME}:{})});
 try{
  const page=await browser.newPage();const network=[];page.on('request',r=>network.push(r.url()));
  await page.setContent(`<div class="ant-select-dropdown"><div class="${holderClass}" style="height:160px;overflow:auto;position:relative"><div id="spacer" style="height:960px"></div></div></div><div id="chosen"></div><script>const holder=document.querySelector('.${holderClass}');function draw(){document.querySelectorAll('.option').forEach(x=>x.remove());let start=Math.floor(holder.scrollTop/32);for(let i=start;i<Math.min(30,start+8);i++){let row=document.createElement('div');row.className='option ant-select-item-option-content';row.style.cssText='position:absolute;left:0;height:32px;top:'+(i*32)+'px';row.textContent=i===25?'目标手册 真实列表':'文档'+i;row.onclick=()=>document.querySelector('#chosen').textContent=row.textContent;holder.append(row)}}holder.addEventListener('scroll',draw);draw();</script>`);
  await chooseVisibleVirtualOption(page,'目标手册 真实列表');
  assert.equal(await page.locator('#chosen').textContent(),'目标手册 真实列表');assert.deepEqual(network,[]);
 }finally{await browser.close();}
});

const source014=path.join(__dirname,'../../eval/artifacts/agent-improvement-20261016/evaluation/ui-candidate014-003');
const raw014=JSON.parse(fs.readFileSync(path.join(source014,'actual-ui-smoke.json'),'utf8'));
const oldWinner=raw014.records.find(x=>x.name==='inner-ranking-initial'),oldChoice=raw014.records.find(x=>x.name==='inner-ranking-count-switch');
const oldLedger=JSON.parse(fs.readFileSync(path.join(source014,'inner-count-final-session-state.json'),'utf8'));
test('actual014 wrong numerator source scope is a hard UI failure despite correct SQL/table',()=>{
 assert.throws(()=>assertLocalOperandPatch(oldChoice,oldWinner),/numerator/);
 assert.throws(()=>assertLocalOperandLedger(oldLedger,oldChoice));
});
test('local numerator source and actual ledger scope are checked independently from denominator',()=>{
 const fixture=structuredClone(oldChoice),ledger=structuredClone(oldLedger);
 fixture.response.metadata.clarify.semantic_contract.condition_sources.numerator.applies_to='numerator';
 ledger.analysis.condition_sources.numerator.applies_to='numerator';
 for(const entry of ledger.constraint_ledger)if(entry.field==='numerator'&&entry.status==='active')entry.applies_to='numerator';
 assertLocalOperandPatch(fixture,oldWinner);assertLocalOperandLedger(ledger,fixture);
 const changed=structuredClone(fixture);changed.response.metadata.clarify.semantic_contract.query_scope.denominator.metric='invoice_count';
 assert.throws(()=>assertLocalOperandPatch(changed,oldWinner));
});
