import { test } from 'node:test';
import assert from 'node:assert/strict';
import { displayValue, makeScope, sourceReady, databaseReady, publicDatabase, apiErrorMessage, databaseErrorMessage, safeDiagnostics, safeExport, safeText, makeContextRequest, bindContextResponse, attachContext, columnTitle } from '../src/contract.mjs';

test('diagnostic keys are hidden recursively and case-insensitively', () => {
  const input={api_key:'fixture-key',nested:{PASSWORD:'fixture-pass',authorization:'fixture-auth',dsn:'fixture-dsn',system_prompt:'fixture-system',user_prompt:'fixture-user',full_prompt:'fixture-full',catalog:{tables:['fixture-secret-table']}},llm_api_key:'fixture-llm',db_url:'fixture-db',secret:'fixture-secret',safe_count:35};
  const before=JSON.stringify(input), output=safeDiagnostics(input);
  assert.equal(output.api_key,'[已隐藏]');assert.equal(output.safe_count,35);
  for (const value of Object.values(output.nested)) assert.equal(value,'[已隐藏]');
  assert.equal(JSON.stringify(input),before);
  assert(!JSON.stringify(output).includes('fixture-'));
});
test('embedded credential text is redacted without changing ordinary numbers', () => {
  const key=['sk','fixture-token-987654321'].join('-');
  const bearer=['Bearer','fixture-bearer-987654321'].join(' ');
  const dsn=['postgresql:','//reader:fixture-pass@localhost/db'].join('');
  const output=safeText(`key=${key} auth=${bearer} connection=${dsn} amount=123.456`);
  assert(!output.includes('fixture-'));assert(output.includes('amount=123.456'));
  assert.equal(safeDiagnostics(123.456),123.456);
});
test('diagnostic arrays, strings, maps and nesting are bounded', () => {
  const bounded=safeDiagnostics({items:Array.from({length:100},(_,i)=>i),text:'x'.repeat(10000)});
  assert.equal(bounded.items.length,21);assert(bounded.text.length<2100);
  let nested={value:'deep'};for(let i=0;i<12;i++)nested={child:nested};
  assert(JSON.stringify(safeDiagnostics(nested)).includes('层级过深'));
  assert.equal(Object.keys(safeDiagnostics(Object.fromEntries(Array.from({length:100},(_,i)=>[`key-${i}`,i])))).length,51);
});
test('export redacts sensitive diagnostics but retains all business rows and precision', () => {
  const table=Array.from({length:35},(_,i)=>({ratio:'0.123456',amount:'12345678901234567890.123456789',count:i}));
  const raw={response:{table,metadata:{nlu:{system_prompt:'fixture-hidden'},note:['Bearer','fixture-export'].join(' ')}}};
  const exported=safeExport(raw);
  assert.equal(exported.response.table.length,35);assert.deepEqual(exported.response.table,table);
  assert.equal(exported.response.metadata.nlu.system_prompt,'[已隐藏]');assert(!JSON.stringify(exported).includes('fixture-export'));
  assert.equal(raw.response.metadata.nlu.system_prompt,'fixture-hidden');
});

