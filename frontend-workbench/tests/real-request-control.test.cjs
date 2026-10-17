const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {collectStartedRequest}=require('./real-request-control.cjs');

function sandbox(t){
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'comagent-stop-'));
 const stop=path.join(directory,'STOP');
 t.after(()=>{
  if(fs.existsSync(stop))fs.unlinkSync(stop);
  fs.rmdirSync(directory);
 });
 return stop;
}

test('preexisting STOP sends no request and invents no response',async t=>{
 const stop=sandbox(t);fs.writeFileSync(stop,'stop');let sent=0,saved=0;
 await assert.rejects(collectStartedRequest(stop,async()=>{sent++;},()=>saved++),{code:'EVALUATION_STOPPED'});
 assert.equal(sent,0);assert.equal(saved,0);
});

for(const status of [200,500])test('STOP during an in-flight '+status+' preserves that actual response and blocks the next send',async t=>{
 const stop=sandbox(t),responses=[];let sent=0,finish;
 const raw={http_status:status,trace_id:'actual-fixture-trace',body:'unchanged'};
 const running=collectStartedRequest(stop,()=>{sent++;return new Promise(resolve=>{finish=resolve;});},response=>responses.push(response));
 fs.writeFileSync(stop,'stop');finish(raw);
 assert.equal(await running,raw);assert.deepEqual(responses,[raw]);
 await assert.rejects(collectStartedRequest(stop,async()=>{sent++;return {};},response=>responses.push(response)),{code:'EVALUATION_STOPPED'});
 assert.equal(sent,1);assert.equal(responses.length,1);
});

test('a transport failure remains an error and never becomes a fabricated response',async t=>{
 const stop=sandbox(t),responses=[];
 await assert.rejects(collectStartedRequest(stop,async()=>{throw new Error('transport failure');},response=>responses.push(response)),/transport failure/);
 assert.deepEqual(responses,[]);
});
