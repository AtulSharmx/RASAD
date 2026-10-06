import { useEffect, useMemo, useRef } from 'react'
import L from 'leaflet'
import { contours } from 'd3-contour'
import { fmt, shortName, type Row } from './api'
import { Chip } from './ui'

type Props = {
  sector: Row; terrain: Row; status: Record<string, string>; risk: string[]
  droneLegs?: { from: string; to: string }[]; onPost?: (id: string) => void; focus?: string
}

function grid(t: Row) {
  const cols = Math.round((t.lon1 - t.lon0) / t.step) + 1, rows = Math.round((t.lat1 - t.lat0) / t.step) + 1
  const v = new Float32Array(cols * rows)
  for (const [lat, lon, e] of t.points) v[Math.round((lat - t.lat0) / t.step) * cols + Math.round((lon - t.lon0) / t.step)] = e
  return { cols, rows, v, lat0: t.lat0, lon0: t.lon0, lat1: t.lat1, lon1: t.lon1, step: t.step as number }
}
type Grid = ReturnType<typeof grid>

// pale shaded relief from the real Copernicus DEM grid
function relief(g: Grid) {
  const c = document.createElement('canvas')
  c.width = g.cols; c.height = g.rows
  const ctx = c.getContext('2d')!, img = ctx.createImageData(g.cols, g.rows)
  const dx = g.step * 111320 * Math.cos(((g.lat0 + g.lat1) / 2) * Math.PI / 180), dy = g.step * 110540
  const at = (r: number, k: number) => g.v[Math.max(0, Math.min(g.rows - 1, r)) * g.cols + Math.max(0, Math.min(g.cols - 1, k))]
  const az = (315 * Math.PI) / 180, alt = (45 * Math.PI) / 180
  for (let r = 0; r < g.rows; r++) for (let k = 0; k < g.cols; k++) {
    const zx = (at(r, k + 1) - at(r, k - 1)) / (2 * dx), zy = (at(r + 1, k) - at(r - 1, k)) / (2 * dy)
    const slope = Math.atan(Math.hypot(zx, zy) * 1.5), aspect = Math.atan2(zy, -zx)
    const hs = Math.max(0, Math.cos(alt) * Math.cos(slope) + Math.sin(alt) * Math.sin(slope) * Math.cos(az - aspect))
    const t = Math.min(1, Math.max(0, (at(r, k) - 2900) / 3000)), f = 0.62 + 0.38 * hs
    const i = ((g.rows - 1 - r) * g.cols + k) * 4
    img.data[i] = (246 - 22 * t) * f; img.data[i + 1] = (246 - 20 * t) * f; img.data[i + 2] = (238 - 22 * t) * f; img.data[i + 3] = 255
  }
  ctx.putImageData(img, 0, 0)
  const h = g.step / 2
  return L.imageOverlay(c.toDataURL(), [[g.lat0 - h, g.lon0 - h], [g.lat1 + h, g.lon1 + h]], { interactive: false })
}

function contourLayer(g: Grid) {
  const min = Math.min(...g.v), max = Math.max(...g.v), th: number[] = []
  for (let x = Math.ceil(min / 200) * 200; x <= max; x += 200) th.push(x)
  const toLL = ([x, y]: number[]) => [g.lon0 + (x - 0.5) * g.step, g.lat0 + (y - 0.5) * g.step]
  const feats = contours().size([g.cols, g.rows]).thresholds(th)(Array.from(g.v)).map((p) => ({
    type: 'Feature' as const, properties: { value: p.value },
    geometry: { type: 'MultiLineString' as const, coordinates: p.coordinates.flat().map((ring) => ring.map(toLL)) },
  }))
  return L.geoJSON({ type: 'FeatureCollection', features: feats } as never, {
    interactive: false,
    style: (f) => {
      const idx = (f?.properties.value ?? 0) % 1000 === 0
      return { color: '#a8673a', weight: idx ? 1.1 : 0.55, opacity: idx ? 0.62 : 0.4 }
    },
  })
}

const label = (html: string, ax: number, ay: number) => L.divIcon({ className: '', html, iconAnchor: [ax, ay] })

