import { useState } from 'react'
import { day, fmt, type Row } from './api'

const W = 680, H = 230, PAD = { l: 52, r: 16, t: 14, b: 30 }
const iw = W - PAD.l - PAD.r, ih = H - PAD.t - PAD.b

function ticks(max: number, n = 4) {
  const raw = max / n, mag = 10 ** Math.floor(Math.log10(raw || 1))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? raw
  return Array.from({ length: Math.floor(max / step) + 1 }, (_, i) => i * step)
}

/* Daily use: actual history (ink line) then forecast P50 (ink, dashed) inside its calibrated P10-P90 band. */
export function BandChart({ actual, forecast, unit }: { actual: Row[]; forecast: Row[]; unit: string }) {
  const [hover, setHover] = useState<number | null>(null)
  const pts = [...actual.map((a) => ({ date: a.date.slice(0, 10), a: a.qty })), ...forecast.map((f) => ({ date: f.date.slice(0, 10), lo: f.p10, mid: f.p50, hi: f.p90 }))]
  if (!pts.length) return null
  const max = Math.max(...pts.map((p: Row) => p.hi ?? p.a)) * 1.08
  const x = (i: number) => PAD.l + (i / (pts.length - 1)) * iw
  const y = (v: number) => PAD.t + ih - (v / max) * ih
  const fStart = actual.length
  const line = (key: string, from: number, to: number) => pts.slice(from, to).map((p: Row, k) => `${k ? 'L' : 'M'}${x(from + k).toFixed(1)},${y(p[key]).toFixed(1)}`).join('')
  const band = pts.slice(fStart).map((p: Row, k) => `${k ? 'L' : 'M'}${x(fStart + k)},${y(p.hi)}`).join('') +
    pts.slice(fStart).reverse().map((p: Row, k) => `L${x(pts.length - 1 - k)},${y(p.lo)}`).join('') + 'Z'
  const h = hover !== null ? pts[hover] as Row : null
  return (
    <div style={{ position: 'relative' }}>
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Daily use in ${unit}: last ${actual.length} days and the next ${forecast.length} days forecast with an 80% band`}
        onMouseMove={(e) => { const r = e.currentTarget.getBoundingClientRect(); const i = Math.round(((e.clientX - r.left) / r.width * W - PAD.l) / iw * (pts.length - 1)); setHover(Math.max(0, Math.min(pts.length - 1, i))) }}
        onMouseLeave={() => setHover(null)}>
        {ticks(max).map((t) => <g key={t}><line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} stroke="#e1e5df" /><text x={PAD.l - 6} y={y(t) + 4} textAnchor="end">{fmt(t)}</text></g>)}
        <text x={PAD.l - 6} y={PAD.t - 2} textAnchor="end">{unit}/day</text>
        <path d={band} fill="#2d5fc4" opacity={0.16} />
        <path d={line('a', 0, fStart)} fill="none" stroke="#16212b" strokeWidth={2} />
        <path d={line('mid', fStart, pts.length)} fill="none" stroke="#16212b" strokeWidth={2} strokeDasharray="5 4" />
        <line x1={x(fStart)} x2={x(fStart)} y1={PAD.t} y2={PAD.t + ih} stroke="#16212b" strokeWidth={1.5} />
        <text className="lbl" x={x(fStart) + 6} y={PAD.t + 12}>Today</text>
        <text className="lbl" x={x(fStart) + 6} y={PAD.t + 28} style={{ fill: '#2d5fc4' }}>Forecast, 80% band</text>
        {[0, fStart, pts.length - 1].map((i) => <text key={i} x={x(i)} y={H - 8} textAnchor={i === 0 ? 'start' : i === pts.length - 1 ? 'end' : 'middle'}>{day(pts[i].date)}</text>)}
        {h && <><line x1={x(hover!)} x2={x(hover!)} y1={PAD.t} y2={PAD.t + ih} stroke="#3a4651" strokeDasharray="3 3" />
          <circle cx={x(hover!)} cy={y(h.a ?? h.mid)} r={5} fill="#16212b" stroke="#fffef9" strokeWidth={2} /></>}
      </svg>
      {h && <div className="tip" style={{ left: `${(x(hover!) / W) * 100}%`, top: 4, transform: 'translateX(-50%)' }}>
        {day(h.date)}: {h.a !== undefined ? `${fmt(h.a, 1)} ${unit} used` : `${fmt(h.mid, 1)} ${unit} expected (${fmt(h.lo, 1)}–${fmt(h.hi, 1)})`}</div>}
    </div>
  )
}

/* Chance the ground route is closed by each date (31 real winters replayed), with the 80% line. */
export function ClosureCurve({ curve, lastSafe, label }: { curve: Row[]; lastSafe?: string; label: string }) {
  const [hover, setHover] = useState<number | null>(null)
  const pts = curve.slice(0, 75)
  const x = (i: number) => PAD.l + (i / (pts.length - 1)) * iw
  const y = (p: number) => PAD.t + ih - p * ih
  const d = pts.map((p, i) => `${i ? `L${x(i)},${y(pts[i - 1].p_closed)}L` : 'M'}${x(i)},${y(p.p_closed)}`).join('')
  const ls = lastSafe ? pts.findIndex((p) => p.date >= lastSafe) : -1
  const h = hover !== null ? pts[hover] : null
  return (
    <div style={{ position: 'relative' }}>
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${label}: chance the ground route is closed by each date`}
        onMouseMove={(e) => { const r = e.currentTarget.getBoundingClientRect(); const i = Math.round(((e.clientX - r.left) / r.width * W - PAD.l) / iw * (pts.length - 1)); setHover(Math.max(0, Math.min(pts.length - 1, i))) }}
        onMouseLeave={() => setHover(null)}>
        {[0, .2, .5, .8, 1].map((t) => <g key={t}><line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} stroke={t === .2 ? '#b8232b' : '#e1e5df'} strokeDasharray={t === .2 ? '6 4' : undefined} /><text x={PAD.l - 6} y={y(t) + 4} textAnchor="end">{t * 100}%</text></g>)}
        <text className="lbl" x={W - PAD.r} y={y(.2) - 6} textAnchor="end" style={{ fill: '#b8232b' }}>20% chance closed = 80% still open</text>
        <path d={d} fill="none" stroke="#16212b" strokeWidth={2.5} />
        {ls > 0 && <><line x1={x(ls)} x2={x(ls)} y1={PAD.t} y2={PAD.t + ih} stroke="#b8232b" strokeWidth={2} />
          <text className="lbl" x={x(ls) + 6} y={PAD.t + 12} style={{ fill: '#b8232b' }}>Last road day {day(pts[ls].date)}</text></>}
        {[0, Math.floor(pts.length / 2), pts.length - 1].map((i) => <text key={i} x={x(i)} y={H - 8} textAnchor={i === 0 ? 'start' : i === pts.length - 1 ? 'end' : 'middle'}>{day(pts[i].date)}</text>)}
        {h && <circle cx={x(hover!)} cy={y(h.p_closed)} r={5} fill="#16212b" stroke="#fffef9" strokeWidth={2} />}
      </svg>
      {h && <div className="tip" style={{ left: `${(x(hover!) / W) * 100}%`, top: 4, transform: 'translateX(-50%)' }}>
        By {day(h.date)}: {Math.round(h.p_closed * 100)}% chance the route is closed</div>}
    </div>
  )
}
