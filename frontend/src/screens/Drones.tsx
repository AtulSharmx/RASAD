import { useState } from 'react'
import { fmt, lakh, rupee, shortName, useApi, type Row } from '../api'
import { useApp } from '../App'
import { Chip, Drone, ErrorNote, Helicopter, Skeleton } from '../ui'

const BANDS = [['12000_20000ft', '12,000–20,000 ft (15 kg)'], ['6000_12000ft', '6,000–12,000 ft (20 kg)'], ['up_to_6000ft', 'up to 6,000 ft (20 kg)']]

export default function Drones() {
  const { mode } = useApp()
  const [n, setN] = useState(20)
  const [band, setBand] = useState('12000_20000ft')
  const [ask, setAsk] = useState({ n: 20, band: '12000_20000ft' })
  const adv = useApi(`drones?mode=${mode}&n=${ask.n}&band=${ask.band}`, true)
  const a = adv.data
  const best = a?.ranking?.[0]
  const maxSaved = Math.max(1, ...(a?.ranking ?? []).map((r: Row) => r.saved_inr))
  return (
    <div className="page">
      <div className="page-head">
        <h1>Drone advisor</h1>
        <p>If new drones arrive (the Army's 2026 RFI seeks 2,715 in three height bands), where should they be based? Each base is tested by re-running this week's plan.</p>
      </div>
      <form className="panel" style={{ display: 'flex', gap: '1rem', alignItems: 'end', flexWrap: 'wrap', marginBottom: '.8rem' }}
        onSubmit={(e) => { e.preventDefault(); setAsk({ n, band }) }}>
        <label style={{ display: 'grid', gap: '.2rem' }}><span className="k">Drones arriving</span>
          <input type="number" min={1} max={500} value={n} onChange={(e) => setN(Math.max(1, Math.min(500, Number(e.target.value) || 1)))}
            style={{ width: '7rem', padding: '.45rem', border: '1px solid var(--ink)', borderRadius: 6, font: '700 1.2rem var(--cond)' }} /></label>
        <label style={{ display: 'grid', gap: '.2rem' }}><span className="k">Height band (payload)</span>
          <select value={band} onChange={(e) => setBand(e.target.value)} style={{ padding: '.5rem', border: '1px solid var(--ink)', borderRadius: 6 }}>
            {BANDS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select></label>
        <button className="btn btn-ink" type="submit" disabled={!!adv.data === false && !adv.error}>Find the best base</button>
        <Chip kind="real" label="Payload and range: Army RFP/RFI">15 kg at 12,000–20,000 ft and 20 kg below (Army RFP, Tribune, Oct 2022); range 10 km one way (2022–2026 RFIs). Each leg must clear the real terrain (Copernicus DEM) by 400 m.</Chip>
        <Chip kind="ph" label="PLACEHOLDER: batteries, cost">2 batteries per drone, 90 min to recharge, 5 min swap, 8 flying hours a day, ₹1,500 per sortie. Helicopter ₹5.33 lakh/h (The Week 2020).</Chip>
      </form>

      {adv.error && <ErrorNote error={adv.error} retry={adv.reload} />}
      {!a && !adv.error && <Skeleton h={360} label="Testing every base (about 30 seconds the first time)" />}
      {a && best && (
        <>
          <section className="panel" data-demo="drone-headline" style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '1.2rem', alignItems: 'center', marginBottom: '.8rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '.8rem' }}>
              <span className="holder heli" style={{ borderRadius: 6, padding: '.6rem' }}><Helicopter /><span>{a.focus.heli_sorties_before}</span></span>
              <b style={{ font: '700 2rem var(--cond)' }}>→</b>
              <span className="holder drone" style={{ borderRadius: 6, padding: '.6rem' }}><Drone /><span>{a.focus.heli_sorties_after}</span></span>
            </div>
            <div>
              <h2 style={{ margin: '0 0 .2rem', font: '700 1.6rem/1.15 var(--cond)' }}>
                {best.saved_inr > 0
                  ? `${a.n} drone${a.n === 1 ? '' : 's'} at ${best.base_name}: ${a.focus.post ? `${shortName(a.focus.post)} needs ${a.focus.heli_sorties_after} helicopter sorties instead of ${a.focus.heli_sorties_before}, ` : ''}saving ${lakh(best.saved_inr)} this week`
                  : `${a.n} drone${a.n === 1 ? '' : 's'} of this band save nothing this week`}
              </h2>
              <p style={{ margin: 0 }}>{rupee(a.headline.split(' Cost inputs')[0])}</p>
              <p className="muted" style={{ margin: '.2rem 0 0', fontSize: '.92rem' }}>{a.assumption}{a.solver_limited ? ' Some plans are the best found within the solver time limit.' : ''}</p>
            </div>
          </section>
          <table className="t" aria-label="Candidate bases">
            <thead><tr><th>Base</th><th>Saved this week</th><th className="n">Helicopter sorties saved</th><th className="n">Helicopter hours saved</th><th className="n">Mule/porter trips saved</th><th>Posts the drones serve</th></tr></thead>
            <tbody>
              {a.ranking.map((r: Row, k: number) => (
                <tr key={r.base}>
                  <td><b>{k === 0 && r.saved_inr > 0 ? 'Best: ' : ''}{r.base_name}</b></td>
                  <td style={{ minWidth: '14rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
                      <span style={{ height: 12, width: `${(Math.max(0, r.saved_inr) / maxSaved) * 9}rem`, background: 'var(--drone)', borderRadius: '0 4px 4px 0' }} />
                      <b>{r.saved_inr > 0 ? lakh(r.saved_inr) : 'nothing'}</b>
                    </div>
                  </td>
                  <td className="n">{fmt(r.heli_sorties_saved)}</td>
                  <td className="n">{fmt(r.heli_hours_saved, 1)} h</td>
                  <td className="n">{r.foot_trips_saved < 0 ? `${fmt(-r.foot_trips_saved)} more` : fmt(r.foot_trips_saved)}</td>
                  <td>{r.posts_served.length ? r.posts_served.join(', ') : <span className="muted">none in range</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
