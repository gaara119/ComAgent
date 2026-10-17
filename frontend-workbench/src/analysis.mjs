/** Local-only analysis. Original rows are never coerced or mutated. */
export const LIMITS = Object.freeze({ bytes: 2 * 1024 * 1024, rows: 20000, columns: 100 });
const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
const ID = /(?:^|_)(?:id|year|month|date|timestamp)(?:$|_)|(?:编号|年份|年度|日期|月份)$/i;
const RATIO = /(?:^|_)(?:ratio|share|percent|percentage|rate|pct|growth)(?:$|_)|占比|比例|增长率|百分比/i;

function columnsValid(columns) {
  if (!columns.length || columns.length > LIMITS.columns) throw Error('请提供 1 至 100 列数据。');
  if (columns.some(k => typeof k !== 'string' || !k.trim())) throw Error('表头必须是非空文本。');
  if (new Set(columns).size !== columns.length) throw Error('表头存在重复列名，请先区分名称。');
}
function validateRows(rows) {
  if (!Array.isArray(rows) || !rows.length) throw Error('请提供至少一行数据。');
  if (rows.length > LIMITS.rows) throw Error('本地分析最多支持 20,000 行；不会自动截断输入。');
  if (rows.some(r => !r || typeof r !== 'object' || Array.isArray(r))) throw Error('每行数据必须是对象。');
}

/** Decimal arithmetic is exact for sums; means disclose a repeating decimal. */
function decimal(value) {
  if (typeof value === 'number' && !Number.isFinite(value)) return null;
  if (!['number', 'string'].includes(typeof value)) return null;
  let text = String(value).trim();
  if (/^[+-]?\d{1,3}(,\d{3})+(\.\d+)?$/.test(text)) text = text.replace(/,/g, '');
  const m = /^([+-]?)(\d+(?:\.\d*)?|\.\d+)(?:e([+-]?\d+))?$/i.exec(text);
  if (!m || text.length > 1024 || Math.abs(Number(m[3] || 0)) > 256) return null;
  const [whole, fraction = ''] = m[2].split('.');
  let n = BigInt((whole || '0') + fraction) * (m[1] === '-' ? -1n : 1n);
  let s = fraction.length - Number(m[3] || 0);
  if (s < 0) { n *= 10n ** BigInt(-s); s = 0; }
  return { n, s };
}
function renderDecimal(n, scale) {
  const sign = n < 0n ? '-' : ''; const raw = (n < 0n ? -n : n).toString().padStart(scale + 1, '0');
  return sign + (scale ? raw.slice(0, -scale) + '.' + raw.slice(-scale) : raw);
}
function sum(values) {
  const s = values.reduce((v, d) => Math.max(v, d.s), 0);
  return { n: values.reduce((v, d) => v + d.n * 10n ** BigInt(s - d.s), 0n), s };
}
function mean(d, count) {
  const places = Math.max(d.s, 18), numerator = d.n * 10n ** BigInt(places - d.s);
  const divisor = BigInt(count), n = numerator / divisor;
  return { text: renderDecimal(n, places), approximate: numerator % divisor !== 0n };
}
function compare(a, b) { const s = Math.max(a.s, b.s); const v = a.n * 10n ** BigInt(s - a.s) - b.n * 10n ** BigInt(s - b.s); return v < 0n ? -1 : v > 0n ? 1 : 0; }
export function numeric(value) { const d = decimal(value); return d ? { exact: renderDecimal(d.n, d.s), approximate: Number(renderDecimal(d.n, d.s)) } : null; }
export function rawText(value) {
  if (value === null) return 'NULL';
  if (value === undefined) return '未提供';
  if (value === '') return '空字符串';
  return typeof value === 'object' ? JSON.stringify(value) : String(value);
}

