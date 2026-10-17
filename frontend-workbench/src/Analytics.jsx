import React, { useEffect, useId, useMemo, useRef, useState } from 'react';
import { analyzeData, analysisDraft, chartSeries, columnRole, LIMITS, parseData, rawText, suggestColumns, tableFromResponse } from './analysis.mjs';
import { clampYaw, DEFAULT_YAW, PALETTE, sceneGeometry } from './chart.mjs';
import './analytics.css';

// Ephemeral browser memory only: never localStorage, network, or an automatic query.
let localAnalysis = null;
const METHODS = { sum: '求和', mean: '平均值', count: '记录计数' };
const labelFor = (table, column) => typeof table?.labels?.[column] === 'string' && table.labels[column].trim() ? table.labels[column] : column;
function responseTable(response) { try { return { table: tableFromResponse(response), error: '' }; } catch (e) { return { table: null, error: e.message }; } }
function navigate(callback, page) { callback?.(page); }
function saveJSON(value, name) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function RawTable({ table }) {
  if (!table) return null;
  return <section className="analytics-card analytics-preview"><div className="analytics-panel-head"><h3>原始数据预览</h3><span>前 {Math.min(8, table.rows.length)} 行 / 共 {table.rows.length} 行</span></div>
    <div className="analytics-table-scroll" data-testid="analytics-source-table"><table><thead><tr>{table.columns.map(k => <th key={k}>{labelFor(table, k)}</th>)}</tr></thead><tbody>{table.rows.slice(0, 8).map((row, i) => <tr key={i}>{table.columns.map(k => <td key={k}>{rawText(row[k])}</td>)}</tr>)}</tbody></table></div>
    <p className="analytics-note">原始值逐字显示；NULL、空字符串与 0 分开保留。{table.truncated ? ' 服务端返回结果已截断，图表不代表完整数据库。' : ' 仅分析当前返回或导入的记录。'}</p>
  </section>;
}
function Fields({ table, config, setConfig }) {
  return <div className="analytics-fields"><label>分类列<select data-testid="analytics-category" value={config.category} onChange={e => setConfig({ ...config, category: e.target.value })}>{table.columns.map(k => <option key={k} value={k}>{labelFor(table, k)}</option>)}</select></label>
    <label>单一数值列<select data-testid="analytics-metric" value={config.metric} disabled={config.method === 'count'} onChange={e => setConfig({ ...config, metric: e.target.value })}><option value="">请选择数值列</option>{table.columns.filter(k => columnRole(table, k) !== 'identity').map(k => <option key={k} value={k}>{labelFor(table, k)}</option>)}</select></label>
    <label>汇总方式<select data-testid="analytics-method" value={config.method} onChange={e => setConfig({ ...config, method: e.target.value })}>{Object.entries(METHODS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label></div>;
}
function Chart({ result, source = 'response', metricLabel }) {
  const chart = useMemo(() => chartSeries(result), [result]);
  const [view, setView] = useState(chart.ringAllowed ? 'ring' : 'bars'); const [yaw, setYaw] = useState(DEFAULT_YAW); const [selected, setSelected] = useState(0);
  const uid = 'analytics-' + useId().replace(/[^a-zA-Z0-9_-]/g, '');
  useEffect(() => { setSelected(0); if (!chart.ringAllowed) setView('bars'); }, [result, chart.ringAllowed]);
  const geometry = useMemo(() => sceneGeometry(chart.rows, view, yaw), [chart, view, yaw]);
  const current = chart.rows[selected] || chart.rows[0];
  const choose = i => setSelected(i);
  const keyChoose = (event, i) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); choose(i); } };
  const share = chart.ringAllowed && current ? current.value / chart.total * 100 : null;
  const reset = () => { setYaw(DEFAULT_YAW); setSelected(0); };
  return <div className="analytics-overview-grid">
    <section className="analytics-scene" aria-label="交互式立体数据图表"><div className="analytics-scene-head"><span className="analytics-eyebrow">{source === 'local' ? 'LOCAL DATA' : 'QUERY RESULT'} / APPROXIMATE VIEW</span><h2>{result.method === 'count' ? '记录分布' : `${metricLabel || result.metric} · ${METHODS[result.method]}`}</h2><p>单列同口径统计 · 原始表格为准</p><strong>{result.method === 'count' ? result.stats.rows : result.method === 'mean' ? result.stats.mean : result.stats.sum}</strong>{result.method === 'mean' && result.stats.meanApproximate && <small>平均值为近似小数</small>}</div>
      <div className="analytics-chart-modes" role="group" aria-label="图表类型">{[['ring', '环形', '◉'], ['bars', '柱状', '▥'], ['ribbon', '序列', '⌁']].map(([key, title, glyph]) => <button key={key} type="button" className={view === key ? 'selected' : ''} aria-label={`立体${title}图`} aria-pressed={view === key} disabled={key === 'ring' && !chart.ringAllowed} title={key === 'ring' && !chart.ringAllowed ? '环图仅用于多个非负、可加总的类别；比例或均值不重归一。' : title} onClick={() => setView(key)}><span aria-hidden="true">{glyph}</span><small>{title}</small></button>)}</div>
      <div className="analytics-chart" data-testid="analytics-chart" data-chart-type={view} data-source={source} data-series={JSON.stringify(chart.rows)}>
        {chart.finite ? <svg viewBox="0 0 950 650" role="img" aria-label={`${METHODS[result.method]}近似可视化；原始数值见表格`}>
          <defs><linearGradient id={`${uid}-floor`} x1="0" y1="0" x2="1" y2="1"><stop stopColor="#e3ecf2" stopOpacity=".7" /><stop offset=".6" stopColor="#fff" stopOpacity=".95" /><stop offset="1" stopColor="#d0e0ea" stopOpacity=".5" /></linearGradient>{PALETTE.map((color, i) => <React.Fragment key={color}><linearGradient id={`${uid}-top${i}`} x1="0" y1="0" x2="1" y2="1"><stop stopColor="#fff" stopOpacity=".8" /><stop offset=".2" stopColor={color} stopOpacity=".85" /><stop offset="1" stopColor={color} /></linearGradient><linearGradient id={`${uid}-side${i}`} x1="0" y1="0" x2=".3" y2="1"><stop stopColor={color} /><stop offset="1" stopColor={color} stopOpacity=".45" /></linearGradient></React.Fragment>)}</defs>
          <path d={geometry.floor} fill={`url(#${uid}-floor)`} stroke="#d7e3e9" />{geometry.grid.map((d, i) => <path key={i} d={d} fill="none" stroke="#c0d3df" strokeWidth=".7" opacity=".5" />)}
          {geometry.plinth && <path d={geometry.plinth} fill="#edf3f7" stroke="#fff" strokeWidth="3" />}
          {geometry.faces.map(face => <g key={face.i} className={`analytics-face ${selected === face.i ? 'selected' : ''}`} role="button" tabIndex="0" aria-label={`选择 ${chart.rows[face.i].label}，原值 ${chart.rows[face.i].raw_value}`} onClick={() => choose(face.i)} onKeyDown={e => keyChoose(e, face.i)}><title>{`${chart.rows[face.i].label}：${chart.rows[face.i].raw_value}`}</title>{face.sides.map((d, j) => <path key={j} d={d} fill={`url(#${uid}-side${face.i % PALETTE.length})`} stroke="#ffffff99" />)}<path d={face.cap} fill={`url(#${uid}-top${face.i % PALETTE.length})`} stroke="#fff" strokeWidth="1.5" />{face.pin && <text x={face.pin[0]} y={face.pin[1]} textAnchor="middle" className="analytics-data-pin">{Number(chart.rows[face.i].value.toPrecision(5)).toLocaleString()}</text>}</g>)}
          {geometry.ribbon && <path d={geometry.ribbon} fill={`url(#${uid}-top2)`} opacity=".75" stroke="#fff" strokeWidth="2" />}
          {geometry.baseline && <path d={geometry.baseline} stroke="#a4bdc9" strokeDasharray="5 5" />}{geometry.line && <path d={geometry.line} stroke="#fff" strokeWidth="4" fill="none" />}
          {geometry.points?.map((point, i) => <g key={i} role="button" tabIndex="0" className="analytics-face" aria-label={`选择 ${chart.rows[i].label}，原值 ${chart.rows[i].raw_value}`} onClick={() => choose(i)} onKeyDown={e => keyChoose(e, i)}><title>{`${chart.rows[i].label}：${chart.rows[i].raw_value}`}</title><circle cx={point[0]} cy={point[1]} r={i === selected ? 9 : 6} fill={PALETTE[i % PALETTE.length]} stroke="#fff" strokeWidth="3" /></g>)}
        </svg> : <div className="analytics-chart-unavailable">数值超出可靠图示范围，请查看精确统计和原始表。</div>}
      </div>
      <div className="analytics-scene-bottom"><span>点击选择 · 按钮旋转</span><div><button type="button" aria-label="向左旋转" onClick={() => setYaw(clampYaw(yaw - .22))}>↶</button><button type="button" aria-label="向右旋转" onClick={() => setYaw(clampYaw(yaw + .22))}>↷</button><button type="button" aria-label="重置图表视角" onClick={reset}>重置</button></div></div>
    </section>
    <aside className="analytics-side"><section className="analytics-card analytics-selected"><div className="analytics-panel-head"><h3>当前选择</h3><span>SELECTED</span></div><h4>{current?.label || '无可绘制分类'}</h4><strong>{current?.raw_value ?? '—'}</strong><p>{current ? `${current.rows} 条原始记录` : '不把空值变成零'}</p>{share !== null ? <><div className="analytics-share-track"><i style={{ width: `${share}%`, background: PALETTE[selected % PALETTE.length] }} /></div><small>约 {share.toFixed(1)}% · 仅占所绘类别数值之和，并非原SQL业务占比</small></> : <small>不计算分布占比：保留负数、单值、比例和均值的原意。</small>}</section>
      <section className="analytics-card analytics-breakdown"><div className="analytics-panel-head"><h3>分类明细</h3><span>{result.grouped.length} 类</span></div>{chart.rows.map((row, i) => <button key={i} type="button" className={i === selected ? 'selected' : ''} onClick={() => choose(i)}><i style={{ background: PALETTE[i % PALETTE.length] }} /><span>{row.label}</span><b>{row.raw_value}</b></button>)}<p className="analytics-note">{chart.omitted ? `图示仅取前8个有值类别，另${chart.omitted}类未绘；未合并、未重排原数据。` : '图形位置和高度使用近似数值，精确值保留在明细与原表。'} {result.method === 'mean' ? '各组均值不相加为总体。' : ''}</p></section>
    </aside>
  </div>;
}

