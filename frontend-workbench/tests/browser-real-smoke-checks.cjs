/* Offline-testable assertions and real-DOM virtual option selection. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const atomicOutputId=value=>typeof value==='string'&&/^[A-Za-z][A-Za-z0-9_.:-]*$/.test(value);
const uuid=value=>typeof value==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
function semanticContract(record){return record.response?.metadata?.clarify?.semantic_contract;}
function atomicIds(requirements){
 assert(Array.isArray(requirements)&&requirements.every(x=>typeof x==='string'),'output requirements must remain a string array');
 return requirements.filter(atomicOutputId);
}
function readProviderOutputEvidence(record,root){
 const response=record.response,ids=new Set(),actualUserSources=[record.request?.message];
 assert(uuid(response?.trace_id),'actual response trace ID required');
 const captureRoot=fs.realpathSync(path.resolve(root,'.runtime/agent-improvement-20261016/provider'));
 for(const step of response.steps||[]){
  const summary=step.output_summary||{};
  if(summary.json_valid!==true)continue;
  assert.equal(step.status,'ok','only a successfully validated provider reply may prove model output IDs');
  const reference=summary.provider_capture;
  assert(typeof reference==='string'&&!path.isAbsolute(reference),'trace-linked provider path required');
  const resolved=fs.realpathSync(path.resolve(root,reference)),relative=path.relative(captureRoot,resolved);
  assert(relative&&!relative.startsWith('..')&&!path.isAbsolute(relative),'provider path must stay in actual project capture root');
  assert(/^[0-9a-f]{32}\.json$/i.test(path.basename(resolved)),'physical provider UUID filename required');
  const capture=JSON.parse(fs.readFileSync(resolved,'utf8'));
  assert(!capture.mock&&!capture.test_generated&&!capture.test_only,'mock captures cannot prove an actual browser reply');
  assert.equal(capture.trace_id,response.trace_id,'provider belongs to this actual response trace');
  assert(uuid(capture.response?.id),'actual provider response ID required');
  assert.equal(capture.request?.model,summary.model);assert.equal(capture.response.model,summary.model);
  assert.deepEqual(capture.response.usage,summary.usage,'trace usage must match original provider response');
  const content=capture.response.choices?.[0]?.message?.content;assert(typeof content==='string');
  const parsed=JSON.parse(content);
  if(parsed.output_requirements!==undefined)for(const id of atomicIds(parsed.output_requirements))ids.add(id);
  for(const message of capture.request.messages||[]){
   if(message.role!=='user')continue;
   let payload;try{payload=JSON.parse(message.content);}catch{continue;}
   const context=payload.runtime_context||payload.request_context;
   if(!context)continue;
   if(context.current_user_message!==undefined)assert.equal(context.current_user_message,record.request.message);
   actualUserSources.push(context.user_brief,context.current_user_message);
   for(const turn of context.actual_conversation||[])actualUserSources.push(turn.user);
  }
 }
 return {ids,actualUserSources};
}
function assertProviderAtomicOutputs(record,root){
 const contract=semanticContract(record),{ids,actualUserSources}=readProviderOutputEvidence(record,root);
 if(ids.size){
  const present=new Set(atomicIds(contract?.output_requirements));
  for(const id of ids)assert(present.has(id),'complete actual model output ID lost or partially rewritten: '+id);
 }
 const scope=contract?.query_scope||{};
 if(scope.requested_percent_decimals!==undefined){
  const source=scope.percent_precision_source;
  assert(Number.isInteger(scope.requested_percent_decimals)&&scope.requested_percent_decimals>=0&&scope.requested_percent_decimals<=9);
  assert.equal(source?.source,'program:explicit_percent_precision','precision requires actual program source');
  assert(typeof source.evidence==='string'&&source.evidence&&!atomicOutputId(source.evidence),'an opaque output ID cannot authorize precision');
  assert(actualUserSources.some(text=>typeof text==='string'&&text.includes(source.evidence)),'precision source must quote actual user text, not model output IDs');
 }
 return [...ids];
}
function assertRankOnlyOutputPreservation(record,previous,root){
 assert.equal(record.request.session_id,previous.request.session_id);
 const card=previous.response.metadata?.clarify?.switch;
 assert(card&&record.request.clarification_id===card.clarification_id&&record.request.intent_version===card.intent_version,'actual current trusted card/version required');
 assert(card.options?.some(option=>option.id===record.request.choice_id),'actual offered choice required');
 const prior=semanticContract(previous),current=semanticContract(record),present=new Set(atomicIds(current?.output_requirements));
 for(const id of atomicIds(prior?.output_requirements))assert(present.has(id),'rank-only choice must preserve unrelated complete output obligation: '+id);
 // A corrupt prior public state cannot redefine the original model's whole
 // output ID and mask the same corruption in the trusted followup.
 for(const id of readProviderOutputEvidence(previous,root).ids)assert(present.has(id),'rank-only choice lost original actual model output obligation: '+id);
}
function assertSavedSemanticContract(state,record){
 assert.equal(state.session_id,record.request.session_id);assert.equal(state.intent.intent_version,record.response.intent.intent_version);
 assert.deepEqual(state.analysis,semanticContract(record),'actual saved analysis must equal the complete returned semantic contract');
}
function countryBindings(response){
 const semantic=response.metadata?.clarify?.semantic_contract;
 return [semantic?.filters||[],response.intent?.filters||[]].flat().filter(x=>['customer.country','invoice.billing_country'].includes(x.column));
}
function assertRegionChoice(record,previous){
 const response=record.response,contract=response.metadata?.clarify?.semantic_contract;
 const bindings=countryBindings(response);assert(bindings.length,'confirmed country binding required');
 for(const binding of bindings){
  assert.equal(binding.column,contract.region_scope);
  assert.equal(binding.value,'France');
  assert.equal(binding.field_owner_proof?.column,binding.column,'old field cannot prove migrated owner');
  assert.equal(binding.field_owner_proof?.source,'program:trusted_region_choice');
  assert.equal(binding.field_owner_proof?.choice_id,record.request.choice_id);
  assert.equal(binding.field_owner_proof?.clarification_id,record.request.clarification_id);
  assert.equal(binding.source,'explicit_user_choice');
  assert.equal(binding.value_index_revalidated,false);
  assert.notEqual(binding.evidence_ref,countryBindings(previous.response)[0]?.evidence_ref);
  assert.equal(binding.value_origin?.evidence_ref,countryBindings(previous.response)[0]?.evidence_ref);
  assert.equal(binding.value_origin?.role,'value_only_not_current_field_authorization');
 }
}
function assertRegionFollowup(record,previous){
 const current=countryBindings(record.response),prior=countryBindings(previous.response);assert(current.length);
 for(const binding of current){
  assert.equal(binding.column,'customer.country');assert.equal(binding.value,'France');
  assert.deepEqual(binding.field_owner_proof,prior[0].field_owner_proof,'year edit preserves actual country authorization');
  assert.equal(binding.source,'explicit_user_choice');assert.equal(binding.value_index_revalidated,false);
 }
}
function assertContextOnly(record,saved,brief){
 const response=record.response;
 assert(!response.sql,'context-only must not execute SQL');
 assert(!response.table||response.table.length===0,'context-only must not answer with DB rows');
 assert.deepEqual(response.evidences||[],[],'context quotes must not forge document evidence');
 assert(!/\[E\d+\]/.test(response.answer),'context-only must not invent E citations');
 assert.equal(response.metadata?.source_scope,'context');
 const outputs=Object.values(response.metadata?.fusion?.actual_outputs||{});assert(outputs.length);
 for(const output of outputs){
  assert.equal(output.source,'user_session_context');assert.equal(output.context_id,saved.context_id);
  assert.equal(output.sha256,saved.content_sha256);assert(output.quotes?.length);
  for(const quote of output.quotes){
   assert(Number.isInteger(quote.char_start)&&quote.char_start>=0);assert(quote.text?.length);
   assert.equal(Array.from(brief).slice(quote.char_start,quote.char_start+Array.from(quote.text).length).join(''),quote.text);
  }
 }
 for(const step of response.steps||[]){
  assert(!/(?:sql_(?:execut|generat|validat)|execute_sql|load_catalog|catalog_lookup)/i.test(step.name),'no SQL/catalog tool permitted');
 }
}
async function chooseVisibleVirtualOption(page,label,combobox=null){
 let dropdown;
 const controls=combobox?await combobox.getAttribute('aria-controls'):null;
 if(controls){
  assert(/^[A-Za-z0-9_:-]+$/.test(controls),'bounded actual combobox controls ID');
  dropdown=page.locator('[id="'+controls+'"]').locator('xpath=ancestor::*[contains(concat(" ",normalize-space(@class)," ")," ant-select-dropdown ")][1]');
 }else dropdown=page.locator('.ant-select-dropdown:visible').last();
 await dropdown.waitFor({state:'visible'});
 const holder=dropdown.locator('.rc-virtual-list-holder, .ant-select-dropdown-list-holder').first();
 if(await holder.count())await holder.evaluate(el=>{el.scrollTop=0;});
 for(let attempt=0;attempt<200;attempt++){
  const option=dropdown.getByText(label,{exact:true}).last();
  if(await option.count()){await option.click();return;}
  assert(await holder.count(),'target option not found in nonvirtual list');
  const moved=await holder.evaluate(el=>{const before=el.scrollTop;el.scrollTop+=Math.max(64,el.clientHeight-24);return el.scrollTop>before;});
  await page.waitForTimeout(45);
  if(!moved){
   const last=dropdown.getByText(label,{exact:true}).last();if(await last.count()){await last.click();return;}
   throw new Error('Document option not present in the real dropdown: '+label);
  }
 }
 throw new Error('Virtual document list exceeded bounded scrolling attempts');
}
function assertLocalOperandPatch(record,previous){
 const contract=record.response.metadata?.clarify?.semantic_contract,prior=previous.response.metadata?.clarify?.semantic_contract;
 assert.equal(contract?.condition_sources?.numerator?.applies_to,'numerator','numerator authorization cannot claim global scope');
 assert.equal(contract.condition_sources.numerator.evidence,record.request.message);
 assert.equal(contract.condition_sources.denominator?.applies_to,'denominator');
 assert.deepEqual(contract.denominator,prior.denominator,'inner ranking switch preserves denominator');
 assert.deepEqual(contract.query_scope.denominator,prior.query_scope.denominator,'typed denominator stays unchanged');
 assert.deepEqual(contract.condition_sources.denominator,prior.condition_sources.denominator,'denominator source stays unchanged');
}
function assertLocalOperandLedger(ledger,record){
 assert.equal(ledger.intent.intent_version,record.response.intent.intent_version,'read exact actual post-choice state');
 assert.equal(ledger.analysis.condition_sources.numerator.applies_to,'numerator');
 const active=ledger.constraint_ledger.filter(x=>x.status==='active'&&x.field==='numerator');
 assert.equal(active.length,1);assert.equal(active[0].intent_version,ledger.intent.intent_version);
 assert.equal(active[0].applies_to,'numerator');
 assert.equal(active[0].value,record.response.metadata.clarify.semantic_contract.numerator);
 for(const entry of ledger.constraint_ledger.filter(x=>x.status==='active'&&x.field==='denominator'))assert.equal(entry.applies_to,'denominator');
}
module.exports={assertRegionChoice,assertRegionFollowup,assertContextOnly,chooseVisibleVirtualOption,assertLocalOperandPatch,assertLocalOperandLedger,atomicOutputId,assertProviderAtomicOutputs,assertRankOnlyOutputPreservation,assertSavedSemanticContract};
