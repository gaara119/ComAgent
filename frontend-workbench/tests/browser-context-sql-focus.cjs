/* Pure assertions for the opt-in, two-chat actual context -> SQL recheck. */
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const FOCUS='context-sql';
const CONTEXT_QUESTION='这份会话正文中的重点市场包含哪些国家？请只依据这份正文回答。';
const SQL_QUESTION='咱们主期间内，重点市场的发票销售额一共是多少？';
const BRIEF_SHA='0fd3caafd6ce11bf7dd66ed1ce7ccb06814fbedcb74e20292eda8981a0875c0d';
const MARKETS=['USA','Canada','Brazil','France','Germany','United Kingdom'];

function assertFocusBrief(brief){
 assert.equal(Array.from(brief).length,5846,'the original complete B user brief is required');
 assert.equal(crypto.createHash('sha256').update(brief,'utf8').digest('hex'),BRIEF_SHA,'original full user brief SHA mismatch');
}

function businessLabels(response){
 assert(Array.isArray(response.table)&&response.table.length,'actual SQL rows required, no reconstructed result');
 const columns=response.metadata?.result_columns||Object.keys(response.table[0]);
 assert(Array.isArray(columns)&&columns.length&&new Set(columns).size===columns.length);
 assert(response.table.every(row=>row&&typeof row==='object'&&!Array.isArray(row)&&Object.keys(row).length===columns.length&&columns.every(key=>Object.hasOwn(row,key))));
 const labels=columns.map(column=>response.metadata?.column_labels?.[column]||column);
 for(const label of labels){
  assert(typeof label==='string'&&/\p{Script=Han}/u.test(label),'actual displayed headers must use Chinese business names');
  assert(!/[A-Za-z_][A-Za-z0-9_]*\s*\(/.test(label),'display header leaks SQL function syntax: '+label);
  assert(!/::|\b(?:SELECT|FROM|WHERE|GROUP\s+BY|ORDER\s+BY|CASE\s+WHEN)\b|\b[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\b|\b[A-Za-z]+_[A-Za-z0-9_]+\b/i.test(label),'display header leaks SQL identifiers or syntax: '+label);
 }
 assert.equal(new Set(labels).size,labels.length,'actual projected business headers must be distinguishable');
 return labels;
}

function assertContextSQL(record,saved,brief){
 assertFocusBrief(brief);
 assert.equal(record.name,'long-brief-sql');assert.equal(record.request.message,SQL_QUESTION);
 assert.equal(record.request.context_id,saved.context_id);assert.equal(record.request.session_id,saved.session_id);
 assert.equal(record.request.scope.route,'auto');assert.equal(record.request.scope.db_id,'chinook');
 const response=record.response,contract=response.metadata?.clarify?.semantic_contract;
 assert.equal(record.http_status,200);assert.equal(response.status,'SUCCEEDED');assert(response.trace_id&&response.sql);
 assert(response.steps?.some(step=>step.name==='sql_exec'&&step.status==='ok'),'real successful SQL execution trace required');
 const context=response.metadata?.session_context;
 assert.equal(context?.context_id,saved.context_id);assert.equal(context.content_sha256,BRIEF_SHA);assert.equal(context.characters,5846);
 assert.equal(contract?.metric,'invoice_revenue');
 for(const candidate of [contract,response.intent]){
  assert.equal(candidate.time_scope.current.start,'2025-01-01');assert.equal(candidate.time_scope.current.end,'2026-01-01');
  const filters=candidate.filters.filter(item=>(item.column||item.field)==='invoice.billing_country');assert.equal(filters.length,1);
  const filter=filters[0];if(filter.column&&filter.field)assert.equal(filter.column,filter.field);
  assert.equal(filter.operator.toUpperCase(),'IN');assert(Array.isArray(filter.value));
  assert.deepEqual([...filter.value].sort(),[...MARKETS].sort(),'all and only the six user-brief markets are required');
 }
 return businessLabels(response);
}

module.exports={FOCUS,CONTEXT_QUESTION,SQL_QUESTION,BRIEF_SHA,assertFocusBrief,businessLabels,assertContextSQL};