export function Overview({ latestResponse, onNavigate }) {
  const current = useMemo(() => responseTable(latestResponse), [latestResponse]);
  const [source, setSource] = useState(localAnalysis?.showChart ? 'local' : 'response');
  const table = source === 'local' ? localAnalysis?.table : current.table;
  const [config, setConfig] = useState(() => current.table ? { ...suggestColumns(current.table), method: 'sum' } : { category: '', metric: '', method: 'sum' });
  useEffect(() => { if (source === 'response' && current.table) setConfig({ ...suggestColumns(current.table), method: 'sum' }); }, [current.table, source]);
  const resolved = useMemo(() => {
    if (source === 'local' && localAnalysis) return { result: localAnalysis.result, error: '' };
    if (!table || (!config.metric && config.method !== 'count')) return { result: null, error: '' };
    try { return { result: analyzeData(table, config), error: '' }; } catch (e) { return { result: null, error: e.message }; }
  }, [source, table, config]);
  return <section className="analytics-root analytics-overview"><header className="analytics-page-heading"><div><p className="analytics-eyebrow">DATA OVERVIEW / 数据概览</p><h1>让数据，呈现更多维度</h1><p>查看真实返回表，或在本地分析自己的数据。</p></div><div className="analytics-actions"><button data-testid="analytics-load-latest" type="button" onClick={() => { setSource('response'); if (current.table) setConfig({ ...suggestColumns(current.table), method: 'sum' }); }}>加载最近查询</button><button type="button" className="analytics-primary" onClick={() => navigate(onNavigate, 'analysis')}>导入数据 ↗</button></div></header>
    {table && source === 'response' && <section className="analytics-card analytics-selector"><div><b>最近查询返回 · {table.rows.length} 行</b><p>选择一个有意义的指标。ID、年份不作金额；比例不重新归一。</p></div><Fields table={table} config={config} setConfig={setConfig} /></section>}
    {(current.error || resolved.error) && <p className="analytics-error" role="alert" data-testid="analytics-error">{resolved.error || current.error}</p>}
    {resolved.result ? <Chart result={resolved.result} source={source} metricLabel={labelFor(table, resolved.result.metric)} /> : <div className="analytics-empty" data-testid="analytics-empty"><div className="analytics-empty-orbit" aria-hidden="true"><span /><span /><span /></div><span className="analytics-eyebrow">YOUR DATA, YOUR INSIGHTS</span><h2>{table ? '先选择本次要看的单一指标' : '从一份真实数据开始'}</h2><p>{table ? '多个数值列或比例列不会被自动拼成占比。你也可以按行计数，或前往分析页选择统计口径。' : '这里还没有业务数据。运行一次查询，或导入 CSV、TSV、JSON，图表就会随你的数据更新。'}</p><div className="analytics-actions"><button type="button" className="analytics-primary" onClick={() => navigate(onNavigate, 'workspace')}>进入问答工作台 →</button><button type="button" onClick={() => navigate(onNavigate, 'analysis')}>本地导入分析</button></div><small>无默认业务数据 · 无演示结果混入</small></div>}
    {table && <RawTable table={table} />}<footer className="analytics-footer"><span>图表仅为近似可视化；原始表格与查询范围是权威依据。</span><button type="button" onClick={() => navigate(onNavigate, 'data')}>查看数据与文档 ↗</button><button type="button" onClick={() => navigate(onNavigate, 'history')}>运行记录 ↗</button></footer>
  </section>;
}

