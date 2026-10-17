/* Fixture-only integration QA. Never route this script to a real model backend. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const NAV=['数据概览','数据分析','问答工作台','数据与文档','运行记录'];

function assertChartSeries(series,expected){
 assert(Array.isArray(series),'chart series must be an actual array');
 assert.equal(series.length,Object.keys(expected).length,'missing or invented chart categories');
 assert.equal(new Set(series.map(row=>row.label)).size,series.length,'duplicate chart category identity');
 for(const row of series){
  assert(Object.hasOwn(expected,row.label),`unexpected chart category: ${row.label}`);
  assert.equal(typeof row.raw_value,'string','exact source value must remain available');
  assert.equal(row.raw_value,expected[row.label],`source value changed for ${row.label}`);
  assert.equal(row.value,Number(expected[row.label]),`drawn numeric value changed for ${row.label}`);
  assert(Number.isFinite(row.value));assert(Number.isInteger(row.rows)&&row.rows>0);
 }
}
function assertBranding(snapshot){
 assert.deepEqual(snapshot.nav,NAV,'five accessible text navigation entries must remain available');
 assert.equal(snapshot.navIcons,0,'top navigation must contain text rather than brand/menu icons');
 assert.equal(snapshot.brandIcons,0,'legacy ComAgent brand icon is still rendered');
 for(const href of snapshot.icons){
  let decoded=href;try{decoded=decodeURIComponent(href);}catch{}
  assert(!/comagent/i.test(decoded),'ComAgent favicon remains');
  assert(!/<text\b[^>]*>\s*C\s*<\/text>/i.test(decoded),'legacy C SVG favicon remains');
 }
}

async function run(){
 const modules=process.env.COMAGENT_QA_NODE_MODULES;
 const {chromium}=modules?require(path.join(modules,'playwright')):require('playwright');
 const base=process.env.COMAGENT_QA_UI_URL||'http://127.0.0.1:35171';
 const focus=process.env.COMAGENT_QA_ANALYTICS_FOCUS||null;assert(focus===null||focus==='local-positive','unsupported analytics QA focus');
 assert(['127.0.0.1','localhost','[::1]'].includes(new URL(base).hostname),'fixture UI must use loopback');
 const output=path.resolve(process.env.COMAGENT_QA_OUTPUT_DIR||path.join(__dirname,'../../eval/artifacts/ui-white-integration',`analytics-${Date.now()}-${process.pid}`));
 fs.mkdirSync(output,{recursive:true});assert.equal(fs.readdirSync(output).length,0,'browser evidence directory must be fresh and empty');
 const requests=[],responses=[],checks=[],errors=[],sizes=[];let browser,page;
 const save=(status,error=null)=>fs.writeFileSync(path.join(output,'browser-white-analytics.json'),JSON.stringify({status,fixture_only:true,real_model_calls:0,real_database_queries:0,base,focus,checks,requests,responses,responsive_viewports:sizes,page_errors:errors,error},null,2));
 const checked=name=>{checks.push(name);save('running');};
 try{
  browser=await chromium.launch({headless:true,...(process.env.COMAGENT_QA_CHROME?{executablePath:process.env.COMAGENT_QA_CHROME}:{})});
  page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{const u=new URL(request.url());if(u.pathname==='/health'||u.pathname.startsWith('/api/'))requests.push({method:request.method(),path:u.pathname,...(request.method()==='POST'?{body:request.postDataJSON()}:{})});});
  await page.goto(base);await page.getByText('接口模拟验证',{exact:true}).waitFor();
  const health=await page.request.get(new URL('/health',base).href);assert(health.ok());assert.equal((await health.json()).ui_test_fixture,true,'fixture-only test refuses a real API');
  const nav=page.getByRole('navigation',{name:'主导航'});
  const snapshot=await page.evaluate(()=>{const n=document.querySelector('nav[aria-label="主导航"]');return{nav:[...n.querySelectorAll('button')].map(x=>x.textContent.trim()),navIcons:n.querySelectorAll('img,svg').length,brandIcons:[...document.querySelectorAll('.brand-logo,[data-testid="brand-logo"],img[alt*="ComAgent" i],svg[aria-label*="ComAgent" i]')].filter(x=>x.getClientRects().length).length,icons:[...document.querySelectorAll('link[rel~="icon"]')].map(x=>x.getAttribute('href')||'')};});
  assertBranding(snapshot);assert.equal(await nav.getByRole('button',{name:'数据概览',exact:true}).getAttribute('aria-current'),'page');
  await page.getByTestId('analytics-empty').waitFor();assert.equal(await page.getByTestId('analytics-chart').count(),0,'overview must not fabricate demonstration results');
  checked('default_overview_empty_five_text_navigation_no_legacy_brand_or_favicon');
  if(focus==='local-positive'){
   await nav.getByRole('button',{name:'数据分析',exact:true}).click();await page.waitForLoadState('networkidle');const beforeLocal=requests.length;
   const csv='分类,金额\n北区,20.5\n南区,10\n中区,5.5',expected={'北区':'20.5','南区':'10','中区':'5.5'};
   await page.getByTestId('analytics-csv-input').fill(csv);await page.getByTestId('analytics-run').click();
   await page.getByTestId('analytics-category').selectOption('分类');await page.getByTestId('analytics-method').selectOption('sum');await page.getByTestId('analytics-metric').selectOption('金额');await page.getByTestId('analytics-run').click();
   let chart=page.getByTestId('analytics-chart');await chart.waitFor();assert.equal(await chart.getAttribute('data-source'),'local');assertChartSeries(JSON.parse(await chart.getAttribute('data-series')),expected);
   const rawBefore=await page.getByTestId('analytics-source-table').innerText();const ring=page.getByRole('button',{name:'立体环形图',exact:true});assert(await ring.isEnabled(),'positive multi-category sum must allow ring');await ring.click();assert.equal(await chart.getAttribute('data-chart-type'),'ring');
   let paths=await chart.locator('svg path[d]').evaluateAll(nodes=>nodes.map(node=>node.getAttribute('d')));assert(paths.length>3);assert(paths.every(d=>d&&!/NaN|Infinity|undefined/.test(d)),'ring paths must be finite actual geometry');
   checked('positive_local_CSV_sum_enables_finite_ring_geometry');
   const initialFloor=await chart.locator('svg > path').first().getAttribute('d');await page.getByRole('button',{name:'向右旋转',exact:true}).click();const rotatedFloor=await chart.locator('svg > path').first().getAttribute('d');assert.notEqual(rotatedFloor,initialFloor,'rotation must change actual SVG geometry');
   assertChartSeries(JSON.parse(await chart.getAttribute('data-series')),expected);await page.getByRole('button',{name:'重置图表视角',exact:true}).click();assert.equal(await chart.locator('svg > path').first().getAttribute('d'),initialFloor,'reset must restore actual initial view');
   checked('ring_rotate_and_reset_change_only_geometry_not_source_values');
   for(const [name,type] of [['立体柱状图','bars'],['立体序列图','ribbon']]){await page.getByRole('button',{name,exact:true}).click();assert.equal(await chart.getAttribute('data-chart-type'),type);assertChartSeries(JSON.parse(await chart.getAttribute('data-series')),expected);paths=await chart.locator('svg path[d]').evaluateAll(nodes=>nodes.map(node=>node.getAttribute('d')));assert(paths.every(d=>d&&!/NaN|Infinity|undefined/.test(d)));}
   assert.equal(await page.getByTestId('analytics-csv-input').inputValue(),csv);assert.equal(await page.getByTestId('analytics-source-table').innerText(),rawBefore);assert.equal(requests.length,beforeLocal,'local positive chart interaction must not call API');
   checked('ring_bars_and_ribbon_preserve_exact_local_source_without_API');
   await page.getByRole('button',{name:'查看立体图表 ↗',exact:true}).click();assert.equal(await nav.getByRole('button',{name:'数据概览',exact:true}).getAttribute('aria-current'),'page');chart=page.getByTestId('analytics-chart');await chart.waitFor();assert.equal(await chart.getAttribute('data-source'),'local');await page.getByRole('button',{name:'立体环形图',exact:true}).click();assert.equal(await chart.getAttribute('data-chart-type'),'ring');assertChartSeries(JSON.parse(await chart.getAttribute('data-series')),expected);
   assert.equal(await page.getByTestId('analytics-source-table').innerText(),rawBefore);assert.equal(requests.length,beforeLocal);assert((await page.locator('.analytics-scene-head').innerText()).includes('LOCAL DATA'));
   await page.screenshot({path:path.join(output,'overview-local-positive-ring.png'),fullPage:true});checked('overview_retains_explicit_local_positive_ring_and_original_table');
   assert.deepEqual(errors,[]);assert.equal(responses.length,0);save('PASS');await browser.close();console.log(JSON.stringify({status:'PASS',focus,output,checks,fixture_chat_requests:0,real_model_calls:0,real_database_queries:0},null,2));return;
  }
  for(const name of NAV){await nav.getByRole('button',{name,exact:true}).click();assert.equal(await nav.getByRole('button',{name,exact:true}).getAttribute('aria-current'),'page');}
  await nav.getByRole('button',{name:'问答工作台',exact:true}).click();
  async function ask(message){
   const waiting=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/chat'&&r.request().method()==='POST');
   await page.getByRole('textbox',{name:'你的问题',exact:true}).fill(message);await page.getByRole('button',{name:'发送问题',exact:true}).click();
   const response=await waiting,body=await response.json();assert.equal(response.status(),200);assert.equal(body.trace_id,'controlled-ui-fixture');
   responses.push({message,request:response.request().postDataJSON(),response:body});await page.waitForFunction(()=>!document.querySelector('textarea[aria-label="你的问题"]').disabled);return body;
  }
  const response=await ask('中文表头测试');assert.equal(response.status,'SUCCEEDED');assert.deepEqual(response.table,[{customer_count:5}]);
  await nav.getByRole('button',{name:'数据概览',exact:true}).click();
  let chart=page.getByTestId('analytics-chart');await chart.waitFor();assert.equal(await chart.getAttribute('data-source'),'response');
  let series=JSON.parse(await chart.getAttribute('data-series'));assert.equal(series.length,1);assert.equal(series[0].value,response.table[0].customer_count);assert.equal(series[0].raw_value,'5');assert.equal(series[0].rows,1);assert(await chart.locator('svg').count()>0,'actual SVG geometry missing');
  assert.equal((await page.locator('.analytics-scene-head h2').innerText()).trim(),'客户数量 · 求和','chart heading must consume the returned Chinese business label');
  await page.screenshot({path:path.join(output,'overview-actual-fixture-table.png'),fullPage:true});checked('overview_chart_uses_actual_returned_table_not_demo');
  await nav.getByRole('button',{name:'数据分析',exact:true}).click();await page.waitForLoadState('networkidle');
  const beforeLocal=requests.length;
  const csv='分类,金额,数量\n北区,10.25,2\n南区,0,0\n西区,-3.5,1\n空值,,4';
  await page.getByTestId('analytics-csv-input').fill(csv);await page.getByTestId('analytics-run').click();
  await page.getByTestId('analytics-category').selectOption('分类');await page.getByTestId('analytics-method').selectOption('sum');await page.getByTestId('analytics-metric').selectOption('金额');await page.getByTestId('analytics-run').click();
  chart=page.getByTestId('analytics-chart');await chart.waitFor();assert.equal(await chart.getAttribute('data-source'),'local');
  series=JSON.parse(await chart.getAttribute('data-series'));assertChartSeries(series,{'北区':'10.25','南区':'0','西区':'-3.5'});
  let table=page.getByTestId('analytics-source-table');assert((await table.innerText()).includes('空字符串'));assert((await table.innerText()).includes('-3.5'));
  assert.equal(await page.getByTestId('analytics-csv-input').inputValue(),csv,'local source text changed while aggregating');
  const ring=page.getByRole('button',{name:'立体环形图',exact:true});assert(await ring.isDisabled(),'negative values must not be rendered as a positive composition');
  await page.getByRole('button',{name:'立体柱状图',exact:true}).click();assert.equal(await chart.getAttribute('data-chart-type'),'bars');assertChartSeries(JSON.parse(await chart.getAttribute('data-series')),{'北区':'10.25','南区':'0','西区':'-3.5'});
  await page.getByRole('button',{name:'立体序列图',exact:true}).click();assert.equal(await chart.getAttribute('data-chart-type'),'ribbon');assertChartSeries(JSON.parse(await chart.getAttribute('data-series')),{'北区':'10.25','南区':'0','西区':'-3.5'});
  assert.equal(requests.length,beforeLocal,'local CSV analysis must not make API calls');
  await page.screenshot({path:path.join(output,'local-csv-negative-zero-missing.png'),fullPage:true});checked('local_csv_single_measure_exact_values_zero_negative_missing_no_API');
  const beforeFile=requests.length;
  await page.getByTestId('analytics-file-input').setInputFiles({name:'quoted-local.csv',mimeType:'text/csv',buffer:Buffer.from('分类,金额\n"含,逗号",0\n负数,-2.75\n空值,','utf8')});
  await page.waitForFunction(()=>document.querySelector('[data-testid="analytics-csv-input"]')?.value.includes('含,逗号'));await page.getByTestId('analytics-run').click();
  await page.getByTestId('analytics-category').selectOption('分类');await page.getByTestId('analytics-method').selectOption('sum');await page.getByTestId('analytics-metric').selectOption('金额');await page.getByTestId('analytics-run').click();
  chart=page.getByTestId('analytics-chart');await chart.waitFor();assertChartSeries(JSON.parse(await chart.getAttribute('data-series')),{'含,逗号':'0','负数':'-2.75'});assert.equal(requests.length,beforeFile,'file import must remain local');
  checked('quoted_CSV_file_import_remains_local_and_preserves_negative_zero');
  await page.getByTestId('analytics-file-input').setInputFiles({name:'quoted-empty-row.csv',mimeType:'text/csv',buffer:Buffer.from('值\n""\n0\n-2','utf8')});
  await page.waitForFunction(()=>document.querySelector('[data-testid="analytics-csv-input"]')?.value==='值\n""\n0\n-2');await page.getByTestId('analytics-run').click();
  table=page.getByTestId('analytics-source-table');assert.equal(await table.locator('tbody tr').count(),3,'a quoted empty CSV record must not be silently dropped');assert((await table.innerText()).includes('空字符串'));
  chart=page.getByTestId('analytics-chart');assertChartSeries(JSON.parse(await chart.getAttribute('data-series')),{'0':'0','-2':'-2'});assert.equal(requests.length,beforeFile,'quoted empty local record must not cause API calls');
  checked('quoted_single_column_empty_record_kept_separate_from_zero');
  for(const width of [1440,1024,736,320]){
   await page.setViewportSize({width,height:1000});await page.waitForTimeout(100);
   const size=await page.evaluate(()=>({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth}));assert(size.scroll<=size.width+1,JSON.stringify({viewport:width,...size}));
   assert(await nav.getByRole('button',{name:'问答工作台',exact:true}).isVisible());assert(await page.getByTestId('analytics-run').isVisible());sizes.push({viewport:width,...size});
   await page.screenshot({path:path.join(output,`analytics-${width}px.png`),fullPage:true});
  }
  checked('four_responsive_widths_keep_navigation_chart_table_and_controls_usable');
  await page.setViewportSize({width:1440,height:1000});await nav.getByRole('button',{name:'问答工作台',exact:true}).click();const nullResult=await ask('空值测试');assert.deepEqual(nullResult.table,[{total_amount:null}]);
  await nav.getByRole('button',{name:'数据分析',exact:true}).click();await page.getByRole('button',{name:'加载最近查询表',exact:true}).click();
  table=page.getByTestId('analytics-source-table');await table.waitFor();assert((await table.innerText()).includes('NULL'));
  await page.getByTestId('analytics-method').selectOption('sum');await page.getByTestId('analytics-metric').selectOption('total_amount');await page.getByTestId('analytics-run').click();
  await page.getByTestId('analytics-error').waitFor();assert((await page.getByTestId('analytics-error').innerText()).includes('空值'));
  assert.equal(await page.getByTestId('analytics-chart').count(),0,'all-NULL response must not become a zero-valued chart');
  checked('actual_returned_NULL_remains_NULL_without_zero_chart');
  assert.deepEqual(errors,[]);save('PASS');await browser.close();console.log(JSON.stringify({status:'PASS',output,checks,fixture_chat_requests:responses.length,real_model_calls:0,real_database_queries:0},null,2));
 }catch(error){save('FAIL',String(error.stack||error));if(page)await page.screenshot({path:path.join(output,'failure.png'),fullPage:true}).catch(()=>{});if(browser)await browser.close();throw error;}
}
module.exports={assertChartSeries,assertBranding,NAV};
if(require.main===module)run().catch(error=>{console.error(error);process.exitCode=1;});
