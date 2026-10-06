import { RefreshCw } from 'lucide-react'
import { fmt, useApi, type Row } from '../api'
import { Badge, Chip, ErrorNote, Skeleton } from '../ui'

const STATE: Record<string, string> = { approve: 'approved', modify: 'modified', reject: 'rejected' }
const parse = (s: string) => { try { return JSON.parse(s) } catch { return {} } }

export default function Audit() {
  const log = useApi<Row[]>('audit')
  if (log.error) return <div className="page"><ErrorNote error={log.error} retry={log.reload} /></div>
  return (
    <div className="page">
      <div className="page-head">
        <h1>Audit log</h1>
        <p>Every approval, change and rejection, with who, when and what changed. Newest first.</p>
        <span className="tools">
          <Chip kind="sim" label="Demo roles">Roles come from the role picker (demo only, no real login). In deployment the identity comes from Army SSO/PKI.</Chip>
          <button className="btn btn-line" onClick={log.reload}><RefreshCw />Refresh</button>
        </span>
      </div>
      {!log.data ? <Skeleton h={300} /> : log.data.length === 0 ? (
        <div className="notice">No decisions yet. Open the <a href="#/plan">plan</a> and approve, modify or reject a line; it will appear here with the role, the time and what changed.</div>
      ) : (
        <table className="t" data-demo="audit" aria-label="Audit log">
          <thead><tr><th>When</th><th>Who</th><th>Action</th><th>Line</th><th>Before</th><th>After</th></tr></thead>
          <tbody>
            {log.data.map((r) => {
              const b = parse(r.before), a = parse(r.after)
              return (
                <tr key={r.id}>
                  <td style={{ whiteSpace: 'nowrap' }}>{new Date(r.ts).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' })}</td>
                  <td><b>{r.role}</b><div className="muted" style={{ fontSize: '.85rem' }}>{r.user}</div></td>
                  <td><Badge status={STATE[r.action] ?? r.action} /></td>
                  <td>{r.item.replace(/ \[.*\]$/, '')}{r.note && <div className="muted">Note: {r.note}</div>}</td>
                  <td>{b.status} {b.kg !== undefined && <span className="muted">{fmt(b.kg)} kg</span>}</td>
                  <td><b>{a.status}</b> {a.kg !== undefined && <span>{fmt(a.kg)} kg</span>}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