export function Analysis({ latestResponse, onNavigate, onUseQuestion }) {
  const [text, setText] = useState(localAnalysis?.text || ''), [filename, setFilename] = useState(localAnalysis?.filename || '粘贴的数据');
  const [table, setTable] = useState(localAnalysis?.table || null), [result, setResult] = useState(localAnalysis?.result || null), [boundText, setBoundText] = useState(localAnalysis?.text || '');
  const [config, setConfig] = useState(localAnalysis?.config || { category: '', metric: '', method: 'sum' }); const [error, setError] = useState(''), [notice, setNotice] = useState(''), [dragging, setDragging] = useState(false);
  const file = useRef(null), readVersion = useRef(0);
  const clear = () => { readVersion.current++; setText(''); setTable(null); setResult(null); setBoundText(''); setError(''); setNotice(''); setFilename('粘贴的数据'); localAnalysis = null; };
  const edit = value => { readVersion.current++; setText(value); setTable(null); setResult(null); setFilename('粘贴的数据'); setNotice('内容已修改，请重新分析。'); setError(''); localAnalysis = null; };
  const run = () => {
    try {
      setError(''); let actual = table, choice = config;
      if (!actual || text !== boundText) { actual = parseData(text); choice = suggestColumns(actual); setTable(actual); setBoundText(text); setConfig(choice); if (choice.requiresChoice) { setResult(null); setNotice('检测到多个数值列，请明确选择一列和汇总方式，再点击分析。'); return; } }
      const next = analyzeData(actual, choice); setResult(next); setNotice(actual.numericLexemesPreserved ? 'JSON 数字按原字面值保留，避免长小数或大整数被提前舍入。' : '本地统计已更新；原始值未改变。');
      localAnalysis = { text, filename, table: actual, config: choice, result: next, showChart: false };
    } catch (e) { setResult(null); setError(e.message || '数据无法分析。'); }
  };
  const readFile = async selected => {
    if (!selected) return; const version = ++readVersion.current;
    setResult(null); localAnalysis = null;
    try {
      if (selected.size > LIMITS.bytes) throw Error('文件最大支持 2MB。');
      if (!/\.(csv|tsv|json|txt)$/i.test(selected.name)) throw Error('请导入 CSV、TSV、JSON 或 TXT 文件。');
      const buffer = await selected.arrayBuffer(), bytes = new Uint8Array(buffer); let content;
      if (bytes[0] === 255 && bytes[1] === 254) content = new TextDecoder('utf-16le').decode(buffer);
      else if (bytes[0] === 254 && bytes[1] === 255) content = new TextDecoder('utf-16be').decode(buffer);
      else { try { content = new TextDecoder('utf-8', { fatal: true }).decode(buffer); } catch { throw Error('无法按 UTF-8 读取，请将文件另存为 UTF-8 CSV 或 TSV。'); } }
      if (version !== readVersion.current) return;
      setText(content); setFilename(selected.name); setTable(null); setResult(null); setError(''); setNotice('文件已在本地读取，点击分析；没有上传或外发。'); localAnalysis = null;
    } catch (e) { if (version === readVersion.current) setError(e.message); }
  };
  const loadLatest = () => { readVersion.current++; const next = responseTable(latestResponse); if (!next.table) { setError(next.error || '最近返回中没有可分析的原始表格。'); return; } const content = JSON.stringify(next.table.rows, null, 2); setText(content); setBoundText(content); setTable(next.table); setConfig(suggestColumns(next.table)); setResult(null); setFilename('最近查询原始返回表'); setError(''); setNotice('已加载原始返回表，请确认列和统计口径后分析。'); localAnalysis = null; };
  return <section className="analytics-root analytics-analysis"><header className="analytics-page-heading"><div><p className="analytics-eyebrow">YOUR DATA / YOUR INSIGHTS</p><h1>分析你的数据</h1><p>选择分类与单一指标，把表格变成清晰的统计和立体图表。</p></div><span className="analytics-local-badge"><i />本地处理 · 不自动上传</span></header>
    <div className="analytics-analysis-grid"><section className="analytics-card analytics-input-panel"><div className="analytics-panel-head"><h2><small>01</small> 添加数据</h2><button type="button" onClick={clear}>清空</button></div>
      <div className={`analytics-dropzone ${dragging ? 'dragging' : ''}`} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); readFile(e.dataTransfer.files[0]); }}><span aria-hidden="true">↥</span><div><b>{filename === '粘贴的数据' ? '拖入文件，或点击导入' : filename}</b><small>CSV / TSV / JSON · 最大 2MB · 最多 20,000 行</small></div><button type="button" onClick={() => file.current?.click()}>导入 ＋</button></div>
      <input ref={file} data-testid="analytics-file-input" type="file" accept=".csv,.tsv,.json,.txt" hidden onChange={e => { readFile(e.target.files[0]); e.target.value = ''; }} />
      <label className="analytics-input-label" htmlFor="analytics-local-text">或粘贴表格 <small>首行是列名，可直接从 Excel 复制</small></label><textarea id="analytics-local-text" data-testid="analytics-csv-input" value={text} onChange={e => edit(e.target.value)} spellCheck="false" placeholder={'分类,数值\n在这里粘贴你的实际数据'} />
      <p className="analytics-note">选择同一量纲的单列；不把金额、数量、比例相加。NULL／空白不计入求和与平均，0 和负数保留。</p>
      {table && <Fields table={table} config={config} setConfig={v => { setConfig(v); setResult(null); localAnalysis = null; setNotice('统计口径已修改，点击分析更新。'); }} />}
      {error && <p className="analytics-error" data-testid="analytics-error" role="alert">{error}</p>}<p className="analytics-status" aria-live="polite">{notice || '尚未导入数据'}</p><div className="analytics-actions"><button type="button" onClick={loadLatest}>加载最近查询表</button><button type="button" className="analytics-primary" data-testid="analytics-run" onClick={run}>分析数据 →</button></div>
    </section>
    <section className="analytics-output"><div className="analytics-panel-head"><h2><small>02</small> 统计结果</h2><button type="button" disabled={!result} onClick={() => saveJSON({ format: 'local-analysis-v1', source: filename, result, columns: table.columns, original_rows: table.rows }, '本地数据分析.json')}>导出完整结果 ↓</button></div>
      {!result ? <div className="analytics-empty analytics-analysis-empty" data-testid="analytics-empty"><span className="analytics-empty-symbol" aria-hidden="true">▥</span><h2>从你的数据开始</h2><p>分析后显示记录数、精确合计、平均值和分类分布。这里不会填入虚构的业务指标。</p></div> : <><div className="analytics-stat-grid">{[['记录数', String(result.stats.rows), '每一行是一条记录'], ['有效数值', String(result.stats.valid), `空缺 ${result.stats.missing} · 非数值 ${result.stats.invalid}`], ['分类数', String(result.stats.categories), labelFor(table, result.category)], ['数值合计', result.stats.sum, result.method === 'count' ? '计数不求和原数值列' : labelFor(table, result.metric)], ['平均值', result.stats.mean, result.stats.meanApproximate ? '循环小数，近似显示' : '按有效数值等权计算'], ['最小 / 最大', result.stats.min === null ? null : `${result.stats.min} / ${result.stats.max}`, '原表数值口径']].map(([name, value, note]) => <div key={name} className="analytics-card analytics-stat"><small>{name}</small><strong>{value ?? '—'}</strong><span>{note}</span></div>)}</div>
        <section className="analytics-summary"><h3>本地数据摘要</h3><p>{result.stats.rows} 行数据，按“{labelFor(table, result.category)}”分类，以{METHODS[result.method]}统计{result.method === 'count' ? '每行记录' : `“${labelFor(table, result.metric)}”`}。空缺和非数值不被当成 0。</p><p>{result.method === 'mean' || result.ratio ? '均值和比例只展示各类数值，不重归一成占比环。' : '图形仅使用近似数值；完整原表和精确统计仍可导出。'}</p><button type="button" onClick={() => { localAnalysis = { text, filename, table, result, config, showChart: true }; navigate(onNavigate, 'overview'); }}>查看立体图表 ↗</button></section>
        <div className="analytics-table-scroll"><table><thead><tr><th>分类</th><th>{METHODS[result.method]}</th><th>原始记录数</th></tr></thead><tbody>{result.grouped.slice(0, 100).map((g, i) => <tr key={i}><td>{g.label}</td><td>{g.valueText ?? 'NULL（无有效数值）'}{g.approximate ? ' ≈' : ''}</td><td>{g.rows}</td></tr>)}</tbody></table></div><p className="analytics-note">共 {result.grouped.length} 类，页面最多展示前 100 类；导出包含全部分类与原始行。</p><Chart result={result} source="local" /></>}
      <div className="analytics-draft-box"><div><h3>继续在工作台探索</h3><p>仅把明确标记的本地摘要填入草稿；不上传文件或全量数据，确认后才由你发送。</p></div><button type="button" data-testid="analytics-use-question" disabled={!result || !onUseQuestion} onClick={() => { onUseQuestion?.(analysisDraft(result, filename)); navigate(onNavigate, 'workspace'); }}>整理为草稿 ↗</button></div>
    </section></div>{table && <RawTable table={table} />}
  </section>;
}
