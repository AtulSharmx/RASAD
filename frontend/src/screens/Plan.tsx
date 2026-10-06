import { useState } from 'react'
import { Check, Pencil, X } from 'lucide-react'
import { api, day, fmt, lakh, rupee, shortName, useApi, type Row } from '../api'
import { useApp, type Role } from '../App'
import { Badge, Chip, Drone, ErrorNote, Helicopter, Holder, Skeleton } from '../ui'

const CAN = { approve: ['Commander'], reject: ['Commander'], modify: ['Commander', 'Logistics Officer'] } as Record<string, Role[]>

function LineStrip({ l, onDecide }: { l: Row; onDecide: (l: Row, action: string, kg?: number) => Promise<void> }) {
  const { role } = useApp()
  const [editing, setEditing] = useState(false)
  const [kg, setKg] = useState(String(l.kg))
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const act = async (action: string, q?: number) => {
    setBusy(true); setErr(null)
    try { await onDecide(l, action, q); setEditing(false) } catch (e) { setErr(String((e as Error).message)) } finally { setBusy(false) }
  }
  const moved = l.mode !== 'not moved'
  const deny = (a: string) => (CAN[a].includes(role) ? undefined : `Only the ${CAN[a].join(' or ')} can ${a}`)
  return (
    <article className={`strip plan-strip ${l.priority === 'urgent' ? 'urgent' : ''}`} data-demo={`plan-${l.post}-${l.mode}`}>
      <Holder mode={moved ? l.mode : undefined} />
      <div className="cells">
        <div className="cell who"><span className="v">{shortName(l.post_name)}</span><span className="k">{l.label}{l.from ? `, from ${l.from}` : ''}</span></div>
        <div className="cell"><span className="k">Load</span><span className="v" style={{ fontSize: '1.25rem' }}>{l.qty_text}</span></div>
        <div className="cell"><span className="k">{moved ? (l.mode === 'helicopter' || l.mode === 'drone' ? `${l.trips} sortie${l.trips === 1 ? '' : 's'}` : `${l.trips} trip${l.trips === 1 ? '' : 's'}`) : 'Status'}</span><span className="v" style={{ fontSize: '1.25rem' }}>{moved ? l.when : 'Not moved'}</span></div>
        <div className="cell"><span className="k">Cost</span><span className="v" style={{ fontSize: '1.25rem' }}>{moved ? lakh(l.cost_inr) : '–'}</span></div>
        <div className="why"><div style={{ flex: 1 }}>
          <p>{rupee(l.reason)}</p>
          {l.mode === 'drone' && l.schedule?.length > 0 && <div className="schedule">{l.schedule.map((s: Row) => `${day(s.date)}: ${s.trips} sorties, ${fmt(s.kg)} kg`).join('; ')}</div>}
          <div className="assume" style={{ marginTop: '.35rem' }}>
            {l.assumptions.map((a: Row) => <Chip key={a.name} kind={a.tag.startsWith('PLACEHOLDER') ? 'ph' : 'real'} label={`${a.name}: ${rupee(a.value)}`}>{a.tag}</Chip>)}
          </div>
        </div></div>
        {moved && (
          <div className="actions">
            {l.status !== 'pending' && <span className={`stamp ${l.status}`}>{l.status === 'approved' ? <Check /> : l.status === 'rejected' ? <X /> : <Pencil />}
              {l.status[0].toUpperCase() + l.status.slice(1)}{l.status === 'modified' || (l.status === 'approved' && l.decided_kg !== l.kg) ? `: ${fmt(l.decided_kg)} kg` : ''}</span>}
            <span style={{ flex: 1 }} />
            {editing ? (
              <span className="modify">
                <label>New quantity <input type="number" min={0} value={kg} onChange={(e) => setKg(e.target.value)} aria-label="New quantity in kg" /> kg</label>
                <button className="btn btn-ink btn-sm" disabled={busy || kg === '' || Number(kg) < 0} onClick={() => act('modify', Number(kg))}>Save change</button>
                <button className="btn btn-line btn-sm" onClick={() => setEditing(false)}>Cancel</button>
              </span>
            ) : <>
              <button className="btn btn-approve btn-sm" disabled={busy || !!deny('approve') || l.status === 'approved'} title={deny('approve')} onClick={() => act('approve')} data-demo={l.post === 'PD' && l.mode === 'drone' ? 'approve' : undefined}><Check />Approve</button>
              <button className="btn btn-line btn-sm" disabled={busy || !!deny('modify')} title={deny('modify')} onClick={() => setEditing(true)}><Pencil />Modify</button>
              <button className="btn btn-reject btn-sm" disabled={busy || !!deny('reject') || l.status === 'rejected'} title={deny('reject')} onClick={() => act('reject')}><X />Reject</button>
            </>}
            {err && <span className="urgent-text" role="alert">{err}</span>}
          </div>
        )}
      </div>
    </article>
  )
}