export default function SectorMap({ sector, terrain, status, risk, droneLegs = [], onPost, focus }: Props) {
  const el = useRef<HTMLDivElement>(null)
  const map = useRef<L.Map | null>(null)
  const layer = useRef<L.LayerGroup | null>(null)
  const g = useMemo(() => grid(terrain), [terrain])

  useEffect(() => {
    if (!el.current) return
    const m = L.map(el.current, { zoomControl: false, attributionControl: false, zoomSnap: 0.1, zoomDelta: 0.5, minZoom: 8, maxZoom: 13 })
    const bounds = L.latLngBounds([[g.lat0, g.lon0], [g.lat1, g.lon1]])
    m.setView(bounds.getCenter(), m.getBoundsZoom(bounds, true) + 0.15) // terrain fills the frame at any size
    m.setMaxBounds(bounds.pad(0.02))
    relief(g).addTo(m)
    contourLayer(g).addTo(m)
    L.control.scale({ imperial: false, position: 'bottomright', maxWidth: 160 }).addTo(m)
    L.control.zoom({ position: 'topleft' }).addTo(m)
    layer.current = L.layerGroup().addTo(m)
    map.current = m
    const ro = new ResizeObserver(() => m.invalidateSize())
    ro.observe(el.current)
    return () => { ro.disconnect(); m.remove(); map.current = null }
  }, [g])

  useEffect(() => {
    const lg = layer.current
    if (!lg) return
    lg.clearLayers()
    const nodes: Record<string, Row> = Object.fromEntries(sector.nodes.map((n: Row) => [n.id, n]))
    const passes: Record<string, Row> = Object.fromEntries(sector.passes.map((p: Row) => [p.id, p]))
    const roadStatus: Record<string, string> = Object.fromEntries(sector.roads.map((r: Row) => [r.segment, r.status]))
    for (const f of sector.osm) if (f.kind === 'road') L.polyline(f.geometry, { color: '#8a3a1c', weight: 3.5, opacity: 0.9, interactive: false }).addTo(lg)
    const real = new Set(sector.nodes.filter((n: Row) => !n.fictional).map((n: Row) => n.id))
    for (const l of sector.links) {
      if (real.has(l.from_node) && real.has(l.to_node)) continue // drawn from OpenStreetMap
      const pts = [nodes[l.from_node], ...(l.pass ? [passes[l.pass]] : []), nodes[l.to_node]].map((n) => [n.lat, n.lon] as [number, number])
      const style = { road: { color: '#16212b', weight: 3 }, jeep_track: { color: '#16212b', weight: 2.5, dashArray: '8 5' },
        mule_track: { color: '#6b3d16', weight: 3, dashArray: '2 6' } }[l.mode as 'road']
      const closed = roadStatus[l.id] === 'closed'
      L.polyline(pts, { ...style, ...(closed ? { color: '#b8232b', dashArray: '3 7', weight: 3.5 } : {}), lineCap: 'round', interactive: false }).addTo(lg)
    }
    for (const leg of droneLegs) {
      const a = sector.nodes.find((n: Row) => n.name === leg.from || n.id === leg.from), b = nodes[leg.to]
      if (a && b) L.polyline([[a.lat, a.lon], [b.lat, b.lon]], { color: '#b0428f', weight: 3.5, dashArray: '10 6', interactive: false }).addTo(lg)
    }
    for (const p of sector.passes) {
      L.marker([p.lat, p.lon], { interactive: false, icon: label(`<div class="mpass">▲ ${p.name} ${fmt(p.alt_m)} m</div>`, 6, 9) }).addTo(lg)
    }
    for (const n of sector.nodes) {
      if (n.kind === 'post') {
        const st = status[n.id] ?? 'stocked', k = risk.indexOf(n.id)
        const fill = st === 'stocked' || st === 'margin' ? '#1d6f43' : st === 'watch' ? '#8a5100' : '#b8232b'
        const sq = L.marker([n.lat, n.lon], { keyboard: true, title: `${n.name}: ${st}`, icon: L.divIcon({ className: '', iconSize: [16, 16], iconAnchor: [8, 8],
          html: `<div style="width:16px;height:16px;background:${fill};border:2px solid #fff;outline:1.5px solid #16212b"></div>` }) }).addTo(lg)
        if (onPost) sq.on('click', () => onPost(n.id))
        if (k >= 0) L.marker([n.lat, n.lon], { interactive: false, icon: L.divIcon({ className: '', iconSize: [44, 44], iconAnchor: [22, 22],
          html: `<div class="ring${focus === n.id ? ' hot' : ''}"><b class="num">${k + 1}</b></div>` }) }).addTo(lg)
        L.marker([n.lat, n.lon], { interactive: false, icon: label(`<div class="mlabel">${shortName(n.name)} <small>${fmt(n.alt_m)} m</small></div>`, k >= 0 ? -26 : -12, 10) }).addTo(lg)
      } else if (['roadhead', 'node', 'depot'].includes(n.kind)) {
        L.circleMarker([n.lat, n.lon], { radius: 6, color: '#16212b', weight: 2, fillColor: '#fff', fillOpacity: 1, interactive: false }).addTo(lg)
        L.marker([n.lat, n.lon], { interactive: false, icon: label(`<div class="mlabel">${n.name}</div>`, -10, 10) }).addTo(lg)
      }
    }
  }, [sector, status, risk, droneLegs, onPost, focus])

  return (
    <div className="mapframe">
      <div ref={el} className="map" role="region" aria-label="Map of Sector X with routes, passes and posts" />
      <div className="mapchips">
        <Chip kind="real" label="Real: terrain, roads, passes">Terrain: Copernicus DEM GLO-90 (contours every 200 m). Roads, passes, Leh: OpenStreetMap (ODbL). Cached on this machine; no international boundaries are shown.</Chip>
        <Chip kind="sim" label="Simulated: posts, tracks" />
      </div>
      <div className="legend" aria-label="Map legend">
        <span><i style={{ borderColor: '#8a3a1c' }} />National highway</span><span><i style={{ borderColor: '#16212b' }} />Forward road</span>
        <span><i style={{ borderColor: '#16212b', borderTopStyle: 'dashed' }} />Jeep track</span><span><i style={{ borderColor: '#6b3d16', borderTopStyle: 'dotted' }} />Mule track</span>
        <span><i style={{ borderColor: '#b0428f', borderTopStyle: 'dashed' }} />Drone leg</span><span><i style={{ borderColor: '#b8232b', borderTopStyle: 'dotted' }} />Closed by snow</span>
        <span><i className="sq" style={{ background: '#b8232b', borderTop: '2px solid #fff' }} />At risk (numbered)</span><span><i className="sq" style={{ background: '#1d6f43', borderTop: '2px solid #fff' }} />Stocked</span>
        <span><i style={{ borderColor: '#a8673a', borderTopWidth: 1 }} />Contour 200 m</span>
      </div>
    </div>
  )
}
