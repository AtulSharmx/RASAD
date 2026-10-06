import { useState } from 'react'
import { day, fmt, lakh, rupee, shortName, useApi, type Row } from '../api'
import { useApp } from '../App'
import { ClosureCurve } from '../charts'
import { Badge, Chip, ErrorNote, Holder, Skeleton } from '../ui'

export default function Pnr() {
  const { mode } = useApp()
  const pnr = useApi(`pnr?mode=${mode}`, true)
  const [sel, setSel] = useState<string | null>(null)
  if (pnr.error) return <div className="page"><ErrorNote error={pnr.error} retry={pnr.reload} /></div>
  if (!pnr.data) return <div className="page"><Skeleton h={500} label="Replaying 31 winters" /></div>

  const items: Row[] = pnr.data.items.filter((i: Row) => ['passed', 'urgent', 'watch'].includes(i.status))
  const stocked = pnr.data.items.length - items.length
  const pick = items.find((i) => `${i.post}:${i.class}` === sel) ?? items.find((i) => i.post === 'PA') ?? items[0]

  return (
    <div className="page">
      <div className="page-head">
        <h1>Point of no return</h1>
        <p>The last day a convoy can still get through, learned from real closure dates and {pnr.data.winters_replayed} real winters. After it, only air.</p>
      </div>

      <div className="grid2" style={{ gridTemplateColumns: '1fr 1.25fr', alignItems: 'start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
          {items.map((i) => {
            const passed = i.status === 'passed'
            const on = pick && i.post === pick.post && i.class === pick.class
            return (
              <button key={i.post + i.class} className="strip-link" style={{ border: 0, padding: 0, background: 'none', textAlign: 'left', cursor: 'pointer', outline: on ? '3px solid var(--ink)' : undefined }}
                onClick={() => setSel(`${i.post}:${i.class}`)} data-demo={`pnr-${i.post}`} aria-pressed={!!on}>
                <article className={`strip ${i.status}`}>
                  <Holder mode={passed ? 'helicopter' : i.dispatch_by.includes('mule') ? 'mule' : i.dispatch_by.includes('jeep') ? 'jeep' : 'truck'} />
                  <div className="cells">
                    <div className="cell who"><span className="v">{shortName(i.post_name)}</span><span className="k">{i.label}</span></div>
                    <div className="cell"><span className="k">Closes (20–80%)</span><span className="v" style={{ fontSize: '1.2rem' }}>{passed ? 'Closed now' : `${day(i.closure_p20)}–${day(i.closure_p80)}`}</span></div>
                    <div className="cell due"><span className="k">{passed ? 'Ground route' : `Last ${i.dispatch_by} day (80%)`}</span><span className="v">{passed ? 'Closed' : day(i.last_safe_dispatch)}</span></div>
                    <div className="why"><p>{passed ? `Ground route closed: air only now, ~${i.cost_multiple}× the road cost.` : `After ${day(i.last_safe_dispatch)}: air only, ~${i.cost_multiple}× the road cost, ${i.heli_sorties} helicopter sorties.`}</p><span className="chips"><Chip kind="ph" label="PLACEHOLDER cost">{rupee(i.cost_basis)}</Chip></span></div>
                  </div>
                </article>
              </button>
            )
          })}
          <p className="muted" style={{ margin: '.2rem' }}>{stocked} other items are stocked until their routes reopen.</p>
        </div>

        {pick && (
          <section className="panel" aria-label="Closure detail">
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '.6rem', flexWrap: 'wrap' }}>
              <h2 style={{ margin: 0 }}>{pick.post_name}, {pick.label.toLowerCase()}</h2><Badge status={pick.status} />
            </div>
            <ClosureCurve curve={pnr.data.curves[pick.post]} lastSafe={pick.status === 'passed' ? undefined : pick.last_safe_dispatch} label={pick.post_name} />
            <div className="facts" style={{ marginTop: '.4rem' }}>
              <div className="fact"><span className="k">Short until reopening ({day(pick.reopen_p80)})</span><span className="v">{fmt(pick.shortfall)} <small>{pick.unit}</small></span></div>
              <div className="fact"><span className="k">By helicopter instead</span><span className="v">{pick.heli_sorties} <small>sorties, {fmt(pick.heli_hours, 1)} h</small></span></div>
              <div className="fact"><span className="k">Air cost</span><span className="v">{lakh(pick.air_cost_inr_lakh * 1e5)}</span></div>
              <div className="fact"><span className="k">Air vs road</span><span className="v">~{pick.cost_multiple}×</span></div>
            </div>
            <p style={{ margin: '.5rem 0 .4rem', fontSize: '.95rem' }}>
              {rupee(pick.cost_basis.split('; PLACEHOLDER')[0])}. <Chip kind="ph">{pick.cost_inputs.source} Rates: truck ₹{pick.cost_inputs.rates.truck_inr_per_kg_km.value}/kg-km, helicopter ₹{fmt(pick.cost_inputs.rates.heli_inr_per_hour.value)}/h. Helicopter payload at this height ({pick.heli_payload_kg} kg) is also a placeholder.</Chip>
            </p>
            <p className="muted" style={{ margin: 0, fontSize: '.92rem' }}>Only {pick.flyable_winter_pct}% of past winter days were inside the helicopter weather limits, so air delivery after the deadline is also a weather risk.</p>
          </section>
        )}
      </div>

      <section className="panel" style={{ marginTop: '.8rem' }} aria-label="Rear axes">
        <h2>Rear axes into Ladakh <Chip kind="real" label="Real dates and weather">Rule fitted on real closure dates (docs/FACTS.md), replayed on Open-Meteo ERA5 weather since 1995.</Chip></h2>
        <table className="t">
          <thead><tr><th>Axis</th><th>Likely closes (20%, 50%, 80%)</th><th>Reopens (late case)</th><th>How it closes</th><th className="n">Error on past winters</th></tr></thead>
          <tbody>
            {pnr.data.axes.map((a: Row) => (
              <tr key={a.id}>
                <td><b>{a.name.replace(' (real)', '')}</b></td>
                <td>{day(a.closure_p20)}, {day(a.closure_p50)}, {day(a.closure_p80)}</td>
                <td>{day(a.reopen_p80)}</td>
                <td>{a.rule.T_c !== null ? `cold: 7-day average ≤ ${a.rule.T_c} °C` : ''}{a.rule.T_c !== null && a.rule.D_cm ? ', or ' : ''}{a.rule.D_cm ? `${a.rule.C_cm ? `${a.rule.C_cm} cm of snow so far and ` : ''}${a.rule.D_cm} cm in 3 days` : ''}</td>
                <td className="n">±{a.rule.loo_error_days} days <span className="muted">({a.rule.years} winters)</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
