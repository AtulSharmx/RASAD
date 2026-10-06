import { useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { api, clearCache, fmt, useApi, type Row } from '../api'
import { useApp } from '../App'
import { Badge, Chip, ErrorNote, Skeleton } from '../ui'

const when = (iso?: string) => (iso ? new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '–')

export default function Sources() {
  const { mode } = useApp()
  const src = useApi<Row[]>('sources')
  const [sel, setSel] = useState('iot_fuel')
  const [busy, setBusy] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const run = async (what: 'sync' | 'live') => {
    setBusy(what); setMsg(null)
    try {
      await api(what === 'sync' ? 'sources/sync' : 'live/refresh', { method: 'POST' })
      clearCache(); src.reload()
      setMsg(what === 'sync' ? 'All sources re-read from their files.' : 'Real 16-day forecast downloaded and loaded.')
    } catch (e) { setMsg(String((e as Error).message)) } finally { setBusy(null) }
  }
  if (src.error) return <div className="page"><ErrorNote error={src.error} retry={src.reload} /></div>
  if (!src.data) return <div className="page"><Skeleton h={420} /></div>
  const cur = src.data.find((s) => s.id === sel) ?? src.data[0]
  const real = src.data.filter((s) => !s.simulated).length
  return (
    <div className="page">
      <div className="page-head">
        <h1>Data sources</h1>
        <p>{src.data.length} streams feed one picture: {real} real, {src.data.length - real} simulated. Each one is a single config file; existing Army systems stay untouched.</p>
        <span className="tools">
          {mode === 'live' && <button className="btn btn-line" disabled={!!busy} onClick={() => run('live')}><RefreshCw />Refresh real forecast</button>}
          <button className="btn btn-ink" disabled={!!busy} onClick={() => run('sync')}><RefreshCw />{busy === 'sync' ? 'Syncing…' : 'Sync all now'}</button>
        </span>
      </div>
      {msg && <div className="notice" role="status" style={{ marginBottom: '.6rem' }}>{msg}</div>}
      <div className="grid2" style={{ gridTemplateColumns: '1.45fr 1fr', alignItems: 'start' }}>
        <table className="t" data-demo="sources" aria-label="Sources">
          <thead><tr><th>Stream</th><th>Data</th><th>Health</th><th className="n">Records</th><th>Newest record</th></tr></thead>
          <tbody>
            {src.data.map((s) => (
              <tr key={s.id} onClick={() => setSel(s.id)} style={{ cursor: 'pointer', background: s.id === cur.id ? '#eef2f7' : undefined }} aria-selected={s.id === cur.id}>
                <td><button className="linkbtn" aria-pressed={s.id === cur.id} onClick={() => setSel(s.id)}>{s.name}</button></td>
                <td>{s.simulated ? <Chip kind="sim">{s.label}</Chip> : <Chip kind="real">{s.owner}</Chip>}</td>
                <td><Badge status={s.health} />{s.notes.map((n: string) => <div key={n} className="watch-text" style={{ fontSize: '.85rem', marginTop: '.2rem' }}>{n}</div>)}</td>
                <td className="n">{fmt(s.records ?? 0)}</td>
                <td>{s.last_record && /^\d{4}-/.test(s.last_record) ? when(s.last_record) : <span className="muted">file {when(s.file_time)}</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <section className="panel" aria-label="Config file">
          <h2>{cur.name}</h2>
          <p className="muted" style={{ margin: '0 0 .4rem' }}>{cur.owner}</p>
          <p style={{ margin: '0 0 .5rem' }}>This is the whole adapter for this stream, <code>{cur.file}</code>. It says where the export is, what each column means and how codes translate. The app reads it on every sync.</p>
          <pre className="cfg">{cur.config}</pre>
          <h2 style={{ marginTop: '.9rem' }}>Add a new stream in three steps</h2>
          <ol style={{ margin: 0, paddingLeft: '1.2rem' }}>
            <li>Put the system's export (CSV or JSON) in <code>data/feeds/</code>, or point to it.</li>
            <li>Copy a config like the one above into <code>sources/</code> and map its columns.</li>
            <li>Press <b>Sync all now</b>. The stream appears here with its health; no code changes.</li>
          </ol>
        </section>
      </div>
    </div>
  )
}