// Preserve JSON numeric lexemes, including long decimals, before JSON.parse can round them.
function preciseJSON(text) {
  let transformed = '', quoted = false, escaped = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) { transformed += c; if (escaped) escaped = false; else if (c === '\\') escaped = true; else if (c === '"') quoted = false; continue; }
    if (c === '"') { quoted = true; transformed += c; continue; }
    if (c === '-' || /\d/.test(c)) {
      const m = /^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:e[+-]?\d+)?/i.exec(text.slice(i));
      if (m) { transformed += JSON.stringify(m[0]); i += m[0].length - 1; continue; }
    }
    transformed += c;
  }
  try { return JSON.parse(transformed); } catch { throw Error('JSON 格式有误，请检查括号、逗号和引号。'); }
}
function delimited(text) {
  let quoted = false; const counts = { ',': 0, '\t': 0, ';': 0 };
  for (let i = 0; i < text.length; i++) { const c = text[i]; if (c === '"') { if (quoted && text[i + 1] === '"') i++; else quoted = !quoted; } else if (!quoted) { if (c === '\n' || c === '\r') break; if (own(counts, c)) counts[c]++; } }
  const separator = Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0];
  const grid = []; let row = [], cell = '', inQuote = false, closed = false;
  const addRow = () => { row.push(cell); if (closed || row.length > 1 || row.some(v => v !== '')) grid.push(row); if (grid.length > LIMITS.rows + 1) throw Error('最多支持 20,000 行数据。'); row = []; cell = ''; closed = false; };
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuote) { if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else { inQuote = false; closed = true; } } else cell += c; continue; }
    if (c === '"') { if (cell !== '' || closed) throw Error('引号必须从单元格开头开始。'); inQuote = true; }
    else if (c === separator) { row.push(cell); cell = ''; closed = false; if (row.length >= LIMITS.columns + 1) throw Error('最多支持 100 列。'); }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; addRow(); }
    else { if (closed && !/\s/.test(c)) throw Error('结束引号后只能跟分隔符或换行。'); if (!closed) cell += c; }
  }
  if (inQuote) throw Error('存在未闭合的双引号。'); addRow();
  if (grid.length < 2) throw Error('需要一行表头和至少一行数据。');
  const columns = grid.shift().map(k => k.trim()); columnsValid(columns);
  const rows = grid.map((r, i) => { if (r.length !== columns.length) throw Error(`第 ${i + 2} 行列数与表头不同。`); return Object.fromEntries(columns.map((k, j) => [k, r[j]])); });
  return { columns, rows, format: separator === '\t' ? 'TSV' : 'CSV', source: 'local', formats: {} };
}
export function parseData(input) {
  if (typeof input !== 'string' || !input.trim()) throw Error('请先粘贴数据或导入文件。');
  if (new TextEncoder().encode(input).length > LIMITS.bytes) throw Error('数据最大支持 2MB；不会自动截断。');
  const text = input.replace(/^\uFEFF/, '');
  if (!/^[\[{]/.test(text.trimStart())) return delimited(text);
  let value = preciseJSON(text.trim()), columns;
  if (value && !Array.isArray(value) && Array.isArray(value.columns) && Array.isArray(value.rows)) {
    columns = value.columns; columnsValid(columns);
    value = value.rows.map((r, i) => { if (!Array.isArray(r) || r.length !== columns.length) throw Error(`JSON 第 ${i + 1} 行与 columns 不一致。`); return Object.fromEntries(columns.map((k, j) => [k, r[j]])); });
  } else if (!Array.isArray(value)) value = value?.table ?? value?.data ?? value?.rows;
  if (Array.isArray(value) && value.length && value.every(v => decimal(v))) value = value.map((v, i) => ({ '记录': String(i + 1), '数值': v }));
  validateRows(value); columns ||= [...new Set(value.flatMap(v => Object.keys(v)))]; columnsValid(columns);
  return { columns, rows: value, format: 'JSON', source: 'local', formats: {}, numericLexemesPreserved: true };
}
export function tableFromResponse(response) {
  if (response?.metadata?.demo === true) return null;
  if (!Array.isArray(response?.table) || !response.table.length) return null;
  const rows = response.table; validateRows(rows);
  const actual = [...new Set(rows.flatMap(r => Object.keys(r)))];
  const proposed = response.metadata?.result_columns;
  const columns = Array.isArray(proposed) && proposed.length === actual.length && new Set(proposed).size === actual.length && proposed.every(k => actual.includes(k)) ? [...proposed] : actual;
  columnsValid(columns);
  return { columns, rows, format: '查询返回表', source: 'response', formats: response.metadata?.result_format || {}, labels: response.metadata?.column_labels || {}, truncated: !!response.metadata?.truncated };
}
export function columnRole(table, column) {
  if (ID.test(column) || /[a-z]Id$|ID$/.test(column)) return 'identity';
  if (table.formats?.[column]?.kind === 'percentage' || RATIO.test(column)) return 'ratio';
  return table.rows.some(r => decimal(r[column])) ? 'numeric' : 'category';
}
export function suggestColumns(table) {
  const metrics = table.columns.filter(k => columnRole(table, k) === 'numeric');
  const metric = metrics.length === 1 ? metrics[0] : '';
  const category = table.columns.find(k => columnRole(table, k) === 'category') || table.columns.find(k => k !== metric) || table.columns[0];
  return { category, metric, method: metric ? 'sum' : 'count', metrics, requiresChoice: metrics.length > 1 };
}
export function analyzeData(table, { category, metric = '', method = 'sum' }) {
  if (!table || !table.columns.includes(category)) throw Error('请选择分类列。');
  if (!['sum', 'mean', 'count'].includes(method)) throw Error('不支持的统计方式。');
  if (method !== 'count' && !table.columns.includes(metric)) throw Error('请选择一个数值列；不同列不会自动混合统计。');
  if (method !== 'count' && columnRole(table, metric) === 'identity') throw Error('编号或年份不作为数值指标求和；可用作分类，或按记录计数。');
  const groups = new Map(), all = []; let missing = 0, invalid = 0;
  for (const row of table.rows) {
    const key = JSON.stringify([typeof row[category], row[category] ?? null]);
    if (!groups.has(key)) groups.set(key, { label: rawText(row[category]), values: [], rows: 0 });
    const g = groups.get(key); g.rows++;
    if (method === 'count') continue;
    const v = decimal(row[metric]);
    if (v) { g.values.push(v); all.push(v); } else if (row[metric] === null || row[metric] === undefined || String(row[metric]).trim() === '') missing++; else invalid++;
  }
  if (method !== 'count' && !all.length) throw Error('这一列没有可统计数字；空值和布尔值不会变成 0。');
  const grouped = [...groups.values()].map(g => {
    let valueText = null, approximate = false;
    if (method === 'count') valueText = String(g.rows);
    else if (g.values.length) { const d = sum(g.values); if (method === 'mean') ({ text: valueText, approximate } = mean(d, g.values.length)); else valueText = renderDecimal(d.n, d.s); }
    return { label: g.label, valueText, rows: g.rows, valid: g.values.length, approximate };
  });
  const total = all.length ? sum(all) : null, sorted = [...all].sort(compare), avg = total ? mean(total, all.length) : null;
  return { category, metric, method, grouped, stats: { rows: table.rows.length, categories: groups.size, valid: method === 'count' ? table.rows.length : all.length, missing, invalid, sum: total ? renderDecimal(total.n, total.s) : null, mean: avg?.text ?? null, meanApproximate: avg?.approximate ?? false, min: sorted.length ? renderDecimal(sorted[0].n, sorted[0].s) : null, max: sorted.length ? renderDecimal(sorted.at(-1).n, sorted.at(-1).s) : null }, ratio: method !== 'count' && columnRole(table, metric) === 'ratio' };
}
export function chartSeries(result, maximum = 8) {
  const candidates = result?.grouped.filter(g => g.valueText !== null) || [];
  const rows = candidates.slice(0, maximum).map(g => ({ label: g.label, value: Number(g.valueText), raw_value: g.valueText, rows: g.rows }));
  const finite = rows.length > 0 && rows.every(r => Number.isFinite(r.value) && !(r.value === 0 && decimal(r.raw_value)?.n !== 0n));
  const total = finite ? rows.reduce((n, r) => n + r.value, 0) : NaN;
  return { rows: finite ? rows : [], omitted: Math.max(0, candidates.length - maximum), finite, ringAllowed: finite && rows.length > 1 && !result.ratio && result.method !== 'mean' && rows.every(r => r.value >= 0) && Number.isFinite(total) && total > 0, total };
}
export function analysisDraft(result, sourceLabel) {
  const methods = { sum: '求和', mean: '平均', count: '记录计数' };
  const brief = (v, n = 100) => String(v ?? 'NULL').length > n ? String(v).slice(0, n) + '…[摘要截取]' : String(v ?? 'NULL');
  const excerpt = result.grouped.slice(0, 5).map(g => ({ category: brief(g.label), value: brief(g.valueText, 160), rows: g.rows }));
  return `请帮我解释以下本地统计摘要。此消息仅含摘要，未上传文件或全量原始数据，不能据此重新核验全部记录或推断因果；长字段已在摘要中明确截取。\n来源：${brief(sourceLabel)}\n总记录：${result.stats.rows}；分类列：${brief(result.category)}；方式：${methods[result.method]}；单一指标：${brief(result.metric || '每行记录')}。\n空缺 ${result.stats.missing}，非数值 ${result.stats.invalid}；不把 NULL 当 0。\n分类摘要（前 ${excerpt.length} 类，共 ${result.grouped.length} 类）：${JSON.stringify(excerpt)}`;
}
