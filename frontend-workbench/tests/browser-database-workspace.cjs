/* Self-contained local browser QA. All APIs below are fixtures; no real model or database is contacted. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto'),assert=require('node:assert/strict');

async function run(){
 const runtimeModules=process.env.COMAGENT_QA_NODE_MODULES||path.resolve(path.dirname(process.execPath),'..','node_modules');
 let playwright;try{playwright=require('playwright');}catch{playwright=require(path.join(runtimeModules,'playwright'));}
 const output=path.resolve(process.env.COMAGENT_QA_OUTPUT_DIR||path.join(__dirname,'../../eval/artifacts/ui-database-workspace',`${Date.now()}-${process.pid}`));
 fs.mkdirSync(output,{recursive:true});assert.equal(fs.readdirSync(output).length,0,'evidence directory must be fresh and empty');
 const dist=path.resolve(__dirname,'../dist'),checks=[],requests=[],pageErrors=[],mockChats=[],savedContexts=[];
 const catalog={table_count:1,column_count:2,foreign_key_count:0,schemas:['public'],tables:[{schema:'public',name:'customer',column_count:2,estimated_row_count:7}],date_ranges:[],sample_values_included:false};
 const builtins=[{db_id:'chinook',name:'Chinook',label:'Chinook',builtin:true,configured:true,catalog_exists:true,catalog_summary:catalog},{db_id:'adventureworks',name:'AdventureWorks',label:'AdventureWorks',builtin:true,configured:true,catalog_exists:true,catalog_summary:catalog}];
 const added={db_id:'pg-fixture-business',name:'Fixture业务库',label:'Fixture业务库',builtin:false,configured:true,catalog_exists:true,catalog_summary:catalog};
 let registered=[],addMode='failure',addRequests=0,browser,server,base;
 const summary=(status,error=null)=>fs.writeFileSync(path.join(output,'browser-database-workspace.json'),JSON.stringify({status,fixture_only:true,real_model_calls:0,real_database_queries:0,base,checks,requests,mock_chat_requests:mockChats.length,mock_database_add_requests:addRequests,page_errors:pageErrors,error},null,2));
 const checked=name=>{checks.push(name);summary('running');};
 const json=(response,status,data)=>{response.writeHead(status,{'Content-Type':'application/json; charset=utf-8'});response.end(JSON.stringify(data));};
 const readBody=async request=>{let body='';for await(const chunk of request)body+=chunk;return body?JSON.parse(body):{};};
 try{
  server=http.createServer(async(request,response)=>{
   try{
    const pathname=new URL(request.url,'http://127.0.0.1').pathname;
    if(pathname==='/health')return json(response,200,{status:'ok',llm_configured:true,database_ready:true,aw_database_ready:true,ui_test_fixture:true});
    if(pathname==='/api/documents')return json(response,200,{documents:[{doc_id:'fixture-manual',title:'Fixture文档',ready:true,format:'md'}]});
    if(pathname==='/api/databases'&&request.method==='GET')return json(response,200,{databases:[...builtins,...registered]});
    if(pathname==='/api/context'&&request.method==='POST'){
     const body=await readBody(request);savedContexts.push(body);
     requests.push({method:'POST',path:pathname,session_id:body.session_id,characters:body.text.length});
     return json(response,200,{session_id:body.session_id,context_id:`fixture-context-${savedContexts.length}`,version:1,characters:body.text.length,content_sha256:crypto.createHash('sha256').update(body.text).digest('hex')});
    }
    if(pathname==='/api/chat'&&request.method==='POST'){
     const body=await readBody(request);mockChats.push(body);requests.push({method:'POST',path:pathname,...body});
     return json(response,200,{status:'SUCCEEDED',answer:mockChats.length===1?'Fixture旧会话答复':'Fixture新会话答复',sql:'SELECT COUNT(*) AS customer_count FROM public.customer',table:[{customer_count:7}],metadata:{result_columns:['customer_count'],column_labels:{customer_count:'客户数量'}},steps:[],evidences:[],trace_id:'fixture-only-browser'});
    }
    if(pathname==='/api/databases'&&request.method==='POST'){
     const body=await readBody(request);addRequests++;requests.push({method:'POST',path:pathname,name:body.name,host:body.host,port:body.port,database:body.database,user:body.user,sslmode:body.sslmode,schemas:body.schemas,password_present:Boolean(body.password)});
     await new Promise(resolve=>setTimeout(resolve,250));
     if(addMode==='failure')return json(response,400,{detail:{code:'CONNECTION_FAILED',message:'无法连接测试主机，请检查地址和端口。'}});
     assert.deepEqual(body.schemas,['public','analytics']);registered=[added];return json(response,201,added);
    }
    if(pathname.startsWith('/api/'))return json(response,404,{detail:'此纯 fixture 服务没有该接口。'});
    const asset=pathname==='/'?'index.html':pathname==='/assets/app.js'?'assets/app.js':pathname==='/assets/app.css'?'assets/app.css':null;
    if(!asset){response.writeHead(404);return response.end('Not found');}
    response.writeHead(200,{'Content-Type':asset.endsWith('.js')?'text/javascript':asset.endsWith('.css')?'text/css':'text/html; charset=utf-8'});response.end(fs.readFileSync(path.join(dist,asset)));
   }catch(error){json(response,500,{detail:'Fixture server error'});pageErrors.push(error.message);}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));base=`http://127.0.0.1:${server.address().port}`;
  browser=await playwright.chromium.launch({headless:true,executablePath:process.env.COMAGENT_QA_CHROME||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,reducedMotion:'reduce'});page.on('pageerror',error=>pageErrors.push(error.message));
  await page.goto(base);await page.getByText('接口模拟验证',{exact:true}).waitFor();
  assert.equal(await page.getByRole('heading',{name:'问答工作台',exact:true}).count(),1);
  assert.equal(await page.locator('aside,.sidebar').count(),0,'sidebar DOM must be removed');
  assert.equal(await page.locator('.proof-card').count(),0,'empty workbench must not reserve an evidence panel');
  async function assertNoOverflow(name){const size=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth}));assert(size.document<=size.viewport+1,`${name}: page overflows ${JSON.stringify(size)}`);assert(size.body<=size.viewport+1,`${name}: body overflows ${JSON.stringify(size)}`);}
  await assertNoOverflow('mobile workbench');await page.screenshot({path:path.join(output,'mobile-390-workbench.png'),fullPage:true,animations:'disabled'});checked('mobile_390_workspace_no_horizontal_overflow_sidebar_removed_no_empty_proof');
  await page.getByRole('textbox',{name:'本会话正文',exact:true}).fill('仅旧会话有效的 Fixture 资料。');
  await page.getByRole('button',{name:'保存资料',exact:true}).click();await page.getByText('资料已绑定当前会话',{exact:true}).waitFor();
  const oldSession=savedContexts.at(-1).session_id;
  async function askFixture(text){await page.getByRole('textbox',{name:'你的问题',exact:true}).fill(text);const response=page.waitForResponse(item=>new URL(item.url()).pathname==='/api/chat'&&item.request().method()==='POST');await page.getByRole('button',{name:'发送问题',exact:true}).click();await response;await page.waitForFunction(()=>!document.querySelector('#workspace-question').disabled);}
  await askFixture('旧会话 Fixture 问题');assert.equal(mockChats[0].session_id,oldSession);assert.equal(mockChats[0].context_id,'fixture-context-1');await page.getByText('Fixture旧会话答复',{exact:true}).waitFor();
  checked('fixture_context_and_old_query_are_bound_before_database_switch');
  await page.getByRole('button',{name:'＋ 添加数据库',exact:true}).click();const dialog=page.getByRole('dialog');await dialog.waitFor();
  const password=dialog.getByLabel('密码',{exact:true});await password.fill('fixture-password-clear-check');
  assert.equal(await password.getAttribute('type'),'password');await dialog.locator('button.ant-modal-close').click();await dialog.waitFor({state:'hidden'});
  await page.getByRole('button',{name:'＋ 添加数据库',exact:true}).click();await dialog.waitFor();assert.equal(await dialog.getByLabel('密码',{exact:true}).inputValue(),'');
  checked('modal_password_is_masked_and_cleared_after_close_and_reopen');
  await assertNoOverflow('mobile modal');await page.screenshot({path:path.join(output,'mobile-390-database-modal.png'),fullPage:true,animations:'disabled'});checked('mobile_390_modal_no_page_horizontal_overflow');
  async function fillDatabase(){await dialog.getByLabel('连接名称',{exact:true}).fill('Fixture业务库');await dialog.getByLabel('主机地址',{exact:true}).fill('fixture.invalid');await dialog.getByLabel('数据库名称',{exact:true}).fill('business');await dialog.getByLabel('用户名',{exact:true}).fill('readonly_fixture');await dialog.getByLabel('密码',{exact:true}).fill('fixture-password-not-real');await dialog.getByLabel('Schema 范围',{exact:true}).fill('public, analytics');}
  await fillDatabase();const submit=dialog.getByRole('button',{name:'验证并添加数据库',exact:true});await submit.evaluate(button=>{button.click();button.click();});
  await page.getByText('无法连接测试主机，请检查地址和端口。',{exact:true}).waitFor();assert.equal(addRequests,1,'duplicate clicks must not register twice');assert(await submit.isEnabled());assert.equal(await dialog.getByLabel('密码',{exact:true}).inputValue(),'fixture-password-not-real');
  await page.screenshot({path:path.join(output,'mobile-390-database-failure.png'),fullPage:true,animations:'disabled'});checked('database_failure_shows_backend_detail_message_duplicate_submit_blocked_retry_available');
  addMode='success';await submit.click();await dialog.waitFor({state:'hidden'});await page.locator('.source-bar').getByText('Fixture业务库',{exact:true}).waitFor();
  assert.equal(await page.getByRole('textbox',{name:'本会话正文',exact:true}).inputValue(),'');assert.equal(await page.getByRole('textbox',{name:'你的问题',exact:true}).inputValue(),'');assert.equal(await page.getByText('资料已绑定当前会话',{exact:true}).count(),0);assert.equal(await page.getByText('Fixture旧会话答复',{exact:true}).count(),0);assert.equal(await page.locator('.proof-card').count(),0);
  await assertNoOverflow('mobile selected custom database');await page.screenshot({path:path.join(output,'mobile-390-custom-selected-cleared.png'),fullPage:true,animations:'disabled'});checked('successful_database_registration_selects_custom_SQL_source_and_clears_old_context_history_question');
  await askFixture('新连接 Fixture 问题');const current=mockChats.at(-1);assert.notEqual(current.session_id,oldSession);assert(!Object.hasOwn(current,'context_id'),'new database query must not send old context');assert.deepEqual(current.scope,{route:'sql',db_id:'pg-fixture-business',doc_ids:[]});
  checked('next_fixture_query_uses_new_session_custom_database_and_no_old_context');
  await page.getByRole('button',{name:'＋ 添加数据库',exact:true}).click();await dialog.waitFor();assert.equal(await dialog.getByLabel('密码',{exact:true}).inputValue(),'');
  assert.equal(await dialog.getByRole('button',{name:'刷新结构',exact:true}).count(),1,'only registered connection can refresh');assert.equal(await dialog.getByRole('button',{name:/^移\s*除$/}).count(),1,'built-in connections cannot be removed');
  const storage=await page.evaluate(()=>({local:{...localStorage},session:{...sessionStorage}}));assert(!JSON.stringify(storage).includes('fixture-password'));checked('successful_add_clears_password_browser_storage_has_no_password_builtin_actions_not_exposed');
  assert.deepEqual(pageErrors,[]);assert.equal(addRequests,2);assert.equal(mockChats.length,2);summary('PASS');console.log(JSON.stringify({status:'PASS',output,checks,fixture_only:true,real_model_calls:0,real_database_queries:0},null,2));
 }catch(error){summary('FAIL',error.stack||error.message);throw error;}
 finally{if(browser)await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}
}

if(require.main===module)run().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
module.exports={run};
