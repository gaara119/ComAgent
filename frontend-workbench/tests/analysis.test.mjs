import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeData, analysisDraft, chartSeries, columnRole, LIMITS, numeric, parseData, rawText, suggestColumns, tableFromResponse } from '../src/analysis.mjs';
import { clampYaw, sceneGeometry } from '../src/chart.mjs';

test('CSV quoting, TSV and semicolon detection preserve source cell strings', () => {
  const t = parseData('类别,金额\r\n"A, B","1,234.50"\r\n"双""引号", 2.00 \r\n');
  assert.equal(t.rows[0]['类别'], 'A, B'); assert.equal(t.rows[1]['类别'], '双"引号'); assert.equal(t.rows[1]['金额'], ' 2.00 ');
  assert.equal(parseData('类\t数\n甲\t1').format, 'TSV'); assert.equal(parseData('类;数\n甲;1').rows[0]['数'], '1');
});
test('all-empty explicit record is preserved; blank trailing line is not a record', () => {
  const t = parseData('分类,金额\n甲,1\n,\n'); assert.equal(t.rows.length, 2); assert.equal(t.rows[1]['金额'], '');
});
test('JSON numeric lexemes preserve long decimals and big integers exactly', () => {
  const t = parseData('[{"分类":"A","数":9007199254740993.12345678901234567890}]');
  assert.equal(t.rows[0]['数'], '9007199254740993.12345678901234567890');
  assert.equal(parseData('[{"分类":"1e3","数":1e3}]').rows[0]['分类'], '1e3');
  assert.equal(parseData('[{"数":true}]').rows[0]['数'], true);
});
test('JSON columns/rows and table envelopes, scalar arrays are supported locally', () => {
  assert.equal(parseData('{"columns":["类","数"],"rows":[["A",2]]}').rows[0]['数'], '2');
  assert.equal(parseData('{"table":[{"类":"A","数":3}]}').rows.length, 1);
  assert.equal(parseData('[1,0,-2] ').rows[2]['数值'], '-2');
});
for (const value of ['分类,数\nA,"oops', 'a,a\n1,2', ',数\nA,1', 'a,b\n1', 'a,b\n"x"oops,2', '[{"n":01}]', '{oops}']) {
  test(`invalid format is rejected: ${value}`, () => assert.throws(() => parseData(value)));
}
test('input limits reject oversized bytes, rows, and columns without truncation', () => {
  assert.throws(() => parseData('数\n' + '字'.repeat(LIMITS.bytes / 2)), /2MB/);
  assert.throws(() => parseData('数\n' + '1\n'.repeat(LIMITS.rows + 1)), /20,000/);
  assert.throws(() => parseData(Array.from({ length: 101 }, (_, i) => 'c' + i).join(',') + '\n' + Array(101).fill(1).join(',')), /100/);
});
test('latest AnswerEnvelope keeps original Decimal strings, null, booleans and ordering', () => {
  const response = { table: [{ id: 1, amount: '0.12345678901234567890', missing: null, flag: false }], metadata: { result_columns: ['amount', 'id', 'missing', 'flag'], truncated: true } };
  const snapshot = JSON.stringify(response), t = tableFromResponse(response);
  assert.equal(t.rows, response.table); assert.deepEqual(t.columns, ['amount', 'id', 'missing', 'flag']); assert.equal(t.rows[0].missing, null); assert.equal(t.truncated, true); assert.equal(JSON.stringify(response), snapshot);
  assert.equal(tableFromResponse({ table: [] }), null); assert.equal(tableFromResponse({ response: { table: [{ value: 5 }] } }), null);
  assert.equal(tableFromResponse({ table: [{ value: 5 }], metadata: { demo: true } }), null);
});
test('untrusted declared result columns cannot drop or duplicate actual columns', () => {
  const t = tableFromResponse({ table: [{ a: 1, b: 2 }], metadata: { result_columns: ['a', 'a'] } }); assert.deepEqual(t.columns, ['a', 'b']);
});
test('ID/year/camel Id are not chosen as metrics; ratio and multiple metrics need choice', () => {
  const t = parseData('customer_id,customerId,year,分类,金额,数量\n1,2,2025,A,10,2');
  assert.equal(columnRole(t, 'customerId'), 'identity'); assert.equal(suggestColumns(t).metric, ''); assert.equal(suggestColumns(t).requiresChoice, true);
  const ratio = tableFromResponse({ table: [{ share: '0.25' }], metadata: { result_format: { share: { kind: 'percentage', source: 'actual_sql_projection' } } } });
  assert.equal(suggestColumns(ratio).metric, '');
  assert.throws(() => analyzeData(t, { category: '分类', metric: 'year' }), /年份/);
});
test('a count-valued single result is represented as its actual value, not fabricated slices', () => {
  const t = tableFromResponse({ table: [{ customer_count: 5 }] }), c = suggestColumns(t), r = analyzeData(t, c), s = chartSeries(r);
  assert.equal(s.rows.length, 1); assert.equal(s.rows[0].value, 5); assert.equal(s.rows[0].raw_value, '5'); assert.equal(s.ringAllowed, false);
});
test('sum is exact; NULL/blank/boolean/invalid are excluded while zero and negative stay', () => {
  const t = parseData('[{"类":"A","数":"0.1"},{"类":"A","数":"0.2"},{"类":"B","数":null},{"类":"C","数":0},{"类":"D","数":-3.5},{"类":"E","数":""},{"类":"F","数":true},{"类":"G","数":"bad"}]');
  const r = analyzeData(t, { category: '类', metric: '数' });
  assert.equal(r.stats.sum, '-3.2'); assert.equal(r.stats.valid, 4); assert.equal(r.stats.missing, 2); assert.equal(r.stats.invalid, 2);
  assert.equal(r.grouped.find(g => g.label === 'B').valueText, null); assert.equal(r.grouped.find(g => g.label === 'C').valueText, '0');
  const s = chartSeries(r); assert.equal(s.ringAllowed, false); assert.deepEqual(s.rows.map(z => z.value), [.3, 0, -3.5]);
});
test('mean uses valid numeric denominators and marks repeating decimals', () => {
  const t = parseData('类,数\nA,1\nA,0\nA,\nA,0'); const r = analyzeData(t, { category: '类', metric: '数', method: 'mean' });
  assert.equal(r.stats.valid, 3); assert.equal(r.stats.mean, '0.333333333333333333'); assert.equal(r.stats.meanApproximate, true); assert.equal(chartSeries(r).ringAllowed, false);
});
test('count counts rows, including missing numeric values, but does not add numeric columns', () => {
  const t = parseData('类,金额,数量\nA,,2\nA,0,5\nB,-3,7'); const r = analyzeData(t, { category: '类', method: 'count' });
  assert.equal(r.stats.sum, null); assert.deepEqual(r.grouped.map(g => g.valueText), ['2', '1']); assert.equal(r.stats.rows, 3);
});
test('mixed metrics are not merged; null, empty and zero categories remain distinct', () => {
  const t = parseData('[{"类":null,"金额":"5","数量":100},{"类":"","金额":"2","数量":200},{"类":0,"金额":"3","数量":300}]');
  const r = analyzeData(t, { category: '类', metric: '金额' }); assert.equal(r.stats.sum, '10'); assert.deepEqual(r.grouped.map(g => g.label), ['NULL', '空字符串', '0']);
});
test('ratios do not become 100% slices, zero sums do not produce NaN shares', () => {
  const t = parseData('类,share_ratio\nA,.25\nB,.5'), r = analyzeData(t, { category: '类', metric: 'share_ratio' }); assert.equal(chartSeries(r).ringAllowed, false);
  const zeros = parseData('类,数\nA,0\nB,0'); assert.equal(chartSeries(analyzeData(zeros, { category: '类', metric: '数' })).ringAllowed, false);
});
test('positive multi-category sums can use ring; all grouped/source values remain available', () => {
  const t = parseData('类,数\n' + Array.from({ length: 12 }, (_, i) => `类${i},${i + 1}`).join('\n')); const r = analyzeData(t, { category: '类', metric: '数' }), s = chartSeries(r);
  assert.equal(s.ringAllowed, true); assert.equal(s.rows.length, 8); assert.equal(s.omitted, 4); assert.equal(r.grouped.length, 12); assert.equal(t.rows.length, 12);
});
test('overflow/underflow decline visualization rather than inventing zeros', () => {
  const big = parseData('类,数\nA,1e256\nB,1e256'); const r = analyzeData(big, { category: '类', metric: '数' }); assert.equal(r.stats.sum.length, 257);
  for (const value of ['1' + '0'.repeat(350), '0.' + '0'.repeat(400) + '1']) {
    const t = parseData('类,数\nA,' + value), result = analyzeData(t, { category: '类', metric: '数' });
    assert.equal(chartSeries(result).finite, false); assert.equal(t.rows[0]['数'], value);
  }
  assert.equal(numeric(false), null); assert.equal(numeric(null), null); assert.equal(numeric(''), null); assert.equal(numeric('10%'), null);
});
test('source labels stay inert text and local draft is explicit, bounded, not a full upload', () => {
  const t = parseData('类,数\n"<img src=x onerror=alert(1)>",1\nB,2'); const r = analyzeData(t, { category: '类', metric: '数' });
  assert.equal(r.grouped[0].label, '<img src=x onerror=alert(1)>'); const d = analysisDraft(r, 'local.csv'); assert.match(d, /未上传文件或全量/); assert.match(d, /原始数据/); assert.ok(d.length < 4000);
  assert.equal(rawText(null), 'NULL'); assert.equal(rawText('0.12345678901234567890'), '0.12345678901234567890');
});
test('all three chart geometries are finite for negative bars and zero series', () => {
  for (const kind of ['bars', 'ribbon', 'ring']) {
    const g = sceneGeometry(kind === 'ring' ? [{ value: 2 }, { value: 3 }] : [{ value: -2 }, { value: 0 }, { value: 3 }], kind, .3);
    assert.doesNotMatch(JSON.stringify(g), /NaN|Infinity/); assert.ok(g.floor.startsWith('M'));
  }
  assert.equal(clampYaw(-50), -.9); assert.equal(clampYaw(50), .45);
});

// Explicit quoted empties are records, unlike whitespace-free blank trailing lines.
test('single-column quoted empty record is not silently dropped', () => {
  const t = parseData('数\n""\n0\n\n');
  assert.equal(t.rows.length, 2); assert.equal(t.rows[0]['数'], ''); assert.equal(t.rows[1]['数'], '0');
});
test('chart geometry supports browsers without Array.toReversed', () => {
  const original = Array.prototype.toReversed;
  try {
    Array.prototype.toReversed = undefined;
    for (const view of ['ring','bars','ribbon']) assert(sceneGeometry([{ label:'A', value:1 },{ label:'B', value:2 }], view, .5));
  } finally { Array.prototype.toReversed = original; }
});
