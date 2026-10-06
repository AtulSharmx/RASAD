// Design-direction mock only (the real app is React). Shared data loading and map layers.
const api = (p) => fetch('/api/' + p).then((r) => { if (!r.ok) throw new Error(p + ' ' + r.status); return r.json(); });

async function loadAll() {
  const [health, sector, terrain, pnr, plan, fc, sources] = await Promise.all(
    ['health', 'sector', 'terrain', 'pnr', 'plan', 'forecast', 'sources'].map(api));
  return { health, sector, terrain, pnr, plan, fc, sources };
}

const RANK = { passed: 0, urgent: 1, watch: 2, margin: 3, stocked: 4 };
const fmt = (n, d = 0) => Number(n).toLocaleString('en-IN', { maximumFractionDigits: d, minimumFractionDigits: d });
const day = (iso) => new Date(iso + 'T00:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });

// worst PNR item per post, plus that post's plan lines and forecast cover
function postSummaries(d) {
  const nodes = Object.fromEntries(d.sector.nodes.map((n) => [n.id, n]));
  const out = {};
  for (const i of d.pnr.items) {
    const cur = out[i.post];
    if (!cur || RANK[i.status] < RANK[cur.item.status]) out[i.post] = { item: i };
  }
  for (const [post, s] of Object.entries(out)) {
    s.node = nodes[post];
    s.lines = d.plan.lines.filter((l) => l.post === post);
    s.cover = d.fc.cover.find((c) => c.post === post && c.class === s.item.class);
  }
  return out;
}

function grid(t) {
  const cols = Math.round((t.lon1 - t.lon0) / t.step) + 1, rows = Math.round((t.lat1 - t.lat0) / t.step) + 1;
  const v = new Float32Array(cols * rows);
  for (const [lat, lon, e] of t.points) v[Math.round((lat - t.lat0) / t.step) * cols + Math.round((lon - t.lon0) / t.step)] = e;
  return { cols, rows, v, ...t };
}

// shaded relief from the real DEM grid; tint(elev) -> [r,g,b]
function reliefOverlay(g, tint, strength = 0.5) {
  const c = document.createElement('canvas');
  c.width = g.cols; c.height = g.rows;
  const ctx = c.getContext('2d'), img = ctx.createImageData(g.cols, g.rows);
  const dx = g.step * 111320 * Math.cos((g.lat0 + g.lat1) / 2 * Math.PI / 180), dy = g.step * 110540;
  const at = (r, k) => g.v[Math.max(0, Math.min(g.rows - 1, r)) * g.cols + Math.max(0, Math.min(g.cols - 1, k))];
  const az = 315 * Math.PI / 180, alt = 45 * Math.PI / 180;
  for (let r = 0; r < g.rows; r++) for (let k = 0; k < g.cols; k++) {
    const zx = (at(r, k + 1) - at(r, k - 1)) / (2 * dx), zy = (at(r + 1, k) - at(r - 1, k)) / (2 * dy);
    const slope = Math.atan(Math.hypot(zx, zy) * 1.6), aspect = Math.atan2(zy, -zx);
    const hs = Math.max(0, Math.cos(alt) * Math.cos(slope) + Math.sin(alt) * Math.sin(slope) * Math.cos(az - aspect));
    const [R, G, B] = tint(at(r, k)), f = 1 - strength + strength * hs;
    const i = ((g.rows - 1 - r) * g.cols + k) * 4;
    img.data[i] = R * f; img.data[i + 1] = G * f; img.data[i + 2] = B * f; img.data[i + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  const h = g.step / 2;
  return L.imageOverlay(c.toDataURL(), [[g.lat0 - h, g.lon0 - h], [g.lat1 + h, g.lon1 + h]], { className: 'relief' });
}

function contourLayer(g, interval, style) {
  const lo = Math.ceil(Math.min(...g.v) / interval) * interval, hi = Math.max(...g.v);
  const th = []; for (let x = lo; x <= hi; x += interval) th.push(x);
  const polys = d3.contours().size([g.cols, g.rows]).thresholds(th)(Array.from(g.v));
  const toLL = ([x, y]) => [g.lon0 + (x - 0.5) * g.step, g.lat0 + (y - 0.5) * g.step];
  const feats = polys.map((p) => ({ type: 'Feature', properties: { value: p.value },
    geometry: { type: 'MultiLineString', coordinates: p.coordinates.flat().map((ring) => ring.map(toLL)) } }));
  return L.geoJSON({ type: 'FeatureCollection', features: feats }, { style, interactive: false });
}

function routeCoords(d, link) {
  const n = Object.fromEntries(d.sector.nodes.map((x) => [x.id, x]));
  const p = Object.fromEntries(d.sector.passes.map((x) => [x.id, x]));
  const pts = [n[link.from_node]];
  if (link.pass) pts.push(p[link.pass]);
  pts.push(n[link.to_node]);
  return pts.map((x) => [x.lat, x.lon]);
}

function baseMap(el, d) {
  const g = grid(d.terrain);
  const map = L.map(el, { zoomControl: false, attributionControl: false, zoomSnap: 0.1, zoomDelta: 0.5 });
  // zoom so the real terrain fills the whole frame (no blank margins), centred on the sector
  const terrainBounds = L.latLngBounds([[g.lat0, g.lon0], [g.lat1, g.lon1]]);
  map.setView([34.08, 76.98], map.getBoundsZoom(terrainBounds, true));
  map.setMaxBounds(terrainBounds);
  return { map, g };
}

// links between two real towns are already drawn from OpenStreetMap; draw only the forward network
const forwardLinks = (d) => {
  const real = new Set(d.sector.nodes.filter((n) => !n.fictional).map((n) => n.id));
  return d.sector.links.filter((l) => !(real.has(l.from_node) && real.has(l.to_node)));
};
