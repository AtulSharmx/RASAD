import { useMemo, useState } from 'react'
import { day, fmt, plural, RANK, shortName, useApi, type Row } from '../api'
import { useApp } from '../App'
import { BandChart } from '../charts'
import { Badge, Chip, ErrorNote, Holder, Skeleton } from '../ui'

export default function PostDetail() {
  const { mode, route } = useApp()
  const pnr = useApi(`pnr?mode=${mode}`, true)
  const fc = useApi(`forecast?mode=${mode}`, true)
  const sector = useApi('sector', true)
  const plan = useApi(`plan?mode=${mode}`)
  const worst = useMemo(() => {
    const w: Record<string, Row> = {}
    for (const i of pnr.data?.items ?? []) if (!w[i.post] || RANK[i.status] < RANK[w[i.post].status]) w[i.post] = i
    return w
  }, [pnr.data])
  const posts = useMemo(() => (sector.data?.nodes ?? []).filter((n: Row) => n.kind === 'post'), [sector.data])
  const post = route[1] ?? 'PA'
  const series = useApi(`forecast/${post}?mode=${mode}&days=60`)
  const [cls, setCls] = useState<string | null>(null)

  const err = pnr.error || fc.error || sector.error
  if (err) return <div className="page"><ErrorNote error={err} /></div>
  if (!pnr.data || !fc.data || !sector.data) return <div className="page"><Skeleton h={500} /></div>

  const node = posts.find((n: Row) => n.id === post)
  const items = pnr.data.items.filter((i: Row) => i.post === post).sort((a: Row, b: Row) => RANK[a.status] - RANK[b.status])
  const sel = cls ?? items[0]?.class
  const selItem = items.find((i: Row) => i.class === sel)
  const acc = fc.data.accuracy.find((a: Row) => a.class === sel)
  const cover = (c: string) => fc.data!.cover.find((x: Row) => x.post === post && x.class === c)
  const lines = (plan.data?.lines ?? []).filter((l: Row) => l.post === post)

  return (
    <div className="page">
      <div className="tabs" role="navigation" aria-label="Posts" style={{ marginBottom: '.7rem' }}>
        {posts.map((p: Row) => (
          <a key={p.id} href={`#/post/${p.id}`} aria-current={p.id === post ? 'page' : undefined}>
            {['passed', 'urgent'].includes(worst[p.id]?.status) && <span className="dot" aria-label="at risk" />}{shortName(p.name)}
          </a>
        ))}
      </div>
      <div className="page-head">
        <h1>{node?.name} <span className="muted" style={{ fontSize: '1.1rem' }}>{fmt(node?.alt_m)} m, {node?.troops} troops</span></h1>
        <Badge status={worst[post]?.status ?? 'stocked'} />
        <span className="tools"><Chip kind="sim" /><Chip kind="real" label="Real: height, weather">Height from Copernicus DEM; weather from Open-Meteo, adjusted for this post's height.</Chip></span>
      </div>

      <table className="t" aria-label="Supply classes">
        <thead><tr><th>Supply</th><th className="n">Stock</th><th className="n">Use today</th><th className="n">Lasts (80% band)</th><th>Last road day (80%)</th><th>Status</th><th>Forecast method</th></tr></thead>
        <tbody>
          {items.map((i: Row) => {
            const c = cover(i.class), a = fc.data!.accuracy.find((x: Row) => x.class === i.class)
            return (
              <tr key={i.class} onClick={() => setCls(i.class)} style={{ cursor: 'pointer', background: i.class === sel ? '#eef2f7' : undefined }}
                aria-selected={i.class === sel}>
                <td><button className="btn btn-sm btn-line" aria-pressed={i.class === sel} onClick={() => setCls(i.class)}>{i.label}</button></td>
                <td className="n">{fmt(i.stock)} {i.unit}</td>
                <td className="n">{c ? fmt(c.use_today_p50, 1) : '–'} {i.unit}</td>
                <td className="n"><b>{c ? (c.days >= c.horizon_days ? `${c.days}+ d` : `${c.days} d`) : '–'}</b> {c && <span className="muted">{c.days_low}–{c.days_high}</span>}</td>
                <td>{i.status === 'passed' ? <span className="urgent-text"><b>Air only</b></span> : i.status === 'stocked' ? <span className="muted">not needed</span> : <b>{day(i.last_safe_dispatch)}</b>}</td>
                <td><Badge status={i.status} /></td>
                <td>{a?.method}</td>
              </tr>
            )
          })}
        </tbody>
      </table>

      <div className="grid2" style={{ marginTop: '.8rem', gridTemplateColumns: '1.5fr 1fr' }}>
        <section className="panel" aria-label="Forecast chart">
          <h2>{selItem?.label}: daily use and forecast</h2>
          {series.data ? (
            <BandChart unit={selItem?.unit ?? ''}
              actual={series.data.actual.filter((r: Row) => r.class === sel)}
              forecast={series.data.forecast.filter((r: Row) => r.class === sel)} />
          ) : series.error ? <ErrorNote error={series.error} /> : <Skeleton h={230} />}
          {acc && <p style={{ margin: '.5rem 0 0' }}>{acc.plain} <b>Measured on simulated data — real accuracy unknown until real CICG data is connected.</b> <Chip kind="sim" label="Why">The simulated use was generated from the same temperature and height inputs the model sees, so these scores are optimistic. The method and band were chosen on {day(acc.select_from)} to {day(acc.select_to)}; the score is from {day(acc.test_from)} to {day(acc.test_to)} only.</Chip></p>}
        </section>
        <section className="panel" aria-label="Planned movements">
          <h2>Planned this week</h2>
          {!plan.data && !plan.error && <Skeleton h={120} />}
          {plan.data && !lines.length && <p className="muted">Nothing to send this week: {selItem?.status === 'stocked' ? 'stocked until the route reopens.' : 'see the Point of no return for the deadline.'}</p>}
          {lines.map((l: Row) => (
            <div key={l.key} className="strip" style={{ marginBottom: '.5rem' }}>
              <Holder mode={l.mode} />
              <div style={{ padding: '.45rem .6rem' }}>
                <b style={{ font: '700 1.15rem var(--cond)' }}>{l.qty_text}</b> <span className="muted">{l.label}, {l.when}</span>
                <p style={{ margin: '.2rem 0 0', fontSize: '.92rem' }}>₹{fmt(l.cost_inr)} for {plural(l.trips, l.mode === 'helicopter' || l.mode === 'drone' ? 'sortie' : 'trip')}. <a href="#/plan">Open in plan</a></p>
              </div>
            </div>
          ))}
        </section>
      </div>
    </div>
  )
}