test('percentage formatting respects explicit metadata scale', () => {
  assert.equal(displayValue('0.123456', {kind:'percentage', scale:100}), '12.35%');
  assert.equal(displayValue('12.3456', {kind:'percentage', scale:1}), '12.35%');
  assert.equal(displayValue('-0.0001', {kind:'percentage', scale:100}), '-0.01%');
  assert.equal(displayValue('0', {kind:'percentage', scale:100}), '0.00%');
});
test('precise database evidence is not mutated or implicitly scaled', () => {
  const row={amount:'12345678901234567890.123456789', ratio:'0.25'};
  const raw=JSON.stringify(row);
  assert.equal(displayValue(row.amount), row.amount);
  assert.equal(displayValue(row.ratio), '0.25');
  displayValue(row.ratio,{kind:'percentage',scale:100});
  assert.equal(JSON.stringify(row),raw);
});
test('NULL, invalid percentages, and boolean retain semantics', () => {
  assert.equal(displayValue(null,{kind:'percentage',scale:100}), 'NULL（空值）');
  assert.equal(displayValue(true,{kind:'percentage',scale:100}), 'true');
  assert.equal(displayValue('N/A',{kind:'percentage',scale:100}), 'N/A');
  assert.equal(displayValue('0.25',{kind:'percentage',scale:10}), '0.25');
});
test('hybrid targets Chinook and empty docs means registered corpus', () => {
  assert.deepEqual(makeScope('hybrid','adventureworks',''),{route:'hybrid',db_id:'chinook',doc_ids:[]});
  assert.deepEqual(makeScope('hybrid','chinook','manual'),{route:'hybrid',db_id:'chinook',doc_ids:['manual']});
});
test('single document and SQL scopes remain explicit', () => {
  assert.deepEqual(makeScope('doc','chinook','doc-a'),{route:'doc',db_id:null,doc_ids:['doc-a']});
  assert.deepEqual(makeScope('sql','adventureworks','doc-a'),{route:'sql',db_id:'adventureworks',doc_ids:[]});
});
test('readiness requires actual source and model flags', () => {
  const h={status:'ok',llm_configured:true,database_ready:true,aw_database_ready:false};
  const docs=[{doc_id:'doc-a',ready:true}];
  assert.equal(sourceReady('hybrid','adventureworks','',h,docs),true);
  assert.equal(sourceReady('doc','chinook','',h,docs),false);
  assert.equal(sourceReady('sql','adventureworks','',h,docs),false);
  assert.equal(sourceReady('hybrid','chinook','',{...h,database_ready:false},docs),false);
  assert.equal(sourceReady('hybrid','chinook','',{...h,llm_configured:false},docs),false);
  assert.equal(sourceReady('doc','chinook','removed-document',h,docs),false);
  assert.equal(sourceReady('hybrid','chinook','removed-document',h,docs),false);
  assert.equal(sourceReady('doc','chinook','doc-a',h,[{doc_id:'doc-a',ready:false}]),false);
});

test('auto scopes retain the selected real database and optional document range',()=>{
  assert.deepEqual(makeScope('auto','adventureworks',''),{route:'auto',db_id:'adventureworks',doc_ids:[]});
  assert.deepEqual(makeScope('auto','chinook','manual'),{route:'auto',db_id:'chinook',doc_ids:['manual']});
  const health={status:'ok',llm_configured:true,database_ready:true,aw_database_ready:false};
  assert.equal(sourceReady('auto','chinook','',health,[]),true);
  assert.equal(sourceReady('auto','adventureworks','',health,[]),false);
  assert.equal(sourceReady('auto','chinook','removed',health,[]),false);
});
test('full context stays separate and preserves exact source text',()=>{
  const text='  原始会话约定\n'+ '资料'.repeat(3000)+'\n';
  const payload=makeContextRequest('session-a',text);
  assert.equal(payload.text,text);assert.equal(payload.session_id,'session-a');
  assert(!Object.hasOwn(payload,'message'));assert(payload.text.length>4000);
  assert.throws(()=>makeContextRequest('s',' '));
  assert.throws(()=>makeContextRequest('s','a'.repeat(120001)));
});
test('context binding is session and source specific; ordinary payload remains compatible',()=>{
  const scope=makeScope('auto','chinook','');
  const response={session_id:'a',context_id:'context-a',version:1,characters:6000,content_sha256:'a'.repeat(64)};
  const binding=bindContextResponse(response,'a',scope);
  const payload={session_id:'a',message:'本轮问题',scope};
  assert.equal(attachContext(payload,binding).context_id,'context-a');
  assert(!Object.hasOwn(payload,'context_id'));
  assert.deepEqual(attachContext(payload,null),payload);
  assert.throws(()=>attachContext({...payload,session_id:'b'},binding));
  assert.throws(()=>attachContext({...payload,scope:makeScope('sql','chinook','')},binding));
  assert.throws(()=>bindContextResponse({...response,session_id:'b'},'a',scope));
  assert.throws(()=>bindContextResponse({...response,version:null},'a',scope));
  assert.throws(()=>bindContextResponse({...response,content_sha256:''},'a',scope));
});
test('Chinese labels change only visible headers, never raw row keys or values',()=>{
  const row={customer_count:5,amount:'123.4500'},snapshot=JSON.stringify(row);
  assert.equal(columnTitle('customer_count',{customer_count:'客户数量'}),'客户数量');
  assert.equal(columnTitle('amount',{amount:''}),'amount');
  assert.equal(columnTitle('amount',null),'amount');
  assert.equal(JSON.stringify(row),snapshot);
});

