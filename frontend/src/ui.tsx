import { useLayoutEffect, useRef, useState, type ReactNode, type SVGProps } from 'react'
import { createPortal } from 'react-dom'
import { CheckCircle2, CircleDashed, Clock, Database, FileWarning, Footprints, OctagonAlert, PawPrint, Truck } from 'lucide-react'
import type { Row } from './api'

/* Helicopter and drone glyphs drawn in Lucide's grammar (24 grid, 2px round stroke): Lucide has neither. */
type IconProps = SVGProps<SVGSVGElement> & { size?: number }
const base = (p: IconProps) => ({ width: p.size ?? 24, height: p.size ?? 24, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor',
  strokeWidth: 2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, ...p, size: undefined })
export const Helicopter = (p: IconProps) => (
  <svg {...base(p)}><path d="M3 5h16M11 5v3" /><path d="M5 12a6 4 0 0 1 6-4h3a5 5 0 0 1 5 5v1H8a3 3 0 0 1-3-2Z" /><path d="M19 13h3M22 10v6M9 18v2M15 18v2M6 20h12" /></svg>
)
export const Drone = (p: IconProps) => (
  <svg {...base(p)}><circle cx="5" cy="5" r="2.5" /><circle cx="19" cy="5" r="2.5" /><circle cx="5" cy="19" r="2.5" /><circle cx="19" cy="19" r="2.5" />
    <path d="M7 7l3 3M17 7l-3 3M7 17l3-3M17 17l-3-3" /><rect x="9.5" y="9.5" width="5" height="5" rx="1" /></svg>
)

export const MODES: Record<string, { cls: string; label: string; Icon: (p: IconProps) => ReactNode }> = {
  truck: { cls: 'road', label: 'Truck', Icon: Truck }, jeep: { cls: 'road', label: 'Jeep', Icon: Truck },
  mule: { cls: 'foot', label: 'Mule', Icon: PawPrint }, porter: { cls: 'foot', label: 'Porter', Icon: Footprints },
  helicopter: { cls: 'heli', label: 'Heli', Icon: Helicopter }, drone: { cls: 'drone', label: 'Drone', Icon: Drone },
}

export function Holder({ mode }: { mode?: string }) {
  const m = mode ? MODES[mode] : undefined
  if (!m) return <div className="holder none"><FileWarning /><span>None</span></div>
  return <div className={`holder ${m.cls}`}><m.Icon /><span>{m.label}</span></div>
}

/* ---- provenance chips with a popover (hover, focus or click) ---- */
const SIM = 'Simulated: military data is classified; in deployment this comes from CICG via adapters.'
const TITLES = { real: 'Real data', sim: 'Simulated', ph: 'PLACEHOLDER' }

export function Chip({ kind, label, children }: { kind: 'real' | 'sim' | 'ph'; label?: string; children?: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null)
  const ref = useRef<HTMLButtonElement>(null)
  useLayoutEffect(() => {
    if (!open || !ref.current) return
    const r = ref.current.getBoundingClientRect()
    setPos({ x: Math.min(r.left, window.innerWidth - 360), y: r.bottom + 6 > window.innerHeight - 160 ? r.top - 8 : r.bottom + 6 })
  }, [open])
  const body = children ?? (kind === 'sim' ? SIM : kind === 'real' ? 'Real public data, cached on this machine.' : 'Not from a public source; listed in docs/PLACEHOLDERS.md.')
  return (
    <>
      <button ref={ref} type="button" className={`chip ${kind}`} aria-expanded={open}
        onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)} onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}
        onClick={(e) => { e.preventDefault(); e.stopPropagation(); setOpen((o) => !o) }}>
        {kind === 'real' && <Database />}{label ?? TITLES[kind]}
      </button>
      {open && pos && createPortal(
        <div className="pop" role="tooltip" style={{ left: pos.x, top: pos.y, transform: pos.y < (ref.current?.getBoundingClientRect().top ?? 0) ? 'translateY(-100%)' : undefined }}>
          <b>{TITLES[kind]}</b>{body}
        </div>, document.body)}
    </>
  )
}

const STATUS: Record<string, [string, typeof CheckCircle2]> = {
  passed: ['Air only', OctagonAlert], urgent: ['Urgent', OctagonAlert], watch: ['Watch', Clock],
  margin: ['Within margin', CircleDashed], stocked: ['Stocked', CheckCircle2],
  approved: ['Approved', CheckCircle2], rejected: ['Rejected', OctagonAlert], modified: ['Modified', CircleDashed], pending: ['Pending', Clock],
  ok: ['Healthy', CheckCircle2], warning: ['Warning', Clock], stale: ['Stale', Clock], error: ['Error', OctagonAlert],
}
export function Badge({ status, text }: { status: string; text?: string }) {
  const [label, Icon] = STATUS[status] ?? [status, CircleDashed]
  return <span className={`badge ${status}`}><Icon />{text ?? label}</span>
}

export function Skeleton({ h = 120, label = 'Loading' }: { h?: number; label?: string }) {
  return <div className="skel" style={{ height: h }} role="status" aria-label={label} />
}

export function ErrorNote({ error, retry }: { error: string; retry?: () => void }) {
  return (
    <div className="notice err" role="alert">
      <OctagonAlert /><div><b>Could not load this screen.</b> {error}. The backend may still be computing; it runs on this laptop at 127.0.0.1:8000.</div>
      {retry && <button className="btn btn-line btn-sm" onClick={retry}>Try again</button>}
    </div>
  )
}

export const costChip = (i: Row) => <Chip kind="ph" label="PLACEHOLDER cost">{i.cost_basis}</Chip>