export default function Plan() {
  const { mode, role } = useApp()
  const plan = useApi(`plan?mode=${mode}`)
  const decide = async (l: Row, action: string, kg?: number) => {
    await api(`plan/decision?mode=${mode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: l.key, action, role, user: `Demo ${role}`, kg: kg ?? null, note: '' }) })
    plan.reload()
  }
  if (plan.error) return <div className="page"><ErrorNote error={plan.error} retry={plan.reload} /></div>
  if (!plan.data) return <div className="page"><Skeleton h={80} /><div style={{ height: 10 }} /><Skeleton h={420} label="Working out the plan" /></div>
  const d = plan.data
  const lines: Row[] = d.lines
  const heli = lines.filter((l) => l.mode === 'helicopter').reduce((s, l) => s + l.trips, 0)
  return (
    <div className="page">
      <div className="page-head">
        <h1>Mixed-fleet plan, next 7 days</h1>
        <p>Which mode carries which load. Road loads always leave before their last road day. Total {lakh(d.total_cost_inr)}, {heli} helicopter sorties.</p>
        <span className="tools"><Badge status={role === 'Commander' ? 'approved' : 'pending'} text={role === 'Commander' ? 'You can approve' : `${role}: ${role === 'Post QM' ? 'view only' : 'can modify'}`} /></span>
      </div>
      <div className="panel" style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '.7rem', padding: '.5rem .8rem', flexWrap: 'wrap' }} aria-label="Flying weather this week">
        <b style={{ font: '700 1.05rem var(--cond)' }}>Flying weather <Chip kind="sim" label="Simulated outlook">Demo weather after 4 Oct 2026 is copied from Oct 2021 (a real early-snow year). Switch to Live for the real 16-day forecast.</Chip></b>
        {d.horizon.map((dt: string) => {
          const w = d.weather[dt]
          return <span key={dt} title={w.wx} style={{ display: 'inline-flex', gap: '.35rem', alignItems: 'center', font: '600 .95rem var(--text)' }}>
            {day(dt)}
            <span className={w.heli ? 'ok-text' : 'urgent-text'} aria-label={`helicopter ${w.heli ? 'can fly' : 'grounded'}`}><Helicopter size={18} /></span>
            <span className={w.drone ? 'ok-text' : 'urgent-text'} aria-label={`drone ${w.drone ? 'can fly' : 'grounded'}`}><Drone size={18} /></span>
            {(!w.heli || !w.drone) && <small className="urgent-text">{!w.heli ? 'no heli' : 'no drone'}</small>}
          </span>
        })}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '.55rem' }}>
        {lines.map((l) => <LineStrip key={l.key} l={l} onDecide={decide} />)}
      </div>
      {d.watch.length > 0 && <p className="muted">On watch, nothing to send this week: {d.watch.map((w: Row) => `${w.post} ${w.class.toLowerCase()} (last road day ${day(w.last_safe_dispatch)})`).join(', ')}.</p>}
    </div>
  )
}
