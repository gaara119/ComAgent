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

export function displayValue(value, rule) {
  if (value === null) return 'NULL（空值）';
  if (rule?.kind === 'percentage' && [1, 100].includes(rule.scale) && typeof value !== 'boolean') {
    const match = String(value).match(/^([+-]?)(\d+)(?:\.(\d*))?$/);
    if (match) {
      const [, sign, whole, fraction = ''] = match;
      // Integer arithmetic avoids changing precise numeric-string evidence.
      let scaled = BigInt(whole + fraction);
      const decimalPlaces = fraction.length - (rule.scale === 100 ? 2 : 0);
      const shift = decimalPlaces - 2;
      if (shift > 0) {
        const divisor = 10n ** BigInt(shift);
        scaled = (scaled + divisor / 2n) / divisor;
      } else scaled *= 10n ** BigInt(-shift);
      const digits = scaled.toString().padStart(3, '0');
      return `${sign === '-' && scaled !== 0n ? '-' : ''}${digits.slice(0, -2)}.${digits.slice(-2)}%`;
    }
  }
  return typeof value === 'object' ? JSON.stringify(value) : String(value ?? '');
}

export function makeScope(route, db, doc) {
  if (route === 'sql') return { route, db_id: db, doc_ids: [] };
  if (route === 'hybrid') return { route, db_id: 'chinook', doc_ids: doc ? [doc] : [] };
  return { route: 'doc', db_id: null, doc_ids: doc ? [doc] : [] };
}

export function sourceReady(route, db, doc, health, documents) {
  if (health?.status !== 'ok' || health.llm_configured === false) return false;
  if (route === 'sql') return (db === 'chinook' ? health.database_ready : health.aw_database_ready) === true;
  const docsReady = doc ? documents.some(item => item.doc_id === doc && item.ready) : route === 'hybrid' && documents.some(item => item.ready);
  return Boolean(docsReady && (route !== 'hybrid' || health.database_ready === true));
}