test('registered SQL and auto sources require their own verified registry entry',()=>{
  const health={status:'ok',llm_configured:true,database_ready:true,aw_database_ready:true};
  const databases=[{db_id:'local-example',configured:true,catalog_exists:true}];
  assert.equal(sourceReady('sql','local-example','',health,[],databases),true);
  assert.equal(sourceReady('auto','local-example','manual',health,[{doc_id:'manual',ready:true}],databases),true);
  assert.equal(sourceReady('auto','local-example','removed',health,[],databases),false);
  assert.equal(sourceReady('sql','removed-connection','',health,[],databases),false);
  assert.equal(sourceReady('sql','local-example','',health,[],[{...databases[0],configured:false}]),false);
  assert.equal(sourceReady('sql','local-example','',health,[],[{...databases[0],catalog_exists:false}]),false);
  assert.equal(sourceReady('sql','local-example','',{...health,llm_configured:false},[],databases),false);
  assert.equal(databaseReady('chinook',{...health,database_ready:false},[{db_id:'chinook',configured:true,catalog_exists:true}]),false);
  assert.deepEqual(makeScope('sql','local-example','old-doc'),{route:'sql',db_id:'local-example',doc_ids:[]});
});

test('public database projection keeps full table summaries and excludes connection credentials',()=>{
  const tables=Array.from({length:35},(_,index)=>({schema:'public',name:`business_${index}`,column_count:6}));
  const input={db_id:'local-example',name:'业务库',configured:true,catalog_exists:true,builtin:false,password:'fixture-password',dsn:'fixture-dsn',connection:{host:'localhost',user:'fixture-user',password:'fixture-password'},catalog_summary:{table_count:35,column_count:210,tables}};
  const snapshot=JSON.stringify(input),result=publicDatabase(input);
  assert.equal(result.label,'业务库');assert.equal(result.catalog_summary.tables.length,35);
  assert.deepEqual(result.catalog_summary.tables,tables);
  assert(!JSON.stringify(result).includes('fixture-'));
  assert.equal(JSON.stringify(input),snapshot);
  assert.equal(publicDatabase({id:'wrong-contract'}),null);
});

test('database API failures preserve actionable server details while hiding passwords',()=>{
  assert.equal(apiErrorMessage({detail:{code:'CONNECTION_FAILED',message:'无法连接主机，请检查地址和端口。'}},400),'无法连接主机，请检查地址和端口。');
  assert.equal(apiErrorMessage({detail:'连接信息格式无效。'},422),'连接信息格式无效。');
  assert.equal(apiErrorMessage({detail:[{loc:['body','port'],msg:'端口超出范围'}]},422),'body.port: 端口超出范围');
  assert.equal(apiErrorMessage({},503),'请求失败（HTTP 503）');
  assert.equal(databaseErrorMessage(new Error('authentication failed: fixture-password'),'fixture-password'),'authentication failed: [已隐藏密码]');
  const dsn='postgresql://reader:fixture-pass@localhost/db';
  assert(!databaseErrorMessage(new Error(`failed ${dsn}`)).includes('fixture-pass'));
});
