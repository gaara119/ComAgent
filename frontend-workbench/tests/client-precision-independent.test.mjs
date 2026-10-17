/** Pure Node checks against the real display contract; no browser or HTTP. */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import {existsSync} from 'node:fs';
import {fileURLToPath,pathToFileURL} from 'node:url';

const modulePath = process.env.COMAGENT_DISPLAY_CONTRACT || [
  new URL('../src/contract.mjs',import.meta.url),
  new URL('../../frontend-workbench/src/contract.mjs',import.meta.url),
].map(fileURLToPath).find(existsSync) || path.resolve('frontend-workbench/src/contract.mjs');
const {displayValue, safeExport} = await import(pathToFileURL(modulePath).href);
const rule = (kind, digits, extra={}) => ({kind,digits,rounding:'half_even',source:'actual_sql_projection',raw_values_preserved:true,...(kind==='percentage'?{scale:100}:{}),...extra});

const exactCases = [
  ['percent zero places','0.125','12%',rule('percentage',0)],
  ['percent one place','0.12345','12.3%',rule('percentage',1)],
  ['percent three places','0.1234567','12.346%',rule('percentage',3)],
  ['percent nine places','0.1234567891234','12.345678912%',rule('percentage',9)],
  ['already scaled three places','12.34567','12.346%',rule('percentage',3,{scale:1})],
  ['percent raw fraction','0.12345','12.34500%',rule('percentage',null)],
  ['percent raw already scaled','12.345','12.345%',rule('percentage',null,{scale:1})],
  ['percent revoked precision remains raw','0.123456','12.345600%',rule('percentage',null)],
  ['percent negative','-0.12345','-12.345%',rule('percentage',3)],
  ['percent zero','0','0.000%',rule('percentage',3)],
  ['percent even tie down','0.00125','0.12%',rule('percentage',2)],
  ['percent odd tie up','0.00135','0.14%',rule('percentage',2)],
  ['percent exact long decimal','12345678901234567890.123456789','1234567890123456789012.345678900%',rule('percentage',9)],
  ['money zero places','12.5','12',rule('money',0)],
  ['money one place','12.345','12.3',rule('money',1)],
  ['money three places','12.34567','12.346',rule('money',3)],
  ['money nine places','12.12345678945','12.123456789',rule('money',9)],
  ['money raw','12.34567','12.34567',rule('money',null)],
  ['money revoked precision remains raw','12.345678','12.345678',rule('money',null)],
  ['money negative','-12.345','-12.34',rule('money',2)],
  ['money even tie down','0.125','0.12',rule('money',2)],
  ['money odd tie up','0.135','0.14',rule('money',2)],
  ['money exact long decimal','12345678901234567890.123456789','12345678901234567890.123456789',rule('money',9)],
  ['money explicit unit scale','12.345','12.34',rule('money',2,{scale:1})],
  ['count does not become money','2','2',rule('count',null)],
  ['count decimal integer string','2.000','2',rule('count',null)],
  ['count noninteger stays actual raw','2.5','2.5',rule('count',null)],
];
for (const [name,value,expected,format] of exactCases) {
  test(name,()=>assert.equal(displayValue(value,format),expected));
}

for (const digits of [-1,10,1.5,true,'1',{},NaN,Infinity]) {
  test(`invalid digits ${JSON.stringify(digits)} cannot authorize rounding`,()=> {
    assert.equal(displayValue('0.123456',rule('percentage',digits)),'0.123456');
    assert.equal(displayValue('12.3456',rule('money',digits)),'12.3456');
  });
}
for (const source of ['model','unknown',null,undefined]) {
  test(`untrusted explicit precision source ${source} stays raw`,()=> {
    assert.equal(displayValue('0.123456',rule('percentage',1,{source})),'0.123456');
    assert.equal(displayValue('12.3456',rule('money',1,{source})),'12.3456');
  });
}
for (const rounding of ['half_up','unknown',true,null]) {
  test(`new explicit precision with unsupported rounding ${rounding} stays raw`,()=> {
    assert.equal(displayValue('0.123456',rule('percentage',1,{rounding})),'0.123456');
    assert.equal(displayValue('12.3456',rule('money',1,{rounding})),'12.3456');
  });
}
for (const scale of [true,false,2,'100',null]) {
  test(`invalid percent scale ${JSON.stringify(scale)} stays raw`,()=>
    assert.equal(displayValue('0.123456',rule('percentage',1,{scale})),'0.123456'));
}
test('money cannot acquire a percentage or arbitrary multiplier',()=> {
  for(const scale of [100,true,'1',2]) assert.equal(displayValue('12.3456',rule('money',1,{scale})),'12.3456');
});
test('legacy percentage without digits preserves two decimal places',()=> {
  // Existing React behavior was half-up; only new explicit rules unify half-even.
  assert.equal(displayValue('0.12345',{kind:'percentage',scale:100}),'12.35%');
  assert.equal(displayValue('12.345',{kind:'percentage',scale:1,source:'sql_projection'}),'12.35%');
});
test('boolean and nonnumeric evidence are never converted to decimal',()=> {
  assert.equal(displayValue(true,rule('percentage',2)),'true');
  assert.equal(displayValue(false,rule('money',2)),'false');
  assert.equal(displayValue('not a number',rule('money',2)),'not a number');
  assert.equal(displayValue(null,rule('percentage',2)),'NULL（空值）');
});
test('display and export leave raw rows and precise numeric strings intact',()=> {
  const original={table:[{amount:'12345678901234567890.123456789',ratio:'0.1234567891234',flag:true,missing:null}],metadata:{result_format:{ratio:rule('percentage',3)}}};
  const before=JSON.stringify(original);
  displayValue(original.table[0].ratio,original.metadata.result_format.ratio);
  const exported=safeExport(original);
  assert.equal(JSON.stringify(original),before);
  assert.deepEqual(exported.table,original.table);
  assert.equal(exported.table[0].amount,'12345678901234567890.123456789');
  assert.notEqual(exported,original);
});
