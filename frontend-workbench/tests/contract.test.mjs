import { test } from 'node:test';
import assert from 'node:assert/strict';
import { displayValue, makeScope, sourceReady, safeDiagnostics, safeExport, safeText } from '../src/contract.mjs';

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
