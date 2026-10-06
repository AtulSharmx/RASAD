import { useCallback, useMemo } from 'react'
import { atRisk, day, fmt, postSummaries, RANK, shortName, useApi, type Row } from '../api'
import { useApp } from '../App'
import SectorMap from '../SectorMap'
import { Chip, costChip, ErrorNote, Holder, Skeleton } from '../ui'

export function whyLine(s: Row) {
  const i = s.item
  const drone = s.lines?.find((l: Row) => l.mode === 'drone')
  if (i.status === 'passed') {
    const why = i.route_closed ? `Ground route closed${i.route_note ? `: ${i.route_note.replace(/\.?$/, '.')}` : '.'}` : 'A convoy can no longer arrive before the route closes.'
    const pay = drone?.assumptions?.find((a: Row) => a.name === 'drone payload')?.value
    return `${why} ${drone ? `Drone from ${drone.from}: ${drone.trips} sorties on ${drone.when}${pay ? `, ${pay} each` : ''}.` : 'Air only.'} Helicopter would cost ~${i.cost_multiple}× the road.`
  }
  const modes = [...new Set((s.lines ?? []).map((l: Row) => l.mode))].join(' + ')
  return `Road open until ${day(i.closure_p20)} (80% confidence).${modes ? ` Plan: ${modes}.` : ''} Road ₹${fmt(i.road_inr_per_kg, 1)}/kg vs helicopter ₹${fmt(i.air_inr_per_kg)}/kg.`
}

export function RiskStrip({ s, n }: { s: Row; n?: number }) {
  const i = s.item
  const main = [...(s.lines ?? [])].sort((a, b) => b.kg - a.kg)[0]
  const passed = i.status === 'passed'
  const due = passed ? 'Air only' : i.days_left === 0 ? 'Today' : day(i.last_safe_dispatch)
  return (
    <a className="strip-link" href={`#/post/${i.post}`} data-demo={`strip-${i.post}`}>
      <article className={`strip ${i.status}`} aria-label={`${i.post_name}, ${i.label}: ${passed ? 'air only' : 'last road day ' + due}`}>
        <Holder mode={main?.mode} />
        <div className="cells">
          <div className="cell who">
            <span className="v">{n !== undefined && <span className="num">{n}</span>}{shortName(i.post_name)}</span>
            <span className="k">{i.label}</span>
          </div>
          <div className="cell">
            <span className="k">Lasts (80%)</span>
            <span className="v">{s.cover ? `${s.cover.days} d` : '–'} {s.cover && <small>{s.cover.days_low}–{s.cover.days_high} d</small>}</span>
          </div>
          <div className="cell due">
            <span className="k">{passed ? 'Ground route' : 'Last road day (80%)'}</span>
            <span className="v">{due}</span>
          </div>
          <div className="why"><p>{whyLine(s)}</p><span className="chips"><Chip kind="sim" label="Sim" />{costChip(i)}</span></div>
        </div>
      </article>
    </a>
  )
}

export default function Dashboard() {
  const { mode, go } = useApp()
  const sector = useApi('sector', true)
  const terrain = useApi('terrain', true)
  const pnr = useApi(`pnr?mode=${mode}`, true)
  const fc = useApi(`forecast?mode=${mode}`, true)
  const plan = useApi(`plan?mode=${mode}`)
  const alerts = useApi<Row[]>(`alerts?mode=${mode}`, true)
  const onPost = useCallback((id: string) => go(`post/${id}`), [go])

  const S = useMemo(() => (pnr.data ? postSummaries(pnr.data, plan.data, fc.data?.cover ?? null) : null), [pnr.data, plan.data, fc.data])
  const risk = useMemo(() => (S ? Object.values(S).filter(atRisk).sort((a, b) => RANK[a.item.status] - RANK[b.item.status] || a.item.days_left - b.item.days_left) : []), [S])
  const rest = useMemo(() => (S ? Object.values(S).filter((s) => !atRisk(s)) : []), [S])
  const status = useMemo(() => (S ? Object.fromEntries(Object.entries(S).map(([k, s]) => [k, s.item.status])) : {}), [S])
  const riskIds = useMemo(() => risk.map((s) => s.item.post), [risk])
  const legs = useMemo(() => (plan.data?.lines ?? []).filter((l: Row) => l.mode === 'drone').map((l: Row) => ({ from: l.from, to: l.post })), [plan.data])

  const err = sector.error || terrain.error || pnr.error
  if (err) return <div className="page"><ErrorNote error={err} retry={() => { sector.reload(); terrain.reload(); pnr.reload() }} /></div>
  return (
    <div className="dash">
      {sector.data && terrain.data && S
        ? <SectorMap sector={sector.data} terrain={terrain.data} status={status} risk={riskIds} droneLegs={legs} onPost={onPost} />
        : <Skeleton h={600} label="Loading the map" />}
      <section className="bay" aria-label="Action strips">
        <div className="bay-head" data-demo="risk">
          <h1>{S ? `${risk.length} posts at risk` : 'Checking posts'}</h1>
          <span>Act before the road shuts</span>
          <small>{rest.length} stocked</small>
        </div>
        <div className="bay-list">
          {!S && <><Skeleton h={130} /><Skeleton h={130} /><Skeleton h={130} /></>}
          {risk.map((s, k) => <RiskStrip key={s.item.post} s={s} n={k + 1} />)}
          {S && (
            <div className="stocked">
              {alerts.data && alerts.data.length > 0 && (
                <p style={{ margin: '0 0 .5rem' }}><a href="#/alerts"><b>{alerts.data.length} data alerts to verify on ground</b></a>: {[...new Set(alerts.data.map((a) => a.post_name.replace('Post ', '')))].join(', ')}</p>
              )}
              <h2>Stocked until the routes reopen</h2>
              <ul>
                {rest.map((s) => (
                  <li key={s.item.post}><a href={`#/post/${s.item.post}`}>{shortName(s.item.post_name)}
                    <span className={s.item.status === 'stocked' ? 'ok-text' : 'watch-text'}>
                      {s.item.status === 'stocked' ? `to ${day(s.item.reopen_p80)}` : s.item.status === 'watch' ? `watch ${s.item.label.toLowerCase()}` : 'review at next update'}
                    </span></a></li>
                ))}
              </ul>
            </div>
          )}
          {S && !plan.data && !plan.error && <p className="muted">Working out the plan…</p>}
        </div>
      </section>
    </div>
  )
}
