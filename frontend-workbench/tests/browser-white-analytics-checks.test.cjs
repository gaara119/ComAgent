const {test}=require('node:test'),assert=require('node:assert/strict');
const {assertChartSeries,assertBranding,NAV}=require('./browser-white-analytics.cjs');

test('chart check accepts exact positive zero negative values and rejects NULL-to-zero invention',()=>{
 const expected={'北区':'10.25','南区':'0','西区':'-3.5'};
 const rows=Object.entries(expected).map(([label,raw_value])=>({label,raw_value,value:Number(raw_value),rows:1}));
 assert.doesNotThrow(()=>assertChartSeries(rows,expected));
 assert.throws(()=>assertChartSeries([...rows,{label:'空值',raw_value:'0',value:0,rows:1}],expected));
 assert.throws(()=>assertChartSeries(rows.map(x=>x.label==='西区'?{...x,value:3.5}:x),expected));
 assert.throws(()=>assertChartSeries(rows.map(x=>x.label==='北区'?{...x,raw_value:'10.3'}:x),expected));
});
test('chart check rejects missing categories, duplicate identities and nonfinite geometry',()=>{
 const row={label:'甲',raw_value:'1',value:1,rows:1};
 assert.throws(()=>assertChartSeries([],{'甲':'1'}));
 assert.throws(()=>assertChartSeries([row,row],{'甲':'1','乙':'1'}));
 assert.throws(()=>assertChartSeries([{...row,value:Infinity}],{'甲':'1'}));
});
test('branding check rejects old visible brand or C favicon without banning ordinary data text',()=>{
 const snapshot={nav:NAV,navIcons:0,brandIcons:0,icons:['data:,']};
 assert.doesNotThrow(()=>assertBranding(snapshot));
 assert.throws(()=>assertBranding({...snapshot,brandIcons:1}));
 assert.throws(()=>assertBranding({...snapshot,navIcons:1}));
 assert.throws(()=>assertBranding({...snapshot,icons:['data:image/svg+xml,'+encodeURIComponent('<svg><text>C</text></svg>')]}));
 assert.throws(()=>assertBranding({...snapshot,icons:['/ComAgent-logo.png']}));
 assert.throws(()=>assertBranding({...snapshot,nav:[...NAV,'隐藏旧导航']}));
});
