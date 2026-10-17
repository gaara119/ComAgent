/** Geometry adapted from the supplied agent-studio-ui dashboard; no DOM or HTML strings. */
export const PALETTE = ['#c9df32', '#28d5a4', '#38b8e8', '#9870ec', '#f2ba65', '#8fb8d4', '#e58db6', '#6ec3bf'];
export const DEFAULT_YAW = -.44;
export const clampYaw = value => Math.max(-.9, Math.min(.45, value));
export function project(x, y, z = 0, yaw = DEFAULT_YAW) {
  const xx = x * Math.cos(yaw) - y * Math.sin(yaw), yy = x * Math.sin(yaw) + y * Math.cos(yaw);
  return [475 + (xx - yy) * .84, 357 + (xx + yy) * .34 - z * .95];
}
export const path = (points, close = true) => points.map((p, i) => (i ? 'L' : 'M') + p.map(n => n.toFixed(2)).join(',')).join(' ') + (close ? 'Z' : '');
function arc(radius, a, b, z, yaw, steps = 36) { return Array.from({ length: steps + 1 }, (_, i) => project(Math.cos(a + (b - a) * i / steps) * radius, Math.sin(a + (b - a) * i / steps) * radius, z, yaw)); }
export function sceneGeometry(rows, kind, yaw = DEFAULT_YAW) {
  const p = (x, y, z = 0) => project(x, y, z, yaw);
  const floor = path([p(-320, -320, -60), p(320, -320, -60), p(320, 320, -60), p(-320, 320, -60)]);
  const grid = Array.from({ length: 7 }, (_, i) => (i - 3) * 80).map(n => path([p(n, -320, -59), p(n, 320, -59)], false) + ' ' + path([p(-320, n, -59), p(320, n, -59)], false));
  const max = Math.max(...rows.map(r => Math.abs(r.value)), 1);
  if (kind === 'ring') {
    const total = rows.reduce((n, r) => n + r.value, 0); let angle = -2.6;
    const faces = rows.map((r, i) => {
      const extent = r.value / total * Math.PI * 2, gap = Math.min(.013, extent / 8), a = angle + gap, b = angle + extent - gap; angle += extent;
      if (r.value <= 0) return null;
      const h = 45 + Math.sqrt(r.value / total) * 140, outer = arc(218, a, b, h, yaw), inner = arc(126, a, b, h, yaw), bottom = arc(218, a, b, 0, yaw), innerBottom = arc(126, a, b, 0, yaw);
      return { i, depth: Math.sin((a + b) / 2 + yaw) + Math.cos((a + b) / 2 + yaw), sides: [path([...outer, ...[...bottom].reverse()]), path([...inner, ...[...innerBottom].reverse()]), path([outer[0], inner[0], innerBottom[0], bottom[0]]), path([outer.at(-1), inner.at(-1), innerBottom.at(-1), bottom.at(-1)])], cap: path([...outer, ...[...inner].reverse()]) };
    }).filter(Boolean).sort((a, b) => a.depth - b.depth);
    return { floor, grid, faces, plinth: path(arc(269, 0, Math.PI * 2, -15, yaw, 90)) };
  }
  const count = rows.length, width = Math.min(68, 430 / Math.max(count, 1) - 10), start = -(count * (width + 13) - 13) / 2;
  if (kind === 'bars') return { floor, grid, faces: rows.map((r, i) => {
    const x = start + i * (width + 13), h = r.value / max * 200, y = -20, d = 75;
    return { i, depth: p(x, 0)[1], cap: path([p(x, y, h), p(x + width, y, h), p(x + width, y + d, h), p(x, y + d, h)]), sides: [path([p(x + width, y, h), p(x + width, y + d, h), p(x + width, y + d), p(x + width, y)]), path([p(x, y + d, h), p(x + width, y + d, h), p(x + width, y + d), p(x, y + d)])], pin: p(x + width / 2, y, h + (h < 0 ? -20 : 20)) };
  }).sort((a, b) => a.depth - b.depth) };
  const points = rows.map((r, i) => p(rows.length === 1 ? 0 : -240 + i * 480 / (rows.length - 1), 0, r.value / max * 200));
  const back = rows.map((r, i) => p(rows.length === 1 ? 0 : -240 + i * 480 / (rows.length - 1), -60, r.value / max * 200));
  return { floor, grid, faces: [], points, ribbon: points.length > 1 ? path([...points, ...[...back].reverse()]) : null, line: path(points, false), baseline: path([p(-270, 0), p(270, 0)], false) };
}
