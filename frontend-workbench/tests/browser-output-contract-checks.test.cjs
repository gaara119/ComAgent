/* Pure offline Node unit fixtures in isolated temp roots. No browser/API/DB. */
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {atomicOutputId,assertProviderAtomicOutputs,assertRankOnlyOutputPreservation,assertSavedSemanticContract}=require('./browser-real-smoke-checks.cjs');
function fixture(t,requirements=['percentage_share']){
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'isolated-output-contract-unit-'));
 t.after(()=>{const resolved=fs.realpathSync(root);assert.equal(path.dirname(resolved),fs.realpathSync(os.tmpdir()));assert(path.basename(resolved).startsWith('isolated-output-contract-unit-'));fs.rmSync(resolved,{recursive:true,force:true});});
 const trace='11111111-1111-4111-8111-111111111111',relative='.runtime/agent-improvement-20261016/provider/local-unit/22222222222242228222222222222222.json';
 const capture={fixture_for_local_unit_test:true,trace_id:trace,request:{model:'deepseek-flash',messages:[{role:'user',content:JSON.stringify({runtime_context:{current_user_message:'Return a share.',user_brief:'',actual_conversation:[]}})}]},
  response:{id:'33333333-3333-4333-8333-333333333333',model:'deepseek-flash',usage:{prompt_tokens:10,completion_tokens:3,total_tokens:13},choices:[{message:{content:JSON.stringify({output_requirements:requirements})}}]}};
 const record={request:{session_id:'isolated-unit-session',message:'Return a share.'},response:{trace_id:trace,intent:{intent_version:1},metadata:{clarify:{semantic_contract:{output_requirements:[...requirements],query_scope:{}},switch:{clarification_id:'unit-card',intent_version:1,options:[{id:'unit-rank-count'}]}}},steps:[{name:'llm',status:'ok',output_summary:{json_valid:true,model:'deepseek-flash',usage:structuredClone(capture.response.usage),provider_capture:relative}}]}};
 function flush(){const file=path.join(root,relative);fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,JSON.stringify(capture));}
 flush();return {root,record,capture,flush,relative};
}
function choice(previous){
 const r=structuredClone(previous);r.request={...r.request,clarification_id:'unit-card',intent_version:1,choice_id:'unit-rank-count'};r.response.intent.intent_version=2;r.response.steps=[];return r;
}
test('opaque IDs including dotted, colon, underscore and dash forms stay whole',t=>{
 const f=fixture(t,['percentage_share','percentile_rank','employee.last_name','top_n:3','invoice-count']);
 assert.deepEqual(assertProviderAtomicOutputs(f.record,f.root),['percentage_share','percentile_rank','employee.last_name','top_n:3','invoice-count']);
});
for(const bad of [['百分比','age_share'],['percentage'],[],['ratio-fragment']])test('partial or missing complete atomic obligations are rejected: '+JSON.stringify(bad),t=>{
 const f=fixture(t);f.record.response.metadata.clarify.semantic_contract.output_requirements=bad;
 assert.throws(()=>assertProviderAtomicOutputs(f.record,f.root),/complete actual model output ID/);
});
test('natural-language precision cleanup is not tested by literal prose equality',t=>{
 const f=fixture(t,['百分比保留2位小数']);f.record.response.metadata.clarify.semantic_contract.output_requirements=['百分比'];
 assert.deepEqual(assertProviderAtomicOutputs(f.record,f.root),[]);
});
for(const kind of ['trace','usage','model','mock','invalid-json'])test('actual provider identity checks reject '+kind,t=>{
 const f=fixture(t);
 if(kind==='trace')f.capture.trace_id='44444444-4444-4444-8444-444444444444';
 if(kind==='usage')f.capture.response.usage.prompt_tokens=11;
 if(kind==='model')f.capture.response.model='unrelated-model';
 if(kind==='mock')f.capture.mock=true;
 if(kind==='invalid-json')f.capture.response.choices[0].message.content='not-json';
 f.flush();assert.throws(()=>assertProviderAtomicOutputs(f.record,f.root));
});
test('a trace cannot read another file outside the provider capture root',t=>{
 const f=fixture(t),outside=path.join(f.root,'outside.json');fs.writeFileSync(outside,JSON.stringify(f.capture));
 f.record.response.steps[0].output_summary.provider_capture='outside.json';
 assert.throws(()=>assertProviderAtomicOutputs(f.record,f.root),/actual project capture root/);
});
test('only successful json_valid=true replies establish atomic obligations',t=>{
 const f=fixture(t);f.capture.response.choices[0].message.content='invalid attempt';f.flush();
 f.record.response.steps[0].output_summary.json_valid=false;f.record.response.steps[0].status='error';
 assert.deepEqual(assertProviderAtomicOutputs(f.record,f.root),[]);
});
test('rank-only choice preserves every prior atomic obligation with actual card binding',t=>{
 const f=fixture(t,['percentage_share','employee.last_name']),r=choice(f.record);
 assertRankOnlyOutputPreservation(r,f.record,f.root);
 r.response.metadata.clarify.semantic_contract.output_requirements=['percentage_share'];
 assert.throws(()=>assertRankOnlyOutputPreservation(r,f.record,f.root),/preserve unrelated complete/);
});
test('already damaged prior state cannot mask corruption inherited by a choice',t=>{
 const f=fixture(t);f.record.response.metadata.clarify.semantic_contract.output_requirements=['百分比','partial_fragment'];
 const r=choice(f.record);assert.throws(()=>assertRankOnlyOutputPreservation(r,f.record,f.root),/original actual model output/);
});
test('stale card or version cannot prove rank-only preservation',t=>{
 const f=fixture(t),r=choice(f.record);r.request.intent_version=0;
 assert.throws(()=>assertRankOnlyOutputPreservation(r,f.record,f.root),/trusted card\/version/);
});
test('saved analysis must equal the complete returned semantic contract',t=>{
 const f=fixture(t),state={session_id:f.record.request.session_id,intent:{intent_version:1},analysis:structuredClone(f.record.response.metadata.clarify.semantic_contract)};
 assertSavedSemanticContract(state,f.record);state.analysis.output_requirements=['truncated'];
 assert.throws(()=>assertSavedSemanticContract(state,f.record),/complete returned semantic/);
});
test('an opaque percentile identifier cannot authorize percentage precision',t=>{
 const f=fixture(t,['percentile_rank']);f.record.response.metadata.clarify.semantic_contract.query_scope={requested_percent_decimals:2,percent_precision_source:{source:'program:explicit_percent_precision',evidence:'percentile_rank'}};
 assert.throws(()=>assertProviderAtomicOutputs(f.record,f.root),/opaque output ID/);
});
test('a real explicit prose precision quote is checked against current user source',t=>{
 const f=fixture(t);f.record.request.message='Return percentage rounded to 2 decimal places.';
 const text='percentage rounded to 2 decimal places';f.capture.request.messages[0].content=JSON.stringify({runtime_context:{current_user_message:f.record.request.message,user_brief:'',actual_conversation:[]}});f.flush();
 f.record.response.metadata.clarify.semantic_contract.query_scope={requested_percent_decimals:2,percent_precision_source:{source:'program:explicit_percent_precision',evidence:text}};
 assertProviderAtomicOutputs(f.record,f.root);
 f.record.response.metadata.clarify.semantic_contract.query_scope.percent_precision_source.evidence='not in actual source';
 assert.throws(()=>assertProviderAtomicOutputs(f.record,f.root),/actual user text/);
});
test('the atomic boundary is whole-ID based rather than a percent substring',()=>{
 assert(atomicOutputId('percentage_share')&&atomicOutputId('percentile_rank')&&atomicOutputId('duration_ms'));
 assert(!atomicOutputId('金额和百分比都保留2位小数')&&!atomicOutputId('percentage rounded to 2 decimal places'));
});
