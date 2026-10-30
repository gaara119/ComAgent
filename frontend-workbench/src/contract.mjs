/** UI projection only. Preserve database values in AnswerEnvelope and exports. */
const hiddenDiagnosticKey = /(?:api[_-]?key|password|secret|authorization|(?:^|_)db[_-]?url$|dsn$|^(?:system|user|full)[_-]?prompt$|^prompt$|^catalog$)/i;

export function safeText(value) {
  return String(value)
    .replace(/\bsk-[A-Za-z0-9_-]+/gi, '[已隐藏凭据]')
    .replace(/Bearer\s+[^\s"'<>]+/gi, 'Bearer [已隐藏凭据]')
    .replace(/postgres(?:ql)?(?:\+[a-z0-9_-]+)?:\/\/[^\s"'<>]+/gi, '[已隐藏数据库连接]');
}

function redact(value, bounded, depth = 0) {
  if (typeof value === 'string') {
    const text = safeText(value);
    return bounded && text.length > 2000 ? `${text.slice(0, 2000)}…[已截断]` : text;
  }
  if (value === null || typeof value !== 'object') return value;
  if (bounded && depth >= 8) return '[层级过深，已省略]';
  if (Array.isArray(value)) {
    const output = (bounded ? value.slice(0, 20) : value).map(item => redact(item, bounded, depth + 1));
    if (bounded && value.length > 20) output.push(`[另有${value.length - 20}项，已省略]`);
    return output;
  }
  const entries = Object.entries(value);
  const output = Object.fromEntries((bounded ? entries.slice(0, 50) : entries).map(([key, item]) => [safeText(key), hiddenDiagnosticKey.test(key) ? '[已隐藏]' : redact(item, bounded, depth + 1)]));
  if (bounded && entries.length > 50) output['[已省略字段]'] = entries.length - 50;
  return output;
}

/** Bounded, redacted diagnostic projection. Does not mutate API data. */
export const safeDiagnostics = value => redact(value, true);
/** Export all business rows and precise numbers, while redacting credentials/prompts. */
export const safeExport = value => redact(value, false);

export function apiErrorMessage(data, status) {
  return safeText(typeof data?.detail === 'string' ? data.detail : Array.isArray(data?.detail) ?
    data.detail.map(item=>`${(item.loc||[]).join('.')}: ${item.msg}`).join('；') :
    data?.detail?.message || data?.error?.message || `请求失败（HTTP ${status}）`);
}

export function databaseErrorMessage(error, password = '') {
  const text=String(error?.message || error || '数据库操作未完成。');
  return safeText(password ? text.split(password).join('[已隐藏密码]') : text);
}

export function displayValue(value, rule) {
  if (value === null) return 'NULL（空值）';
  const precision = rule && Object.hasOwn(rule, 'digits');
  const digits = precision ? rule.digits : 2;
  const trusted = precision ? rule.source === 'actual_sql_projection' :
    !rule?.source || ['sql_projection', 'actual_sql_projection'].includes(rule.source);
  const validDigits = digits === null || (Number.isInteger(digits) && digits >= 0 && digits <= 9);
  const percent = rule?.kind === 'percentage' && [1, 100].includes(rule.scale);
  const money = rule?.kind === 'money' && precision && (rule.scale === undefined || rule.scale === 1);
  const validRounding = rule?.rounding === undefined || rule?.rounding === 'half_even';
  if (rule?.kind === 'count' && rule.source === 'actual_sql_projection' && typeof value !== 'boolean' && value !== null && /^[-+]?\d+(?:\.0*)?$/.test(String(value)))
    return BigInt(String(value).split('.')[0]).toString();
  if (trusted && validDigits && validRounding && (percent || money) && typeof value !== 'boolean') {
    const match = String(value).match(/^([+-]?)(\d+)(?:\.(\d*))?$/);
    if (match) {
      const [, sign, whole, fraction = ''] = match;
      // Integer arithmetic avoids changing precise numeric-string evidence.
      let scaled = BigInt(whole + fraction);
      const decimalPlaces = fraction.length - (percent && rule.scale === 100 ? 2 : 0);
      if (digits === null) {
        // Preserve the existing Decimal multiplication quantum: multiplying
        // 0.12345 by integer100 yields12.34500, not a new two-place rounding.
        const target = fraction.length;
        if (percent && rule.scale === 100) scaled *= 100n;
        const raw = scaled.toString().padStart(target + 1, '0');
        const rendered = target ? raw.slice(0, -target) + '.' + raw.slice(-target) : raw;
        return `${sign === '-' ? '-' : ''}${rendered}${percent ? '%' : ''}`;
      }
      const shift = decimalPlaces - digits;
      if (shift > 0) {
        const divisor = 10n ** BigInt(shift);
        const quotient = scaled / divisor;
        const remainder = scaled % divisor;
        // Match Python Decimal's existing round-half-even presentation.
        const even = precision || rule.rounding === 'half_even';
        scaled = quotient + (remainder * 2n > divisor ||
          (remainder * 2n === divisor && (!even || quotient % 2n === 1n)) ? 1n : 0n);
      } else scaled *= 10n ** BigInt(-shift);
      const rendered = scaled.toString().padStart(digits + 1, '0');
      return `${sign === '-' && (precision || scaled !== 0n) ? '-' : ''}${digits ? rendered.slice(0, -digits) + '.' + rendered.slice(-digits) : rendered}${percent ? '%' : ''}`;
    }
  }
  return typeof value === 'object' ? JSON.stringify(value) : String(value ?? '');
}

export function makeScope(route, db, doc) {
  if (route === 'sql') return { route, db_id: db, doc_ids: [] };
  if (route === 'auto') return { route, db_id: db, doc_ids: doc ? [doc] : [] };
  if (route === 'hybrid') return { route, db_id: 'chinook', doc_ids: doc ? [doc] : [] };
  return { route: 'doc', db_id: null, doc_ids: doc ? [doc] : [] };
}

/** Keep the registry projection public: connection credentials never enter UI history or exports. */
export function publicDatabase(item) {
  if (!item || typeof item.db_id !== 'string' || !item.db_id.trim()) return null;
  return {db_id:item.db_id,name:safeText(item.name || item.label || item.db_id),label:safeText(item.label || item.name || item.db_id),
    builtin:item.builtin === true,configured:item.configured === true,catalog_exists:item.catalog_exists === true,
    catalog_summary:safeExport(item.catalog_summary || {})};
}

export function databaseReady(db, health, databases = []) {
  // Built-in health probes are retained for compatibility and reflect current connectivity.
  if (db === 'chinook') return health?.database_ready === true;
  if (db === 'adventureworks') return health?.aw_database_ready === true;
  const item = databases.find(item => item.db_id === db);
  return Boolean(item?.configured && item?.catalog_exists);
}

export function sourceReady(route, db, doc, health, documents, databases = []) {
  if (health?.status !== 'ok' || health.llm_configured === false) return false;
  if (route === 'sql') return databaseReady(db, health, databases);
  if (route === 'auto') return databaseReady(db, health, databases) &&
    (!doc || documents.some(item => item.doc_id === doc && item.ready));
  const docsReady = doc ? documents.some(item => item.doc_id === doc && item.ready) : route === 'hybrid' && documents.some(item => item.ready);
  return Boolean(docsReady && (route !== 'hybrid' || health.database_ready === true));
}

export function makeContextRequest(sessionId, text) {
  if (typeof text !== 'string' || !text.trim()) throw new Error('请填写本会话正文。');
  if (text.length > 120000) throw new Error('会话正文不能超过120000个字符。');
  return {session_id:sessionId,text};
}

export function bindContextResponse(response, sessionId, scope) {
  if (response?.session_id !== sessionId || typeof response.context_id !== 'string' || !response.context_id ||
      !Number.isInteger(response.version) || response.version < 1 || !Number.isInteger(response.characters) || response.characters < 1 ||
      !/^[a-f\d]{64}$/i.test(response.content_sha256 || '')) throw new Error('正文保存响应缺少有效会话、版本或完整性信息。');
  return {...response,scope_key:JSON.stringify(scope)};
}

export function attachContext(payload, binding) {
  if (!binding) return payload;
  if (payload.session_id !== binding.session_id || JSON.stringify(payload.scope) !== binding.scope_key)
    throw new Error('正文绑定的会话或来源已改变，请重新保存正文。');
  return {...payload,context_id:binding.context_id};
}

export function columnTitle(key, labels) {
  return typeof labels?.[key] === 'string' && labels[key].trim() ? labels[key] : key;
}
