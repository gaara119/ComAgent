/* UI-only source-menu regression. Fixture responses; no model or database calls. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');

async function run(){
 const moduleRoot=process.env.COMAGENT_QA_NODE_MODULES||path.resolve(path.dirname(process.execPath),'..','node_modules');
 let playwright;try{playwright=require('playwright');}catch{playwright=require(path.join(moduleRoot,'playwright'));}
 const output=path.resolve(process.env.COMAGENT_QA_OUTPUT_DIR||path.join(__dirname,'../../eval/artifacts/ui-auto-source-20261018',`browser-${Date.now()}`));
 fs.mkdirSync(output,{recursive:true});assert.equal(fs.readdirSync(output).length,0,'use a fresh evidence directory');
 const dist=path.resolve(__dirname,'../dist'),checks=[],chatRequests=[],errors=[];
 const hint='支持艺术家销售排名→介绍文档，以及指标手册定义→SQL计算。跨源数据库为Chinook。';
 let server,browser,base;
 const json=(res,status,data)=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify(data));};
 const save=(status,error)=>fs.writeFileSync(path.join(output,'browser-auto-source.json'),JSON.stringify({status,fixture_only:true,real_model_calls:0,real_database_queries:0,base,checks,chat_requests:chatRequests,page_errors:errors,error},null,2));
 const checked=name=>{checks.push(name);save('running');};
 try{
  server=http.createServer(async(req,res)=>{
   try{
    const url=new URL(req.url,'http://127.0.0.1');
    if(url.pathname==='/health')return json(res,200,{status:'ok',llm_configured:true,database_ready:true,aw_database_ready:true,ui_test_fixture:true});
    if(url.pathname==='/api/documents')return json(res,200,{documents:[{doc_id:'fixture-artist',title:'Fixture艺术家介绍',ready:true,format:'md'}]});
    if(url.pathname==='/api/databases')return json(res,200,{databases:['chinook','adventureworks'].map(db_id=>({db_id,name:db_id==='chinook'?'Chinook':'AdventureWorks',label:db_id==='chinook'?'Chinook':'AdventureWorks',builtin:true,configured:true,catalog_exists:true}))});
    if(url.pathname==='/api/chat'&&req.method==='POST'){
     let body='';for await(const chunk of req)body+=chunk;chatRequests.push(JSON.parse(body));
     return json(res,200,{status:'SUCCEEDED',answer:'Fixture：已按问题安排跨源步骤。',sql:null,table:[],metadata:{},steps:[],evidences:[],trace_id:'fixture-auto-source'});
    }
    if(url.pathname.startsWith('/api/'))return json(res,404,{detail:'No fixture endpoint'});
    const asset=url.pathname==='/'?'index.html':url.pathname==='/assets/app.js'?'assets/app.js':url.pathname==='/assets/app.css'?'assets/app.css':null;
    if(!asset){res.writeHead(404);return res.end('Not found');}
    res.writeHead(200,{'Content-Type':asset.endsWith('.js')?'text/javascript':asset.endsWith('.css')?'text/css':'text/html; charset=utf-8'});res.end(fs.readFileSync(path.join(dist,asset)));
   }catch(error){errors.push(error.message);json(res,500,{detail:'Fixture error'});}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));base=`http://127.0.0.1:${server.address().port}`;
  browser=await playwright.chromium.launch({headless:true,executablePath:process.env.COMAGENT_QA_CHROME||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  const page=await browser.newPage({viewport:{width:1666,height:1200},deviceScaleFactor:1,reducedMotion:'reduce'});page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);await page.getByText('接口模拟验证',{exact:true}).waitFor();
  async function select(label,text){const box=page.getByRole('combobox',{name:label,exact:true});await box.click();await page.locator('.ant-select-dropdown:visible').getByText(text,{exact:true}).click();}
  await page.getByRole('combobox',{name:'数据来源',exact:true}).click();
  const labels=await page.locator('.ant-select-dropdown:visible .ant-select-item-option-content').allTextContents();
  assert.deepEqual(labels,['自动综合问答','数据库问数','指定文档问答']);assert(!labels.includes('数据库与文档'));
  await page.keyboard.press('Escape');checked('source_selector_contains_only_auto_sql_doc_no_hybrid_option');
  assert.equal(await page.getByText(hint,{exact:true}).count(),0);checked('SQL_mode_hides_cross_source_hint');
  await select('数据来源','自动综合问答');await page.getByText(hint,{exact:true}).waitFor();
  await select('查询文档','Fixture艺术家介绍');await page.getByText('可在问题中直接提出数据库与文档联动需求，系统按问题安排处理步骤。',{exact:true}).waitFor();
  await page.screenshot({path:path.join(output,'auto-source-desktop.png'),fullPage:true,animations:'disabled'});checked('auto_mode_shows_cross_source_hint_and_selected_document');
  const question='销售额最高的艺术家是谁？请结合介绍文档说明其音乐风格。';await page.getByRole('textbox',{name:'你的问题',exact:true}).fill(question);
  const response=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/chat'&&r.request().method()==='POST');await page.getByRole('button',{name:'发送问题',exact:true}).click();await response;
  await page.getByText('Fixture：已按问题安排跨源步骤。',{exact:true}).waitFor();assert.equal(chatRequests.length,1);assert.equal(chatRequests[0].message,question);assert.deepEqual(chatRequests[0].scope,{route:'auto',db_id:'chinook',doc_ids:['fixture-artist']});checked('cross_source_question_sends_auto_and_preserves_selected_database_document_and_original_question');
  await select('数据来源','指定文档问答');assert.equal(await page.getByText(hint,{exact:true}).count(),0);checked('document_mode_hides_cross_source_hint');
  await page.getByRole('navigation',{name:'主导航',exact:true}).getByRole('button',{name:'数据与文档',exact:true}).click();await page.getByRole('heading',{name:'数据与文档',exact:true}).waitFor();await page.getByText('登记文档',{exact:true}).waitFor();checked('top_navigation_data_and_documents_resource_page_remains_available');
  assert.deepEqual(errors,[]);save('PASS');console.log(JSON.stringify({status:'PASS',output,checks,fixture_only:true,real_model_calls:0,real_database_queries:0},null,2));
 }catch(error){save('FAIL',error.stack||error.message);throw error;}
 finally{if(browser)await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}
}
if(require.main===module)run().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
module.exports={run};
