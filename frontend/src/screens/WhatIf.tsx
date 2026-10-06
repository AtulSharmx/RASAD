import { fmt, lakh, plural, shortName, useApi, type Row } from '../api'
import { useApp } from '../App'
import { Chip, ErrorNote, Holder, Skeleton } from '../ui'

const ROWS: [string, string, (v: Row) => string][] = [
  ['posts_at_risk', 'Posts at risk', (k) => `${k.posts_at_risk}${k.at_risk.length ? ` (${k.at_risk.map(shortName).join(', ')})` : ''}`],
  ['heli_sorties', 'Helicopter sorties', (k) => fmt(k.heli_sorties)],
  ['heli_hours', 'Helicopter hours', (k) => `${fmt(k.heli_hours, 1)} h`],
  ['drone_sorties', 'Drone sorties', (k) => fmt(k.drone_sorties)],
  ['foot_trips', 'Mule and porter trips', (k) => fmt(k.foot_trips)],
  ['not_moved_kg', 'Cannot move this week', (k) => `${fmt(k.not_moved_kg)} kg`],
  ['cost_inr', 'Cost this week', (k) => lakh(k.cost_inr)],
]

export default function WhatIf() {
  const { mode, route } = useApp()
  const runs = useApi<Row[]>(`scenarios?mode=${mode}`, true)
  if (runs.error) return <div className="page"><ErrorNote error={runs.error} retry={runs.reload} /></div>
  if (!runs.data) return <div className="page"><Skeleton h={420} label="Re-running the plan for each what-if" /></div>
  const sel = runs.data.find((r) => r.id === route[1]) ?? runs.data[0]
  const moved = sel.plan.filter((l: Row) => l.mode !== 'not moved')
  const stuck = sel.plan.filter((l: Row) => l.mode === 'not moved')
  return (
    <div className="page">
      <div className="page-head">
        <h1>What-if</h1>
        <p>One click changes an input, re-runs the point of no return and the plan, and shows before and after.</p>
        <span className="tools"><Chip kind="sim" label="Simulated inputs" /></span>
      </div>
      <div className="tabs" role="tablist" aria-label="Scenarios" style={{ marginBottom: '.8rem' }}>
        {runs.data.map((r) => <a key={r.id} role="tab" href={`#/whatif/${r.id}`} aria-current={r.id === sel.id ? 'page' : undefined} aria-selected={r.id === sel.id}>{r.title}</a>)}
      </div>
      <div className="grid2" style={{ gridTemplateColumns: '1.1fr 1fr', alignItems: 'start' }}>
        <section className="panel" data-demo="whatif-table" aria-label="Before and after">
          <h2>{sel.title}</h2>
          <table className="t">
            <thead><tr><th>This week</th><th className="n">Today's plan</th><th className="n">With this change</th></tr></thead>
            <tbody>
              {ROWS.map(([key, label, show]) => {
                const changed = JSON.stringify(sel.before[key]) !== JSON.stringify(sel.after[key])
                return (
                  <tr key={key} className="wi-row">
                    <td>{label}</td>
                    <td className="n">{show(sel.before)}</td>
                    <td className="n"><span key={sel.id} className={`flip${changed ? ' changed' : ''}`}>{show(sel.after)}</span></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <ul style={{ margin: '.6rem 0 0', paddingLeft: '1.1rem' }}>
            {sel.changes.filter((c: string) => c.startsWith('New posts') || c.startsWith('Cost is lower')).map((c: string) => <li key={c}><b>{c}</b></li>)}
          </ul>
        </section>
        <section className="panel" aria-label="Plan with this change">
          <h2>The plan with this change</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '.4rem' }}>
            {moved.map((l: Row) => (
              <div key={l.key} className="strip" style={{ gridTemplateColumns: '3.6rem 1fr' }}>
                <Holder mode={l.mode} />
                <div style={{ padding: '.35rem .6rem' }}>
                  <b style={{ font: '700 1.1rem var(--cond)' }}>{shortName(l.post_name)}, {l.label.toLowerCase()}</b>{' '}
                  <span>{l.qty_text}, {plural(l.trips, l.mode === 'helicopter' || l.mode === 'drone' ? 'sortie' : 'trip')}, {l.when}</span>
                </div>
              </div>
            ))}
            {stuck.map((l: Row) => <p key={l.key} className="urgent-text" style={{ margin: 0 }}><b>Cannot move this week:</b> {l.qty_text} {l.label.toLowerCase()} for {shortName(l.post_name)}.</p>)}
          </div>
        </section>
      </div>
    </div>
  )
}
